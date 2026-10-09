"""Read-only presentation; publication/translation remain server-owned."""
import html
import math
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit
from django.conf import settings
from django.utils.html import strip_tags
from django.utils.text import slugify


def reading_minutes(source, language):
    return max(1, math.ceil(len(re.findall(r"\S+", strip_tags(source))) / (160 if language == "fa" else 200)))


class _ReaderParser(HTMLParser):
    """Parse only the model's sanitized HTML, preserving code as literal text."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = {"tag": None, "children": []}
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = {"tag": tag, "attrs": dict(attrs), "children": []}
        self.stack[-1]["children"].append(node)
        if tag != "br":
            self.stack.append(node)

    def handle_endtag(self, tag):
        if len(self.stack) > 1 and self.stack[-1]["tag"] == tag:
            self.stack.pop()

    def handle_data(self, data):
        self.stack[-1]["children"].append(data)


def _text(node):
    return node if isinstance(node, str) else "".join(_text(c) for c in node["children"])


def reader_content(post, language):
    parser = _ReaderParser()
    parser.feed(post.body_as_html() if language == "fa" else post.body_as_html_en())
    toc, used = [], set()
    article = slugify(getattr(post, "slug_" + language) or "article", allow_unicode=True)
    own_host = urlsplit(settings.SITE_URL).netloc

    def render(node, literal=False):
        if isinstance(node, str):
            if language == "fa" and not literal and "{{" not in node and "{%" not in node:
                parts, end = [], 0
                for match in re.finditer(r"[A-Za-z][A-Za-z0-9_+./'-]*(?: +[A-Za-z][A-Za-z0-9_+./'-]*)*", node):
                    parts.extend([html.escape(node[end:match.start()], quote=False),
                                  '<bdi dir="ltr">' + html.escape(match[0], quote=False) + '</bdi>'])
                    end = match.end()
                return "".join(parts) + html.escape(node[end:], quote=False)
            return html.escape(node, quote=False)
        tag, attrs = node["tag"], dict(node.get("attrs", {}))
        if tag in ("h2", "h3"):
            title = _text(node)
            base = "section-" + article + "-" + (slugify(title, allow_unicode=True) or "heading")
            anchor, number = base, 2
            while anchor in used:
                anchor = base + "-" + str(number)
                number += 1
            used.add(anchor)
            attrs["id"] = anchor
            toc.append({"id": anchor, "title": title, "level": tag[1]})
        if tag == "a":
            try:
                external = bool(urlsplit(attrs.get("href", "")).netloc) and urlsplit(attrs.get("href", "")).netloc != own_host
            except ValueError:
                external = False
            if external:
                attrs["rel"] = " ".join(sorted(set(attrs.get("rel", "").split()) | {"noopener"}))
        content = "".join(render(c, literal or tag in ("pre", "code")) for c in node["children"])
        if not tag:
            return content
        attributes = "".join(' ' + k + '="' + html.escape(v or "", quote=True) + '"' for k, v in attrs.items())
        return '<' + tag + attributes + '>' + ('' if tag == 'br' else content + '</' + tag + '>')

    return render(parser.root), toc


def article_dek(post, language):
    """Remove a duplicated title prefix for presentation only; SEO stays exact."""
    summary = getattr(post, "summary_" + language) or ""
    title = getattr(post, "title_" + language) or ""
    if title and summary.startswith(title):
        summary = summary[len(title):].lstrip(" .،؛:؟?!–—-")
    return summary
