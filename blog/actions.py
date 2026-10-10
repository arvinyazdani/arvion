"""Practical next steps extracted from the article, never invented destinations."""
from html.parser import HTMLParser
from urllib.parse import urlsplit
from django.conf import settings
from django.urls import resolve, Resolver404


class ArticleLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.current = [], None

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.current = [dict(attrs).get('href', ''), []]

    def handle_data(self, data):
        if self.current is not None:
            self.current[1].append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self.current is not None:
            href, parts = self.current
            self.links.append((href, ''.join(parts).strip()))
            self.current = None


def article_actions(body, language):
    parser = ArticleLinks()
    parser.feed(body)
    actions, seen = [], set()
    origin = urlsplit(settings.SITE_URL)
    for href, label in parser.links:
        url = urlsplit(href)
        if (url.scheme and url.scheme not in ('http', 'https')) or (
                url.netloc and (url.netloc != origin.netloc or url.scheme not in ('http', 'https'))):
            continue
        if not label or not url.path.startswith('/' + language + '/') or url.path in seen:
            continue
        try:
            resolve(url.path)
        except Resolver404:
            continue
        path = url.path.removeprefix('/' + language + '/')
        priority = next((rank for rank, prefix in enumerate((
            'tools/', 'assessments/', 'projects/demos/', 'crm/', 'services/', 'contact/'
        )) if path.startswith(prefix)), None)
        if priority is None:
            continue
        seen.add(url.path)
        actions.append({'url': href, 'label': label, 'priority': priority})
    return sorted(actions, key=lambda item: item['priority'])[:4]
