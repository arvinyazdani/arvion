"""Owner-approved English editions of existing published posts; no FA writes."""
import json
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.validators import validate_slug
from django.db import transaction
from django.utils import timezone

from blog.models import Post


ENGLISH_DIRECTORY = Path(__file__).parent / "english_content"
ENGLISH_FIELDS = ("slug_en", "title_en", "summary_en", "body_en")


def load_english_editions(directory=ENGLISH_DIRECTORY):
    editions = []
    seen = {key: set() for key in ("slug_fa", "slug_en", "title_en", "summary_en")}
    for path in sorted(Path(directory).glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n") or "\n---\n" not in text[4:]:
            raise ValueError(f"{path.name}: invalid front matter")
        header, body = text[4:].split("\n---\n", 1)
        item = {}
        for line in header.splitlines():
            key, separator, value = line.partition(":")
            if not separator or key in item:
                raise ValueError(f"{path.name}: invalid metadata")
            item[key] = json.loads(value)
        if item.keys() != seen.keys():
            raise ValueError(f"{path.name}: unexpected metadata fields")
        for key, values in seen.items():
            value = item[key]
            if not isinstance(value, str) or not value.strip() or value in values:
                raise ValueError(f"{path.name}: empty or duplicate {key}")
            values.add(value)
        try:
            validate_slug(item["slug_en"])
        except ValidationError as exc:
            raise ValueError(f"{path.name}: invalid English slug") from exc
        if len(item["slug_en"]) > 170 or len(item["title_en"] + " | Rvion") > 60:
            raise ValueError(f"{path.name}: oversized slug or SEO title")
        if not 90 <= len(item["summary_en"]) <= 155:
            raise ValueError(f"{path.name}: summary must be 90–155 characters")
        if len(body.split()) < 500 or any("\u0600" <= char <= "\u06ff" for char in body):
            raise ValueError(f"{path.name}: incomplete or non-English body")
        item["body_en"] = body
        editions.append(item)
    if len(editions) != 8:
        raise ValueError("Expected exactly the eight approved English editions")
    return editions


def publish_english_editions(*, apply=False, directory=ENGLISH_DIRECTORY):
    """Validate the complete set before writing; preserve all other Post fields.

    An existing, currently published FA post is required. There is no create,
    publication-date change, deletion, tag change or unpublished-post promotion.
    The row's existing publication state exposes the newly complete translation.
    """
    editions = load_english_editions(directory)
    result = {"updated": 0, "unchanged": 0, "dry_run": not apply}
    with transaction.atomic():
        queryset = Post.objects.all()
        if apply:
            queryset = queryset.select_for_update()
        posts = {post.slug_fa: post for post in queryset.filter(
            slug_fa__in=[item["slug_fa"] for item in editions]
        ).order_by("pk")}
        now = timezone.now()
        for item in editions:
            post = posts.get(item["slug_fa"])
            if post is None or not post.is_published or not post.published_at or post.published_at > now:
                raise ValueError(f"Published source missing: {item['slug_fa']}")
            if post.slug_en and post.slug_en != item["slug_en"]:
                raise ValueError(f"Existing English URL differs: {item['slug_fa']}")
            if Post.objects.filter(slug_en=item["slug_en"]).exclude(pk=post.pk).exists():
                raise ValueError(f"English URL already belongs to another post: {item['slug_en']}")
        for item in editions:
            post = posts[item["slug_fa"]]
            if all(getattr(post, key) == item[key] for key in ENGLISH_FIELDS):
                result["unchanged"] += 1
                continue
            result["updated"] += 1
            if apply:
                for key in ENGLISH_FIELDS:
                    setattr(post, key, item[key])
                post.save(update_fields=ENGLISH_FIELDS)
    return result
