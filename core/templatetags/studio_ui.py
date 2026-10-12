"""Inline the existing home styles, without a second copy of their source."""
from functools import lru_cache
from pathlib import Path
import posixpath
import re

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from django.templatetags.static import static
from django.utils.safestring import mark_safe

register = template.Library()
STYLES = ("core/studio/tour.css", "core/css/home-paths.css", "blog/css/articles.css")
SHELL_STYLES = ('core/css/tokens.css', 'core/css/home-shell.generated.css',
                'core/css/components.css', 'core/css/public-shell.css',
                'core/css/footer-studio.css', 'core/css/order-flow.css',
                'core/css/studio-fonts.generated.css')


def _read_style(name):
    css = Path(finders.find(name)).read_text(encoding='utf-8')
    if name == 'core/css/tokens.css':
        # The final generated font sheet owns the same faces, with disjoint
        # Unicode ranges. Non-home routes still use the canonical tokens intact.
        css = re.sub(r'@font-face\{font-family:Vazirmatn;[^}]+\}', '', css)
    def absolute_url(match):
        url = match.group(1).strip().strip('\"\'')
        if url.startswith(('/', '#', 'data:', 'https:', 'http:')):
            return match.group(0)
        return 'url("' + static(posixpath.normpath(posixpath.join(posixpath.dirname(name), url))) + '")'
    return re.sub(r'url\(([^)]+)\)', absolute_url, css)


@lru_cache(maxsize=2)
def _styles(kind):
    names = STYLES if kind == 'scene' else SHELL_STYLES
    return "\n".join(_read_style(name) for name in names)


@register.simple_tag
def studio_styles(kind='scene'):
    # Repository-owned CSS only: no user input or dynamic CSS interpolation.
    if kind not in ('scene', 'shell'):
        raise ValueError('Unknown studio stylesheet group')
    css = _styles.__wrapped__(kind) if settings.DEBUG else _styles(kind)
    attribute = 'data-studio-styles' if kind == 'scene' else 'data-studio-shell-styles'
    return mark_safe("<style " + attribute + ">" + css + "</style>")
