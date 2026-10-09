import json
import base64
import gzip
from types import SimpleNamespace

from django.contrib.auth.models import AnonymousUser
from django.template import Context, Template
from django.test import RequestFactory, SimpleTestCase, override_settings


@override_settings(RVION_ENTRY_ENABLED=True)
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
        self.assertEqual(set(payload), {"scene_gzip", "css", "js"})
        self.assertEqual(payload["css"], "/static/core/css/entry.css?v=3")
        self.assertEqual(payload["js"], "/static/core/js/entry.js?v=2")
        html = gzip.decompress(base64.b64decode(payload["scene_gzip"])).decode("utf-8")
        self.assertEqual(html.count('class="panel"'), 5)
        self.assertLess(len(source.encode("utf-8")), 5000)

    def test_server_localization_and_gateway_routes(self):
        for lang in ("fa", "en"):
            _, payload = self.payload(lang)
            html = gzip.decompress(base64.b64decode(payload["scene_gzip"])).decode("utf-8")
            self.assertIn(f'href="/{lang}/start/"', html)
            self.assertIn(f'href="/{lang}/assessments/"', html)
            self.assertLess(html.index(f'href="/{lang}/start/"'),
                            html.index(f'href="/{lang}/assessments/"'))
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

    @override_settings(RVION_ENTRY_ENABLED=False)
    def test_rollout_switch_keeps_normal_home_disabled(self):
        self.assertEqual(self.payload(), ("", None))

    @override_settings(RVION_ENTRY_ENABLED=False, DEBUG=False)
    def test_preview_query_cannot_enable_production(self):
        request = RequestFactory().get("/fa/?entry_seek=0.8", HTTP_HOST="localhost")
        request.user = AnonymousUser()
        self.assertEqual(Template("{% load entry_ui %}{% entry_payload %}").render(
            Context({"request": request, "lang": "fa"})), "")
