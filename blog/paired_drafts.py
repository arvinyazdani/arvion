"""Validated bilingual bundles; pair is an import identity, never publication authority."""
import json
from dataclasses import dataclass
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.validators import validate_slug

DIRECTORY = Path(__file__).parent / "international_drafts"


@dataclass(frozen=True)
class PairedDraft:
    slug_fa: str
    tags: tuple
    values: dict


def load_paired_drafts(directory=None):
    groups = {}
    seen = {"fa": set(), "en": set()}
    for path in sorted(Path(directory or DIRECTORY).glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n") or "\n---\n" not in text[4:]:
            raise ValueError(f"{path.name}: missing front matter")
        header, body = text[4:].split("\n---\n", 1)
        data = {}
        for line in header.splitlines():
            key, sep, raw = line.partition(":")
            if not sep or key in data:
                raise ValueError(f"{path.name}: invalid metadata")
            data[key] = json.loads(raw)
        language = data.get("lang")
        if language not in seen:
            raise ValueError(f"{path.name}: unsupported language")
        fields = {f"{key}_{language}" for key in ("slug", "title", "summary")}
        required = {"lang", "pair", "status", "tags", "target_keywords"} | fields
        if set(data) not in (required, required | {"cta_url"}) or data["status"] != "draft-unreviewed":
            raise ValueError(f"{path.name}: unsupported metadata/publication status")
        pair, slug = data["pair"], data[f"slug_{language}"]
        try:
            validate_slug(pair)
            validate_slug(slug)
        except (ValidationError, TypeError) as exc:
            raise ValueError(f"{path.name}: invalid identity") from exc
        if len(slug) > 170 or slug in seen[language]:
            raise ValueError(f"{path.name}: duplicate/oversized slug")
        title, summary = data[f"title_{language}"], data[f"summary_{language}"]
        if not all(isinstance(value, str) and value.strip() for value in (title, summary, body)):
            raise ValueError(f"{path.name}: missing content")
        if len(title + (" | آرویون" if language == "fa" else " | Rvion")) > 60 or not 90 <= len(summary) <= 155:
            raise ValueError(f"{path.name}: SEO length contract")
        for key in ("tags", "target_keywords"):
            if not isinstance(data[key], list) or not data[key] or any(
                not isinstance(value, str) or not value.strip() or len(value) > 100 for value in data[key]
            ) or len(data[key]) != len(set(data[key])):
                raise ValueError(f"{path.name}: invalid {key}")
        group = groups.setdefault(pair, {"languages": set(), "tags": [], "values": {}})
        if language in group["languages"]:
            raise ValueError(f"{path.name}: repeated pair language")
        group["languages"].add(language)
        if language == "fa":
            group["tags"] = data["tags"] + group["tags"]
        else:
            group["tags"].extend(data["tags"])
        group["values"].update({key: data[key] for key in fields})
        group["values"][f"body_{language}"] = body
        seen[language].add(slug)
    if not groups or any("fa" not in group["languages"] for group in groups.values()):
        raise ValueError("Every pair requires a Persian edition; bundle must not be empty")
    return [PairedDraft(group["values"]["slug_fa"], tuple(dict.fromkeys(group["tags"])), group["values"])
            for group in groups.values()]
