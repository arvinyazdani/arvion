import json
from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.template import Context, Template
from django.test import RequestFactory, SimpleTestCase


class EntryPayloadTests(SimpleTestCase):
    def payload(self, lang="fa", staff=False, path=None):
        request = RequestFactory().get(path or f"/{lang}/")
        request.user = SimpleNamespace(is_staff=True) if staff else AnonymousUser()
        source = Template("{% load entry_ui %}{% entry_payload %}").render(
            Context({"request": request, "lang": lang}))
        return source, json.loads(source.split(">", 1)[1].split("</script>")[0]) if source else None

    def test_payload_is_inert_json_and_only_two_local_static_assets(self):
        source, payload = self.payload()
        self.assertIn('type="application/json"', source)
        self.assertNotIn('<div', source)
        self.assertEqual(set(payload), {"html", "css", "js"})
        self.assertEqual(payload["css"], "/static/core/css/entry.css?v=1")
        self.assertEqual(payload["js"], "/static/core/js/entry.js?v=1")
        self.assertEqual(payload["html"].count('class="panel"'), 5)

    def test_server_localization_and_gateway_routes(self):
        for lang in ("fa", "en"):
            _, payload = self.payload(lang)
            html = payload["html"]
            self.assertIn(f'href="/{lang}/start/"', html)
            self.assertIn(f'href="/{lang}/assessments/"', html)
            self.assertNotIn("data-fa=", html)
            self.assertNotIn("data-en=", html)
            if lang == "en":
                self.assertNotRegex(html, r"[\u0600-\u06ff]")
                self.assertIn("Discovery", html)
            else:
                self.assertIn("نیازسنجی", html)

    def test_staff_and_non_home_have_no_payload(self):
        self.assertEqual(self.payload(staff=True), ("", None))
        self.assertEqual(self.payload(path="/fa/start/"), ("", None))
