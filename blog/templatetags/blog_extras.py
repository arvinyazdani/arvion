from django import template
from blog.presentation import reading_minutes
from blog.covers import cover_alt as editorial_cover_alt
from blog.covers import cover_url as editorial_cover_url

register = template.Library()

@register.inclusion_tag("blog/includes/context_reading.html", takes_context=True)
def context_reading(context):
    """Publication-aware incoming links, including protected gallery via shared shell."""
    from blog.models import Post
    from blog.languages import translated_posts
    request = context.get("request")
    route = request.resolver_match.view_name if request and request.resolver_match else ""
    language = context.get("lang", "fa")
    costs = "custom-software-cost-us-2026-crm-accounting-b2b"
    hiring = "hire-django-freelancer-us-rates-2026"
    raya = "personal-accounting-economic-progress-raya"
    slugs = {
        "core:home": (costs, hiring, raya), "home": (costs, hiring, raya),
        "services:detail": (costs, hiring), "crm_product": (costs, hiring),
        "projects:demo_gallery": (costs, hiring), "projects:demos": (costs, hiring),
    }.get(route, ())
    if route == "blog:detail":
        post = context.get("post")
        current = getattr(post, "slug_fa", "")
        if current in (costs, hiring, "enterprise-crm-development-cost-stages", "custom-or-ready-made-crm", "corporate-website-cost-1405"):
            slugs = tuple(slug for slug in (costs, hiring) if slug != current)
    posts = list(translated_posts(Post.objects.published().filter(slug_fa__in=slugs), language)) if slugs else []
    return {"reading_posts": posts, "lang": language}

@register.filter
def cover_url(post, language):
    return editorial_cover_url(post, language)

@register.filter
def local_number(value, language):
    return str(value).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")) if language == "fa" else value

@register.filter
def primary_tag(post, language):
    tags = [tag.name for tag in post.tags.all()]
    localized = [name for name in tags if contains_persian(name) == (language == "fa")]
    return next(iter(localized or (tags if language == "fa" else [])), "")

@register.filter
def cover_alt(post, language):
    return editorial_cover_alt(post, language)

@register.filter
def contains_persian(value):
    return any('\u0600' <= char <= '\u06ff' for char in str(value))


@register.filter
def read_minutes(post, language):
    source = post.body_as_html() if language == "fa" else post.body_as_html_en()
    return reading_minutes(source, language)
