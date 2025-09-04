"""
Management command to clear OPA cache for users
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.opa_integration import opa_client

User = get_user_model()


class Command(BaseCommand):
    help = 'Clear OPA cache for users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Email of specific user to clear cache for',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Clear cache for all users',
        )

    def handle(self, *args, **options):
        if options['user']:
            # Clear cache for specific user
            opa_client.clear_user_cache(options['user'])
            self.stdout.write(
                self.style.SUCCESS(f'Successfully cleared OPA cache for user: {options["user"]}')
            )
        elif options['all']:
            # Clear cache for all users
            users = User.objects.filter(email__isnull=False).values_list('email', flat=True)
            for email in users:
                opa_client.clear_user_cache(email)
            self.stdout.write(
                self.style.SUCCESS(f'Successfully cleared OPA cache for {len(users)} users')
            )
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --user <email> or --all')
            )
