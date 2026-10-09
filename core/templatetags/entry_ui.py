"""Server-localized, inert payload; no overlay is rendered without JavaScript."""
from django import template
from django.conf import settings
from django.templatetags.static import static
from django.template.loader import render_to_string
from django.utils.html import json_script
from django.utils.translation import override

register = template.Library()


@register.simple_tag(takes_context=True)
def entry_payload(context):
    request = context.get("request")
    if not request or request.user.is_staff or request.path not in ("/fa/", "/en/"):
        return ""
    # Performance gate is currently BLOCKED. No automatic rollout of this preview.
    local_preview = (settings.DEBUG and "entry_seek" in request.GET
                     and request.get_host().split(":")[0] in ("localhost", "127.0.0.1"))
    if not getattr(settings, "RVION_ENTRY_ENABLED", False) and not local_preview:
        return ""
    lang = request.path.strip("/")
    with override(lang):
        html = render_to_string("core/_entry_scene.html", {"lang": lang})
    return json_script({"html": html, "css": static("core/css/entry.css") + "?v=2",
                        "js": static("core/js/entry.js") + "?v=1"}, "rvion-entry-payload")
