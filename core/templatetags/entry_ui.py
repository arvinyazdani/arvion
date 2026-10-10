"""Server-localized, compressed inert payload; no overlay without JavaScript."""
import base64
import gzip
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
    # Public activation remains off until the control-relative performance gate passes.
    local_preview = (settings.DEBUG and "entry_seek" in request.GET
                     and request.get_host().split(":")[0] in ("localhost", "127.0.0.1"))
    if not getattr(settings, "RVION_ENTRY_ENABLED", False) and not local_preview:
        return ""
    lang = request.path.strip("/")
    with override(lang):
        # HomeView already fetched the published, translated slice. Reuse it;
        # no database lookup, AJAX or session/cache-policy change in this tag.
        html = render_to_string("core/_entry_scene.html", {
            "lang": lang, "latest_posts": context.get("latest_posts", ())})
    scene = base64.b64encode(gzip.compress(html.encode("utf-8"), mtime=0)).decode("ascii")
    return json_script({"scene_gzip": scene, "css": static("core/css/entry.css") + "?v=3",
                        "js": static("core/js/entry.js") + "?v=2"}, "rvion-entry-payload")
