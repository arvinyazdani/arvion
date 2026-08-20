from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, SimpleTestCase

from core.views.i18n import switch_language


class LanguageRedirectSecurityTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def request(self, referer):
        request = self.factory.get(
            "/language/", {"lang": "en"}, HTTP_REFERER=referer,
        )
        SessionMiddleware(lambda value: None).process_request(request)
        return request

    def test_language_switch_does_not_redirect_to_external_referer(self):
        response = switch_language(self.request("https://attacker.example/phish"))

        self.assertEqual(response.url, "/")

    def test_language_switch_keeps_same_host_referer(self):
        response = switch_language(self.request("http://testserver/fa/services/"))

        self.assertEqual(response.url, "http://testserver/fa/services/")
