"""A public article translation needs both its own slug and title."""
from django.db.models import Q


def translated_posts(queryset, language):
    slug, title = f"slug_{language}", f"title_{language}"
    return queryset.exclude(
        Q(**{f"{slug}__isnull": True}) | Q(**{slug: ""}) |
        Q(**{f"{title}__isnull": True}) | Q(**{title: ""})
    )


def available_post_languages(post):
    return tuple(language for language in ("fa", "en")
                 if getattr(post, f"slug_{language}") and
                 getattr(post, f"title_{language}"))
