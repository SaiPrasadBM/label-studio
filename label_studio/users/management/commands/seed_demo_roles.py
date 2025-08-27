from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

from organizations.models import Organization, OrganizationMember
from organizations.roles import get_user_role_for_org, get_fine_grained_role, get_org_role


class Command(BaseCommand):
    help = "Seed a demo organization with users mapped to OWNER/ADMIN/MEMBER and EDITOR/ANNOTATOR/VIEWER roles."

    def add_arguments(self, parser):
        parser.add_argument(
            "--org-title",
            default="Demo Org",
            help="Title for the demo organization.",
        )
        parser.add_argument(
            "--owner-email", default="owner@example.com", help="Owner email"
        )
        parser.add_argument(
            "--owner-password", default="owner123", help="Owner password"
        )
        parser.add_argument(
            "--admin-email", default="admin@example.com", help="Admin email"
        )
        parser.add_argument(
            "--admin-password", default="admin123", help="Admin password"
        )
        parser.add_argument(
            "--supervisor-email", default="supervisor@example.com", help="Supervisor email"
        )
        parser.add_argument(
            "--supervisor-password", default="super123", help="Supervisor password"
        )
        parser.add_argument(
            "--worker-email", default="worker@example.com", help="Worker email"
        )
        parser.add_argument(
            "--worker-password", default="worker123", help="Worker password"
        )
        parser.add_argument(
            "--viewer-email", default="viewer@example.com", help="Viewer email (not added to org)"
        )
        parser.add_argument(
            "--viewer-password", default="viewer123", help="Viewer password"
        )

    def handle(self, *args, **options):
        User = get_user_model()

        def create_user(email, password, first, last, is_staff=False, is_superuser=False):
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": email.split("@")[0],
                    "first_name": first,
                    "last_name": last,
                    "is_staff": is_staff,
                    "is_superuser": is_superuser,
                },
            )
            if created:
                user.set_password(password)
                user.save()
            return user

        # 1) Create users
        owner = create_user(
            options["owner_email"], options["owner_password"], "Olivia", "Owner"
        )
        admin = create_user(
            options["admin_email"], options["admin_password"], "Manny", "Maintainer", is_staff=True
        )
        supervisor = create_user(
            options["supervisor_email"], options["supervisor_password"], "Sally", "Supervisor"
        )
        worker = create_user(
            options["worker_email"], options["worker_password"], "Will", "Worker"
        )
        viewer = create_user(
            options["viewer_email"], options["viewer_password"], "Victor", "Viewer"
        )  # not added to org

        # 2) Create an organization owned by 'owner' (or reuse if exists)
        org = Organization.objects.filter(title=options["org_title"], created_by=owner).first()
        if not org:
            org = Organization.create_organization(created_by=owner, title=options["org_title"])

        # Set active org for owner
        owner.active_organization = org
        owner.save(update_fields=["active_organization"])

        # 3) Add members with roles: admin->MAINTAINER, supervisor->SUPERVISOR, worker->WORKER
        org.add_user(admin, role=OrganizationMember.ROLE_MAINTAINER)
        org.add_user(supervisor, role=OrganizationMember.ROLE_SUPERVISOR)
        org.add_user(worker, role=OrganizationMember.ROLE_WORKER)

        # Set their active orgs
        admin.active_organization = org
        supervisor.active_organization = org
        worker.active_organization = org
        admin.save(update_fields=["active_organization"])
        supervisor.save(update_fields=["active_organization"])
        worker.save(update_fields=["active_organization"])

        # 4) Tokens for API usage
        def token(user):
            return Token.objects.get_or_create(user=user)[0].key

        tokens = {
            "owner": token(owner),
            "maintainer": token(admin),
            "supervisor": token(supervisor),
            "worker": token(worker),
            "viewer": token(viewer),
        }

        # 5) Show coarse and fine-grained roles
        def describe(u):
            coarse = get_user_role_for_org(u, org)
            fine = get_fine_grained_role(u, org)
            orgr = get_org_role(u, org)
            self.stdout.write(
                f"{u.email:24} -> org_role: {str(orgr):11} | coarse: {coarse:6} | fine: {fine} | token: {Token.objects.get(user=u).key}"
            )

        self.stdout.write(self.style.SUCCESS("Seed complete. Users and roles:"))
        for u in [owner, admin, supervisor, worker, viewer]:
            describe(u)

        self.stdout.write(self.style.NOTICE(f"Organization: {org.title} (id={org.id})"))
        self.stdout.write(self.style.SUCCESS("Tokens:"))
        for k, v in tokens.items():
            self.stdout.write(f"  {k}: {v}")
