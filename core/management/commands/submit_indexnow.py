from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from urllib.parse import urlsplit

from core.indexnow import submit_urls


class Command(BaseCommand):
    help = "Submit public same-site URLs to IndexNow. URLs are never crawled or modified by this command."

    def add_arguments(self, parser):
        parser.add_argument("--url", action="append", default=[], help="Absolute public URL; repeat for multiple URLs.")

    def handle(self, *args, **options):
        urls = options["url"]
        if not urls:
            raise CommandError("Supply at least one --url.")
        host = urlsplit(settings.SITE_URL).netloc
        if any(urlsplit(url).netloc != host or urlsplit(url).scheme != "https" for url in urls):
            raise CommandError("Only HTTPS URLs on this configured site are allowed.")
        result = submit_urls(urls)
        self.stdout.write(f"IndexNow: {result['status']} ({result['count']} URL(s))")
