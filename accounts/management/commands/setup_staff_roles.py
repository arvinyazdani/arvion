from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandError

from accounts.staff_roles import STAFF_ROLES, group_name


class Command(BaseCommand):
    help = "Create least-privilege Rvion staff groups and optionally assign a user."

    def add_arguments(self, parser):
        parser.add_argument("--email", help="Existing user email to assign")
        parser.add_argument("--role", choices=tuple(STAFF_ROLES), help="Role assigned with --email")

    def handle(self, *args, **options):
        for role, config in STAFF_ROLES.items():
            group, _ = Group.objects.get_or_create(name=group_name(role))
            permissions = []
            for model_key, actions in config["permissions"].items():
                app_label, model = model_key.split(".")
                for action in actions:
                    try:
                        permission = Permission.objects.get(
                            content_type__app_label=app_label,
                            content_type__model=model,
                            codename=f"{action}_{model}",
                        )
                    except Permission.DoesNotExist as exc:
                        raise CommandError(f"Missing permission: {app_label}.{action}_{model}") from exc
                    permissions.append(permission)
            group.permissions.set(permissions)
            self.stdout.write(f"{group.name}: {len(permissions)} permissions")

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
