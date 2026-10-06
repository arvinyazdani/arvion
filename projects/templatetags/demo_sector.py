from django import template
from projects.sector_catalog import sector_catalog

register = template.Library()


@register.inclusion_tag("projects/demo_scenes/sector.html", takes_context=True)
def demo_sector(context):
    lang = context.get("lang", "fa")
    demo = context.get("demo", {})
    category = demo.get("category") if isinstance(demo, dict) else demo.category
    return {"sector": sector_catalog(category, lang), "lang": lang, "demo": demo,
            "full_sample": context.get("full_sample", False)}
