from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from accounts.staff_roles import STAFF_ROLES, group_name, sync_staff_role_groups


class Command(BaseCommand):
    help = "Create least-privilege Rvion staff groups and optionally assign a user."

    def add_arguments(self, parser):
        parser.add_argument("--email", help="Existing user email to assign")
        parser.add_argument("--role", choices=tuple(STAFF_ROLES), help="Role assigned with --email")

    def handle(self, *args, **options):
        try:
            groups = sync_staff_role_groups()
        except Exception as exc:
            raise CommandError(str(exc)) from exc
        for group in groups.values():
            self.stdout.write(f"{group.name}: {group.permissions.count()} permissions")

        email, role = options.get("email"), options.get("role")
        if bool(email) != bool(role):
            raise CommandError("--email and --role must be supplied together")
        if email:
            User = get_user_model()
            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist as exc:
                raise CommandError(f"No user found for {email}") from exc
            user.groups.remove(*Group.objects.filter(name__in=[group_name(key) for key in STAFF_ROLES]))
            user.groups.add(Group.objects.get(name=group_name(role)))
            user.is_staff = True
            user.save(update_fields=["is_staff"])
            self.stdout.write(self.style.SUCCESS(f"Assigned {user.email} to {role}"))
        else:
            self.stdout.write(self.style.SUCCESS("Rvion staff roles are ready."))
