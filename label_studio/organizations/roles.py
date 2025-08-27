"""Organization role helpers based on persisted membership roles.

Defines org roles: OWNER, MAINTAINER, SUPERVISOR, WORKER.
Also provides backward-compatible coarse/fine roles for existing frontend usage.
"""
from __future__ import annotations
from typing import Literal, Dict, Set

from organizations.models import OrganizationMember

# New org roles
OrgRole = Literal["OWNER", "MAINTAINER", "SUPERVISOR", "WORKER"]

# Back-compat types
CoarseRole = Literal["OWNER", "ADMIN", "MEMBER"]
FineRole = Literal["EDITOR", "ANNOTATOR", "VIEWER"]


def get_org_role(user, organization) -> OrgRole | None:
    if not user or not getattr(user, "is_authenticated", False) or not organization:
        return None
    try:
        om = OrganizationMember.find_by_user(user, organization.pk)
        # Owner override if created_by
        if organization.created_by_id == user.id:
            return OrganizationMember.ROLE_OWNER
        return om.role
    except Exception:
        # Not a member
        if organization and organization.created_by_id == user.id:
            return OrganizationMember.ROLE_OWNER
        return None


def is_org_owner(user, organization) -> bool:
    return bool(organization and user and organization.created_by_id == user.id)


def is_org_maintainer(user, organization) -> bool:
    role = get_org_role(user, organization)
    return role in {OrganizationMember.ROLE_OWNER, OrganizationMember.ROLE_MAINTAINER}


def is_org_supervisor(user, organization) -> bool:
    role = get_org_role(user, organization)
    return role in {
        OrganizationMember.ROLE_OWNER,
        OrganizationMember.ROLE_MAINTAINER,
        OrganizationMember.ROLE_SUPERVISOR,
    }


def is_org_worker(user, organization) -> bool:
    role = get_org_role(user, organization)
    return role in {
        OrganizationMember.ROLE_OWNER,
        OrganizationMember.ROLE_MAINTAINER,
        OrganizationMember.ROLE_SUPERVISOR,
        OrganizationMember.ROLE_WORKER,
    }


# Backward-compatible helpers
def get_user_role_for_org(user, organization) -> CoarseRole:
    if is_org_owner(user, organization):
        return "OWNER"
    role = get_org_role(user, organization)
    if role in {OrganizationMember.ROLE_MAINTAINER}:
        return "ADMIN"
    if role in {
        OrganizationMember.ROLE_SUPERVISOR,
        OrganizationMember.ROLE_WORKER,
    }:
        return "MEMBER"
    return "MEMBER"


def is_org_admin(user, organization) -> bool:
    # Admin-like: OWNER or MAINTAINER
    return is_org_maintainer(user, organization)


def get_fine_grained_role(user, organization) -> FineRole:
    if not user or not getattr(user, "is_authenticated", False):
        return "VIEWER"
    if is_org_maintainer(user, organization):
        return "EDITOR"
    if is_org_worker(user, organization):
        # SUPERVISOR/WORKER -> ANNOTATOR by current UI mapping
        return "ANNOTATOR"
    return "VIEWER"


# Capability map tuned to new semantics via coarse mapping
# Note: Owner implicitly has all Maintainer capabilities
ROLE_CAPABILITIES: Dict[FineRole, Set[str]] = {
    "EDITOR": {
        # Maintainer-equivalent
        "view_project",
        "view_all_tasks",
        "annotate",
        "export",
        "manage_project_settings",
        "manage_tasks",
        "manage_jobs",
        "manage_webhooks",
        "manage_storages",
        "invite_members",
        "modify_member_roles",
        "create_projects",
        "assign_jobs_tasks_projects",
    },
    "ANNOTATOR": {
        # Worker/Supervisor mapped as annotators in fine-grained role
        "view_project",
        "annotate",
        "export",
    },
    "VIEWER": {
        "view_project",
    },
}


def has_capability(user, organization, capability: str) -> bool:
    # Owners get all maintainer capabilities
    if is_org_owner(user, organization):
        return True
    role = get_fine_grained_role(user, organization)
    return capability in ROLE_CAPABILITIES.get(role, set())


def can_view_project(user, organization) -> bool:
    return has_capability(user, organization, "view_project")


def can_manage_project_settings(user, organization) -> bool:
    return has_capability(user, organization, "manage_project_settings")


def can_manage_tasks(user, organization) -> bool:
    return has_capability(user, organization, "manage_tasks")


def can_manage_jobs(user, organization) -> bool:
    return has_capability(user, organization, "manage_jobs")


def can_manage_webhooks(user, organization) -> bool:
    return has_capability(user, organization, "manage_webhooks")


def can_manage_storages(user, organization) -> bool:
    return has_capability(user, organization, "manage_storages")


def can_manage_members(user, organization) -> bool:
    # Back-compat: manage_members now split into inviting and modifying roles
    return can_invite_members(user, organization) and can_modify_member_roles(user, organization)


def can_invite_members(user, organization) -> bool:
    # Maintainer and Owner
    return has_capability(user, organization, "invite_members")


def can_modify_member_roles(user, organization) -> bool:
    # Maintainer and Owner
    return has_capability(user, organization, "modify_member_roles")


# Back-compat wrapper used by projects.permissions
def can_import_data(user, organization) -> bool:
    # Restrict imports to maintainer (admin-like) and owner
    return is_org_maintainer(user, organization)


# New helpers per requested semantics
def can_view_all_tasks(user, organization) -> bool:
    return has_capability(user, organization, "view_all_tasks")


def can_create_projects(user, organization) -> bool:
    return has_capability(user, organization, "create_projects")


def can_assign_jobs_tasks_projects(user, organization) -> bool:
    # Supervisors can assign, maintainers/owners too; workers typically cannot
    if is_org_owner(user, organization) or is_org_maintainer(user, organization):
        return True
    # Supervisors: mapped as ANNOTATOR fine role, so explicitly allow
    role = get_org_role(user, organization)
    return role == OrganizationMember.ROLE_SUPERVISOR
