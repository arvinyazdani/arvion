from pathlib import Path
from unittest.mock import patch
from django.test import SimpleTestCase
from ops import seo_crawl_audit


class SeoCrawlerTests(SimpleTestCase):
    def test_isolated_headers_timings_links_and_local_control_origin(self):
        def fetch(args, **kwargs):
            Path(args[args.index('-D') + 1]).write_text(
                'HTTP/1.1 200 OK\r\nSet-Cookie: csrftoken=not-reported; Path=/\r\n'
                'Cache-Control: private, no-store\r\nVary: Cookie\r\n'
            )
            self.assertEqual(args[-1], 'http://127.0.0.1:8202/fa/example/')
            return ('<title>A &amp; B</title><h1>Example</h1>'
                    '<meta name="description" content="A useful description">'
                    '<link rel="canonical" href="https://rvionai.com/fa/example/">'
                    '<a href="/fa/blog/example/?tag=one&amp;q=two">Read</a>'
                    '\n__CODE__200 __T__0.123 __TTFB__0.12')
        with patch.object(seo_crawl_audit, 'sh', side_effect=fetch):
            row = seo_crawl_audit.audit('https://rvionai.com/fa/example/', 'http://127.0.0.1:8202')
        self.assertEqual(row['title'], 'A & B')
        self.assertEqual(row['cookie_names'], ['csrftoken'])
        self.assertNotIn('not-reported', str(row))
        self.assertEqual(row['cache_control'], ['private, no-store'])
        self.assertEqual(row['ttfb'], 0.12)
        self.assertEqual(row['t'], 0.123)
        self.assertEqual(row['links'], ['https://rvionai.com/fa/blog/example/?tag=one&q=two'])
