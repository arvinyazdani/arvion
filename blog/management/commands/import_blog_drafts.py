from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from blog.drafts import load_drafts
from blog.models import Post


class Command(BaseCommand):
    help = "Import unreviewed Persian article drafts without publishing anything."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report only; no database writes.")
        parser.add_argument("--update", action="store_true", help="Update existing UNPUBLISHED drafts only.")

    def handle(self, *args, **options):
        try:
            drafts = load_drafts()  # Validate every file before any write.
        except (ValueError, OSError) as exc:
            raise CommandError(str(exc)) from exc
        counts = {"created": 0, "updated": 0, "skipped": 0}
        lines = []
        # One import transaction: a failure cannot leave half of the bundle.
        # Dry-run uses the same decisions but performs no INSERT/UPDATE/DELETE.
        with transaction.atomic():
            for draft in drafts:
                queryset = Post.objects.all()
                if not options["dry_run"]:
                    queryset = queryset.select_for_update()
                post = queryset.filter(slug_fa=draft.slug_fa).first()
                values = {key: getattr(draft, key) for key in ("title_fa", "summary_fa", "body_fa")}
                if post is None:
                    action = "created"
                    if not options["dry_run"]:
                        post = Post.objects.create(slug_fa=draft.slug_fa, **values,
                                                   is_published=False, published_at=None)
                        post.tags.set(draft.tags)
                elif post.is_published or not options["update"]:
                    action = "skipped"
                else:
                    action = "updated"
                    if not options["dry_run"]:
                        for key, value in values.items():
                            setattr(post, key, value)
                        # Publication dates and English/editorial fields are not ours to overwrite.
                        post.save(update_fields=list(values))
                        post.tags.set(draft.tags)
                counts[action] += 1
                display_action = {"created": "create", "updated": "update", "skipped": "skip"}[action]
                lines.append(f"{'Would ' + display_action if options['dry_run'] else action}: {draft.slug_fa}")
        for line in lines:
            self.stdout.write(line)
        self.stdout.write(
            f"{'DRY RUN — no database writes. ' if options['dry_run'] else ''}"
            f"Created: {counts['created']}; updated: {counts['updated']}; skipped: {counts['skipped']}. "
            "Unreviewed drafts only; no article was published."
        )
