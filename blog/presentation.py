"""Read-only presentation; publication/translation remain server-owned."""
import html
import math
import re
from django.utils.html import strip_tags


def reading_minutes(source, language):
    return max(1, math.ceil(len(re.findall(r"\S+", strip_tags(source))) / (160 if language == "fa" else 200)))


def reader_content(post, language):
    # Only add generated IDs to already-sanitized HTML; never evaluate templates.
    rendered = post.body_as_html() if language == "fa" else post.body_as_html_en()
    toc = []

    def heading(match):
        level, text = match.groups()
        anchor = f"article-section-{len(toc) + 1}"
        toc.append({"id": anchor, "title": html.unescape(strip_tags(text)), "level": level})
        return f'<h{level} id="{anchor}">{text}</h{level}>'

    return re.sub(r"<h([23])>(.*?)</h\1>", heading, rendered, flags=re.S), toc
