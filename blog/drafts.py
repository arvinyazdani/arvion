"""Load the repository's unreviewed Persian drafts, never publication settings.

Front matter uses JSON values (a small, deterministic YAML subset). No YAML
dependency or executable document format is needed for these four files.
"""
import json
from dataclasses import dataclass
from pathlib import Path

from django.core.validators import validate_unicode_slug
from django.core.exceptions import ValidationError


DRAFT_DIRECTORY = Path(__file__).parent / "content_drafts"
REQUIRED_FIELDS = frozenset({"slug_fa", "title_fa", "summary_fa", "tags"})


@dataclass(frozen=True)
class ArticleDraft:
    filename: str
    slug_fa: str
    title_fa: str
    summary_fa: str
    tags: tuple
    body_fa: str


def load_drafts():
    drafts = []
    slugs = set()
    for path in sorted(DRAFT_DIRECTORY.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n") or "\n---\n" not in text[4:]:
            raise ValueError(f"{path.name}: missing front matter")
        header, body = text[4:].split("\n---\n", 1)
        metadata = {}
        for line in header.splitlines():
            key, separator, value = line.partition(":")
            if not separator or key in metadata:
                raise ValueError(f"{path.name}: invalid or duplicate metadata key")
            metadata[key] = json.loads(value)
        if metadata.keys() != REQUIRED_FIELDS:
            raise ValueError(f"{path.name}: only slug_fa/title_fa/summary_fa/tags are allowed")
        for key in ("slug_fa", "title_fa", "summary_fa"):
            if not isinstance(metadata[key], str) or not metadata[key].strip():
                raise ValueError(f"{path.name}: {key} must be nonempty text")
        slug = metadata["slug_fa"]
        try:
            validate_unicode_slug(slug)
        except ValidationError as exc:
            raise ValueError(f"{path.name}: invalid slug_fa") from exc
        if len(slug) > 170 or slug in slugs:
            raise ValueError(f"{path.name}: oversized or duplicate slug_fa")
        if len(metadata["title_fa"] + " | آرویون") > 60:
            raise ValueError(f"{path.name}: title including brand exceeds 60 characters")
        if not 110 <= len(metadata["summary_fa"]) <= 140:
            raise ValueError(f"{path.name}: description must be 110–140 characters")
        tags = metadata["tags"]
        if not isinstance(tags, list) or not tags or any(
            not isinstance(tag, str) or not tag.strip() or len(tag) > 100 for tag in tags
        ) or len(set(tags)) != len(tags):
            raise ValueError(f"{path.name}: invalid tags")
        if not body.strip():
            raise ValueError(f"{path.name}: missing article body")
        slugs.add(slug)
        drafts.append(ArticleDraft(path.name, slug, metadata["title_fa"],
                                   metadata["summary_fa"], tuple(tags), body))
    if not drafts:
        raise ValueError("No repository article drafts found")
    return drafts
