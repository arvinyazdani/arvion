from django.core.management.base import BaseCommand, CommandError

from blog.english_editions import publish_english_editions


class Command(BaseCommand):
    help = "Attach approved English editions to eight already published Persian posts. Dry-run by default."

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--apply", action="store_true")
        group.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        try:
            result = publish_english_editions(apply=options["apply"])
        except (ValueError, OSError) as exc:
            raise CommandError(str(exc)) from exc
        prefix = "DRY RUN, no writes" if result["dry_run"] else "English editions attached"
        self.stdout.write(f"{prefix}: {result['updated']} updated; {result['unchanged']} unchanged. Persian content, covers and publication dates preserved.")
