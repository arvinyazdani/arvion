"""Piece 2 server contract: closed choices, real catalogue, no identity."""
import json
from urllib.parse import parse_qs, urlsplit

from django.http import QueryDict
from django.test import TestCase
from django.utils import translation

from core.order_gateway import final_form_url
from core.order_paths import ADDONS, CONSULTATION, TOPICS, crm_choices, parse_choices, start_url
from projects.demo_labels import CATEGORY_FEATURE_KEYS, demo_config_labels


class OrderWizardVocabularyTests(TestCase):
    def setUp(self):
        translation.activate("fa")
        self.addCleanup(translation.deactivate_all)

    def test_each_closed_palette_and_look_is_accepted(self):
        for palette in ("warm", "midnight", "sage", "rose", "ocean", "gold", "violet", "graphite"):
            for look in ("modern", "industrial", "cinematic", "video", "classic", "soft"):
                self.assertEqual(parse_choices({"palette": palette, "look": look}),
                                 {"palette": palette, "look": look})

    def test_invalid_choices_and_free_text_are_not_transportable(self):
        self.assertEqual(parse_choices(QueryDict("palette=custom&look=minimal&brand=PRIVATE&phone=PRIVATE&features=catalog")), {})
        for value in ("Warm", " warm", "#ff0000", "<script>", "", "../gold"):
            self.assertNotIn("palette", parse_choices({"palette": value}))
            self.assertNotIn("look", parse_choices({"look": value}))

    def test_start_and_final_urls_preserve_only_the_closed_choices(self):
        for lang in ("fa", "en"):
            with translation.override(lang):
                url = start_url("corporate", palette="ocean", look="industrial", brand="PRIVATE")
                self.assertEqual(urlsplit(url).path, f"/{lang}/start/")
                self.assertEqual(parse_qs(urlsplit(url).query),
                                 {"type": ["corporate"], "palette": ["ocean"], "look": ["industrial"]})
                url = final_form_url({"type": "corporate", "palette": "ocean", "look": "industrial", "brand": "PRIVATE"})
                self.assertEqual(urlsplit(url).path, f"/{lang}/contact/")
                self.assertNotIn("PRIVATE", url)
                self.assertEqual(parse_qs(urlsplit(url).query)["palette"], ["ocean"])

    def test_specialist_and_consultation_routing_is_unchanged(self):
        for topic, destination in (("clinic", "/fa/clinic-order/"), ("crm", "/fa/crm-order/")):
            response = self.client.get("/en/start/", {"type": topic, "palette": "sage", "look": "soft", "go": "form"})
            self.assertEqual(urlsplit(response.url).path, destination)
            self.assertEqual(parse_qs(urlsplit(response.url).query)["look"], ["soft"])
            consult = self.client.get("/en/start/", {"type": topic, "consult": "1", "palette": "sage"})
            self.assertEqual(urlsplit(consult.url).path, "/en/contact/")

    def test_server_json_uses_the_actual_catalogue_in_each_language(self):
        for lang in ("fa", "en"):
            response = self.client.get(f"/{lang}/start/", {"palette": "rose", "brand": "PRIVATE"})
            html = response.content.decode()
            payload = json.loads(html.split('<script id="order-wizard-data" type="application/json">', 1)[1].split("</script>", 1)[0])
            self.assertEqual(payload["initial"], {"palette": "rose"})
            self.assertEqual([row["key"] for row in payload["topics"]], [topic.key for topic in TOPICS])
            for row in payload["topics"]:
                if row["key"] in CATEGORY_FEATURE_KEYS:
                    self.assertEqual(row["features"], [list(item) for item in demo_config_labels(lang, row["key"])["features"]])
                    self.assertEqual([item[0] for item in row["features"]], list(CATEGORY_FEATURE_KEYS[row["key"]]))
                elif row["key"] == "crm":
                    self.assertEqual(row["features"], [list(item) for item in crm_choices(lang)[0]])
                else:
                    self.assertEqual(row["features"], [])
            self.assertEqual(payload["addons"], [[key, fa if lang == "fa" else en] for key, fa, en in ADDONS])
            self.assertEqual(payload["consultation"], CONSULTATION[0 if lang == "fa" else 1])
            self.assertEqual(len(payload["palettes"]), 8)
            self.assertEqual(len(payload["looks"]), 6)
            self.assertNotIn("PRIVATE", json.dumps(payload))
            self.assertNotIn("session_key", payload)
            self.assertNotIn("brand", payload)
            self.assertEqual(payload["continue_url"], f"/{lang}/start/")

    def test_no_javascript_fallback_keeps_palette_and_look_across_navigation(self):
        page = self.client.get("/fa/start/?palette=gold&look=classic")
        self.assertContains(page, "order-topic-card", count=9)
        consult_query = parse_qs(urlsplit(page.context["order_consultation_url"]).query)
        self.assertEqual(consult_query, {"palette": ["gold"], "look": ["classic"], "consult": ["1"]})
        for card in page.context["order_topics"]:
            self.assertEqual(parse_qs(urlsplit(card["url"]).query)["palette"], ["gold"])
            self.assertEqual(parse_qs(urlsplit(card["url"]).query)["look"], ["classic"])
        page = self.client.get("/fa/start/?type=crm&palette=gold&look=classic")
        self.assertContains(page, 'name="palette" value="gold"')
        self.assertContains(page, 'name="look" value="classic"')
        self.assertContains(page, 'name="go" value="form"')

    def test_preferences_are_readonly_and_prefill_existing_summary_fields(self):
        for lang, palette_label, look_label in (("fa", "اقیانوس", "صنعتی"), ("en", "Ocean", "Industrial")):
            page = self.client.get(f"/{lang}/contact/?type=corporate&palette=ocean&look=industrial&brand=PRIVATE")
            self.assertIn(palette_label, "\n".join(page.context["order_summary"]))
            self.assertIn(look_label, page.context["form"].initial["message"])
            self.assertNotContains(page, 'name="palette"')
            self.assertNotContains(page, 'name="look"')
            self.assertNotIn("PRIVATE", page.context["form"].initial["message"])
        page = self.client.get("/fa/crm-order/?type=crm&palette=ocean&look=industrial")
        self.assertIn("اقیانوس", page.context["form"].initial["additional_notes"])
        self.assertIn("صنعتی", page.context["form"].initial["additional_notes"])

    def test_no_implicit_preselection_or_catalogue_outside_start(self):
        page = self.client.get("/en/start/")
        self.assertEqual(page.context["order_wizard_data"]["initial"], {})
        for path in ("/en/", "/en/contact/", "/fa/crm-order/"):
            self.assertNotContains(self.client.get(path), 'id="order-wizard-data"')
