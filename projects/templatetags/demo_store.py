from django import template
from projects.storefront_catalog import storefront_catalog

register = template.Library()


@register.inclusion_tag("projects/demo_scenes/storefront.html", takes_context=True)
def demo_storefront(context):
    lang = context.get("lang", "fa")
    catalog = storefront_catalog(lang)
    return {"lang": lang, "store": catalog, "products": catalog["products"]}
