from django.http import QueryDict
from django.test import SimpleTestCase
from django.utils import translation

from core.order_paths import TOPICS, crm_choices, parse_choices, request_type, start_url, topic_cards
from projects.demo_labels import demo_config_labels


class OrderPathTests(SimpleTestCase):
    def setUp(self):
        translation.activate("fa")
        self.addCleanup(translation.deactivate_all)

    def test_nine_topics_use_existing_features(self):
        self.assertEqual(len(TOPICS), 9)
        for lang in ("fa", "en"):
            for card in topic_cards(lang):
                if card["key"] not in {"crm", "other"}:
                    self.assertTrue(set(card["features"]).issubset(dict(demo_config_labels(lang, card["key"])["features"]).values()))
                self.assertTrue(card["url"].startswith("/fa/start/?type="))
        self.assertEqual(len(crm_choices("fa")[0]), 9)
        self.assertEqual(len(crm_choices("en")[1]), 6)

    def test_query_allowlist_ignores_personal_and_unknown_values(self):
        values = parse_choices(QueryDict("type=crm&addons=webapp&addons=evil&modules=sales,unknown&extensions=ai&phone=secret&name=secret&brief_timing=tomorrow"))
        self.assertEqual(values, {"type": "crm", "addons": "webapp", "modules": "sales", "extensions": "ai"})
        self.assertEqual(parse_choices(QueryDict("type=unknown&modules=sales")), {})

    def test_addon_precedence(self):
        self.assertEqual(request_type({"type": "jewelry"}), "ecommerce")
        self.assertEqual(request_type({"type": "ecommerce", "addons": "webapp,support"}), "webapp")
        self.assertEqual(request_type({"type": "corporate", "addons": "support"}), "website")
        self.assertEqual(request_type({"addons": "support"}), "support")
        self.assertEqual(request_type({"type": "crm", "consult": "1"}), "consultation")

    def test_start_urls_follow_active_language(self):
        with translation.override("en"):
            self.assertEqual(start_url("clinic"), "/en/start/?type=clinic")
