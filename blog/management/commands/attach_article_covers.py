"""Attach reviewed repository assets without replacing any existing cover."""
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from PIL import Image

from blog.covers import COVER_ALTS, INTERNATIONAL_COVERS, SINGLE_LANGUAGE_COVERS
from blog.models import Post


class Command(BaseCommand):
    help = "Attach the eight reviewed article covers; never overwrite a cover."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report without database/media writes.")
        parser.add_argument("--bundle", choices=("original", "international"), default="original")

    def handle(self, *args, **options):
        directory = Path(settings.BASE_DIR) / "blog/content_drafts/covers"
        assets = {slug: directory / (slug + "-v2.jpg") for slug in COVER_ALTS}
        if options["bundle"] == "international":
            directory = Path(settings.BASE_DIR) / "blog/static/blog/covers"
            assets = {slug: directory / (item[0] + "-fa-v1.jpg")
                      for slug, item in INTERNATIONAL_COVERS.items()}
            assets.update({slug: directory / (item["prefix"] + "-" + item["language"] + "-v1.jpg")
                           for slug, item in SINGLE_LANGUAGE_COVERS.items()})
            for item in INTERNATIONAL_COVERS.values():
                if item[0] != "raya":
                    with Image.open(directory / (item[0] + "-en-v1.jpg")) as image:
                        if image.size != (1200, 630):
                            raise CommandError("Invalid English cover dimensions")
                        image.verify()
        # Validate the complete mapping before the first write.
        for slug, path in assets.items():
            try:
                with Image.open(path) as image:
                    if image.size != (1200, 630) or image.format != "JPEG":
                        raise ValueError("Expected a 1200x630 JPEG")
                    image.verify()
            except (OSError, ValueError) as error:
                raise CommandError("Invalid cover for " + slug + ": " + str(error)) from error
        attached = skipped = 0
        for slug, path in assets.items():
            with transaction.atomic():
                post = Post.objects.select_for_update().filter(Q(slug_fa=slug) | Q(slug_en=slug)).first()
                if post is None or post.hero_image:
                    skipped += 1
                    self.stdout.write("Skipped: " + slug + (" (missing article)" if post is None else " (already has image)"))
                    continue
                if not options["dry_run"]:
                    with path.open("rb") as source:
                        post.hero_image.save(path.name, File(source), save=False)
                    # No publication/content updates, save hooks or importer side effects.
                    Post.objects.filter(pk=post.pk).update(hero_image=post.hero_image.name)
                attached += 1
                self.stdout.write(("Would attach: " if options["dry_run"] else "Attached: ") + slug)
        self.stdout.write("{}: {}; skipped: {}".format("Would attach" if options["dry_run"] else "Attached", attached, skipped))
