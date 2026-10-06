from datetime import timedelta
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone, translation

from leads.models import Lead
from .models import DemoSelection, DemoTemplate, Project


class ProjectTests(TestCase):
    def setUp(self):
        translation.activate("fa")
        self.addCleanup(translation.deactivate_all)
        self.project = Project.objects.create(title_fa="پروژه", title_en="Project", slug="project", is_active=True)

    def test_project_uses_slug_url(self):
        response = self.client.get(reverse("projects:detail", args=["project"]), {"lang": "en"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Project")

    def test_project_labels_follow_page_language(self):
        fa_list = self.client.get(reverse("projects:list") + "?lang=fa")
        self.assertRedirects(fa_list, reverse("projects:demo_gallery"), status_code=302, fetch_redirect_response=False)

        en_detail = self.client.get(reverse("projects:detail", args=["project"]) + "?lang=en")
        self.assertContains(en_detail, "Case study")
        self.assertContains(en_detail, "LINKS")
        self.assertNotContains(en_detail, "مطالعه موردی")

    def test_inactive_project_is_hidden(self):
        self.project.is_active = False
        self.project.save()
        self.assertEqual(self.client.get(self.project.get_absolute_url()).status_code, 404)

    def test_gallery_shows_fictional_demos_and_configurator_creates_session_selection(self):
        demo = DemoTemplate.objects.create(
            slug="demo-test", category="ecommerce", title_fa="دموی تست", title_en="Test demo",
            tagline_fa="نمونه فرضی", tagline_en="Fictional demo", fictional_brand_fa="برند فرضی",
            fictional_brand_en="TEST BRAND", style_key="minimal", default_features=["payment"],
        )
        gallery = self.client.get(reverse("projects:demo_gallery") + "?lang=fa")
        self.assertContains(gallery, "دموی تست")
        self.assertContains(gallery, "بدون ثبت‌نام")
        self.assertContains(gallery, "بازکردن و شخصی‌سازی")
        preview = self.client.get(reverse("projects:demo_preview", args=[demo.slug]) + "?lang=fa")
        self.assertContains(preview, "برند فرضی")
        self.assertContains(preview, reverse("projects:demo_full", args=[demo.slug]))
        response = self.client.post(reverse("projects:demo_configure", args=[demo.slug]), {
            "submission_token": "gallery-flow-token",
            "brand_preview": "فروشگاه من", "theme": "custom", "custom_color": "#123abc",
            "personality": "minimal", "features": ["payment", "catalog"],
        })
        selection = DemoSelection.objects.get()
        self.assertRedirects(response, reverse("leads:contact") + f"?demo={selection.public_token}&request_type=ecommerce")
        self.assertEqual(selection.selections["features"], ["payment", "catalog"])
        self.assertEqual(selection.selections["brand"], "فروشگاه من")
        self.assertEqual(selection.selections["custom_color"], "#123abc")

        full = self.client.get(reverse("projects:demo_full", args=[demo.slug]) + "?lang=fa")
        self.assertContains(full, 'content="noindex,nofollow"', html=False)
        self.assertContains(full, "بازگشت به انتخاب‌ها")
        self.assertContains(full, 'data-demo-view="desktop"', html=False)
        self.assertContains(full, 'data-demo-view="mobile"', html=False)
        self.assertContains(full, '<h1>', html=False)
        self.assertContains(full, 'id="sample-content"', html=False)

    def test_invalid_custom_colour_is_rejected_without_creating_selection(self):
        demo = DemoTemplate.objects.create(
            slug="invalid-colour", category="portfolio", title_fa="تست", title_en="Test",
            tagline_fa="شرح", tagline_en="Description", fictional_brand_fa="فرضی",
            fictional_brand_en="FICTIONAL", style_key="editorial", default_features=[],
        )
        response = self.client.post(reverse("projects:demo_configure", args=[demo.slug]), {
            "submission_token": "invalid-colour-token",
            "theme": "custom", "custom_color": "not-a-colour", "personality": "editorial",
        })
        self.assertRedirects(
            response,
            reverse("projects:demo_preview", args=[demo.slug]) + "?invalid=1",
            fetch_redirect_response=False,
        )
        self.assertFalse(DemoSelection.objects.exists())

    def test_missing_submission_token_is_rejected_without_creating_selection(self):
        demo = DemoTemplate.objects.create(
            slug="no-token", category="portfolio", title_fa="تست", title_en="Test",
            tagline_fa="شرح", tagline_en="Description", fictional_brand_fa="فرضی",
            fictional_brand_en="FICTIONAL", style_key="editorial", default_features=[],
        )
        response = self.client.post(reverse("projects:demo_configure", args=[demo.slug]), {
            "theme": "warm", "personality": "editorial",
        })
        self.assertRedirects(
            response, reverse("projects:demo_preview", args=[demo.slug]) + "?invalid=1",
            fetch_redirect_response=False,
        )
        self.assertFalse(DemoSelection.objects.exists())

    def test_configurator_is_single_page_and_preserves_state_between_views(self):
        script = (Path(settings.BASE_DIR) / "projects/static/projects/js/demo-configurator.js").read_text(encoding="utf-8")
        self.assertIn("history.replaceState", script)
        self.assertIn("sessionStorage.setItem", script)
        self.assertIn('state.theme = "custom"', script)
        self.assertIn('setAttribute("aria-pressed"', script)
        self.assertIn("data-demo-back", script)
        # The only reload in the file is narrowly gated to a real
        # back-forward-cache restore (so a stale hidden submission_token is
        # replaced before the visitor can act on it) — never unconditional,
        # so ordinary navigation still stays a single page.
        self.assertIn('addEventListener("pageshow", (event) => { if (event.persisted) location.reload(); })', script)

    def test_restaurant_preview_has_category_specific_menu_scene(self):
        demo = DemoTemplate.objects.create(
            slug="restaurant-scene", category="restaurant", title_fa="کافه تست", title_en="Test café",
            tagline_fa="طعم تازه", tagline_en="A fresh taste", fictional_brand_fa="کافه فرضی",
            fictional_brand_en="FICTIONAL CAFE", style_key="bold", default_features=["booking"],
        )
        response = self.client.get(reverse("projects:demo_preview", args=[demo.slug]) + "?lang=fa")
        self.assertContains(response, "demo-site-restaurant")
        self.assertContains(response, "پیشنهاد امشب")
        self.assertContains(response, "رزرو میز")

    def test_each_business_category_renders_its_own_bilingual_sample_scene(self):
        scenes = {
            "ecommerce": ("demo-scene-shop", "گلدان آوید", "Avid sculptural vase"),
            "restaurant": ("demo-scene-restaurant", "پاستای زعفرانی", "Saffron butter pasta"),
            "portfolio": ("demo-scene-portfolio", "بازآفرینی تجربه خرید روزمره", "Reframing the everyday shop"),
            "corporate": ("demo-scene-corporate", "تحلیل و مشاوره", "Discovery & advisory"),
            "clinic": ("demo-scene-clinic", "انتخاب نوبت · نمایشی و غیرقابل رزرو", "APPOINTMENT PICKER · PREVIEW ONLY"),
            "education": ("demo-scene-education", "مبانی طراحی محصول", "Product design essentials"),
            "jewelry": ("demo-scene-jewelry", "انگشتر آفتاب", "Aftab signet ring"),
        }
        for category, (scene_class, sample_fa, sample_en) in scenes.items():
            with self.subTest(category=category):
                demo = DemoTemplate.objects.create(
                    slug=f"scene-{category}", category=category,
                    title_fa="نمونه تست", title_en="Sample test",
                    tagline_fa="روایت نمونه", tagline_en="Sample story",
                    fictional_brand_fa="برند فرضی", fictional_brand_en="FICTIONAL BRAND",
                    style_key="modern", default_features=[],
                )
                fa_response = self.client.get(reverse("projects:demo_preview", args=[demo.slug]) + "?lang=fa")
                self.assertEqual(fa_response.status_code, 200)
                self.assertContains(fa_response, scene_class, html=False)
                self.assertContains(fa_response, sample_fa)
                en_response = self.client.get(reverse("projects:demo_preview", args=[demo.slug]) + "?lang=en")
                self.assertEqual(en_response.status_code, 200)
                self.assertContains(en_response, sample_en)
                self.assertContains(en_response, 'data-default-personality="modern"', html=False)

    def test_jewelry_demo_is_seeded_and_its_real_order_handoff_is_ecommerce(self):
        seeded_demo = DemoTemplate.objects.get(slug="sarvin-atelier")
        self.assertEqual(seeded_demo.category, "jewelry")
        gallery = self.client.get(reverse("projects:demo_gallery") + "?lang=fa")
        self.assertContains(gallery, "گالری طلا و جواهر")
        demo = DemoTemplate.objects.create(
            slug="jewelry-order-flow", category="jewelry", title_fa="گالری جواهر تست",
            title_en="Test jewellery atelier", tagline_fa="یک انتخاب ماندگار",
            tagline_en="A lasting choice", fictional_brand_fa="سروین",
            fictional_brand_en="SARVIN", style_key="luxury",
            default_features=["catalog", "booking"],
        )
        preview = self.client.get(reverse("projects:demo_preview", args=[demo.slug]) + "?lang=fa")
        self.assertContains(preview, "قیمت روز · نیازمند استعلام")
        self.assertContains(preview, "عیار، وزن، اجرت ساخت، موجودی و قیمت روز")
        self.assertContains(preview, 'value="gold" checked', html=False)
        token = preview.context["submission_token"]
        response = self.client.post(reverse("projects:demo_configure", args=[demo.slug]), {
            "submission_token": token, "brand_preview": "جواهر من", "theme": "gold",
            "personality": "luxury", "features": ["catalog", "booking", "blog"],
        })
        selection = DemoSelection.objects.get()
        self.assertRedirects(
            response,
            reverse("leads:contact") + f"?demo={selection.public_token}&request_type=ecommerce",
            fetch_redirect_response=False,
        )
        self.assertEqual(selection.selections["features"], ["catalog", "booking"])
        self.assertEqual(selection.selections["theme"], "gold")

    def test_mobile_customizer_uses_one_live_preview_and_an_accessible_bottom_sheet(self):
        demo = DemoTemplate.objects.create(
            slug="mobile-customizer", category="jewelry", title_fa="نمونه موبایل",
            title_en="Mobile sample", tagline_fa="شرح", tagline_en="Description",
            fictional_brand_fa="فرضی", fictional_brand_en="FICTIONAL",
            style_key="luxury", default_features=["catalog"],
        )
        response = self.client.get(reverse("projects:demo_preview", args=[demo.slug]))
        self.assertContains(response, 'data-config-toggle', html=False)
        self.assertContains(response, 'aria-controls="demo-config-body"', html=False)
        self.assertContains(response, 'data-config-backdrop', html=False)
        self.assertContains(response, 'data-config-open', html=False)
        self.assertContains(response, 'name="personality" value="industrial"', html=False)
        self.assertContains(response, "demo-scene-jewelry")
        self.assertContains(response, "demo-jewel-ring")
        css = (Path(settings.BASE_DIR) / "projects/static/projects/css/demo-gallery.css").read_text(encoding="utf-8")
        self.assertIn(".demo-config.is-mobile-open", css)
        self.assertIn("prefers-reduced-motion:reduce", css)
        script = (Path(settings.BASE_DIR) / "projects/static/projects/js/demo-configurator.js").read_text(encoding="utf-8")
        self.assertIn('setAttribute("aria-modal", "true")', script)
        self.assertIn('event.key === "Escape"', script)
        self.assertIn('announceChange(control.dataset.featureLabel', script)

    def test_each_category_has_a_distinct_working_preview_flow_and_feature_modules(self):
        markers = {
            "ecommerce": ('data-store-add', 'data-demo-filter-group="shop"', "data-feature-module=\"payment\""),
            "restaurant": ('data-demo-choice-group="reservation"', 'data-demo-filter-group="menu"', "data-feature-module=\"booking\""),
            "portfolio": ('data-demo-filter-group="portfolio"', "نقش و روند طراحی", "data-feature-module=\"blog\""),
            "corporate": ("data-demo-group-summary", "اولویت زمانی", "data-feature-module=\"booking\""),
            "clinic": ('data-demo-choice-select', 'data-demo-choice-day-group', "حریم مراجعه‌کننده", "data-feature-module=\"payment\""),
            "education": ("سرفصل‌ها", "درس صوتی کوتاه", "data-feature-module=\"membership\""),
            "jewelry": ('data-demo-attribute-summary', "عیار پیشنهادی", "data-feature-module=\"payment\""),
        }
        for category, expected_markers in markers.items():
            with self.subTest(category=category):
                demo = DemoTemplate.objects.create(
                    slug=f"working-flow-{category}", category=category,
                    title_fa="نمونه تست", title_en="Test sample",
                    tagline_fa="روایت نمونه", tagline_en="A sample story",
                    fictional_brand_fa="برند فرضی", fictional_brand_en="FICTIONAL BRAND",
                    style_key="modern", default_features=[],
                )
                fa_response = self.client.get(reverse("projects:demo_preview", args=[demo.slug]) + "?lang=fa")
                self.assertEqual(fa_response.status_code, 200)
                for marker in expected_markers:
                    self.assertContains(fa_response, marker, html=False)
                en_response = self.client.get(reverse("projects:demo_preview", args=[demo.slug]) + "?lang=en")
                self.assertEqual(en_response.status_code, 200)
                self.assertContains(en_response, "data-demo-configurator", html=False)

        script = (Path(settings.BASE_DIR) / "projects/static/projects/js/demo-configurator.js").read_text(encoding="utf-8")
        self.assertIn("module.hidden = !enabled", script)
        self.assertIn("sampleBasketCount += 1", script)
        self.assertIn("activeFilters.set(groupKey, button.dataset.demoFilter)", script)
        self.assertIn("parts.join(\" · \")", script)
        self.assertIn('window.matchMedia("(max-width: 760px)").matches ? "mobile" : "desktop"', script)

        stylesheet = (Path(settings.BASE_DIR) / "projects/static/projects/css/demo-gallery.css").read_text(encoding="utf-8")
        self.assertIn('.demo-stage[data-view="mobile"] .demo-site{width:100%;max-width:none', stylesheet)
        self.assertIn(".demo-editor-strip{order:1}", stylesheet)
        self.assertIn(".demo-open-config{position:static", stylesheet)

    def test_preview_page_embeds_a_fresh_submission_token_on_every_render(self):
        demo = DemoTemplate.objects.create(
            slug="fresh-token", category="portfolio", title_fa="تست", title_en="Test",
            tagline_fa="شرح", tagline_en="Description", fictional_brand_fa="فرضی",
            fictional_brand_en="FICTIONAL", style_key="editorial", default_features=[],
        )
        url = reverse("projects:demo_preview", args=[demo.slug]) + "?lang=fa"
        first = self.client.get(url)
        second = self.client.get(url)

        def extract_token(response):
            marker = 'name="submission_token" value="'
            body = response.content.decode()
            start = body.index(marker) + len(marker)
            return body[start:body.index('"', start)]

        first_token, second_token = extract_token(first), extract_token(second)
        self.assertTrue(first_token)
        self.assertNotEqual(first_token, second_token)

    def test_submitting_the_same_submission_token_twice_creates_only_one_selection(self):
        demo = DemoTemplate.objects.create(
            slug="idempotent-demo", category="ecommerce", title_fa="دموی ثابت", title_en="Stable demo",
            tagline_fa="شرح", tagline_en="Description", fictional_brand_fa="فرضی",
            fictional_brand_en="FICTIONAL", style_key="minimal", default_features=[],
        )
        payload = {
            "submission_token": "same-token-abc", "brand_preview": "برند من",
            "theme": "warm", "personality": "minimal", "features": ["payment"],
        }
        first = self.client.post(reverse("projects:demo_configure", args=[demo.slug]), payload)
        second = self.client.post(reverse("projects:demo_configure", args=[demo.slug]), payload)

        self.assertEqual(DemoSelection.objects.count(), 1)
        selection = DemoSelection.objects.get()
        expected_redirect = reverse("leads:contact") + f"?demo={selection.public_token}&request_type=ecommerce"
        self.assertRedirects(first, expected_redirect, fetch_redirect_response=False)
        self.assertRedirects(second, expected_redirect, fetch_redirect_response=False)

    def test_a_new_submission_token_creates_a_new_selection(self):
        demo = DemoTemplate.objects.create(
            slug="two-real-choices", category="ecommerce", title_fa="دموی دوگانه", title_en="Two-choice demo",
            tagline_fa="شرح", tagline_en="Description", fictional_brand_fa="فرضی",
            fictional_brand_en="FICTIONAL", style_key="minimal", default_features=[],
        )
        configure_url = reverse("projects:demo_configure", args=[demo.slug])
        self.client.post(configure_url, {
            "submission_token": "token-one", "theme": "warm", "personality": "minimal", "features": [],
        })
        self.client.post(configure_url, {
            "submission_token": "token-two", "theme": "sage", "personality": "editorial", "features": [],
        })

        self.assertEqual(DemoSelection.objects.count(), 2)
        self.assertEqual(
            sorted(DemoSelection.objects.values_list("submission_token", flat=True)),
            ["token-one", "token-two"],
        )

    def test_reused_submission_token_from_a_different_session_is_rejected(self):
        demo = DemoTemplate.objects.create(
            slug="cross-session-demo", category="ecommerce", title_fa="دموی مشترک", title_en="Shared demo",
            tagline_fa="شرح", tagline_en="Description", fictional_brand_fa="فرضی",
            fictional_brand_en="FICTIONAL", style_key="minimal", default_features=[],
        )
        configure_url = reverse("projects:demo_configure", args=[demo.slug])
        payload = {"submission_token": "shared-token", "theme": "warm", "personality": "minimal", "features": []}

        owner = Client()
        owner_response = owner.post(configure_url, payload)
        self.assertEqual(DemoSelection.objects.count(), 1)
        original = DemoSelection.objects.get()
        self.assertEqual(original.session_key, owner.session.session_key)

        intruder = Client()
        intruder_response = intruder.post(configure_url, payload)

        # No second row, no exposure of the first session's row, no attachment.
        self.assertRedirects(
            intruder_response, reverse("projects:demo_preview", args=[demo.slug]) + "?invalid=1",
            fetch_redirect_response=False,
        )
        self.assertEqual(DemoSelection.objects.count(), 1)
        original.refresh_from_db()
        self.assertEqual(original.session_key, owner.session.session_key)
        self.assertNotEqual(original.session_key, intruder.session.session_key)
        self.assertNotIn("demo_selection_token", intruder.session)
        # The legitimate owner's redirect is unaffected by the replay attempt.
        self.assertRedirects(
            owner_response, reverse("leads:contact") + f"?demo={original.public_token}&request_type=ecommerce",
            fetch_redirect_response=False,
        )

    def test_reused_submission_token_with_edited_data_is_rejected_and_original_kept(self):
        """A stale token resubmitted with different data (the classic
        Back-then-edit case without a page reload) must not touch the
        original row or create a second one — but the visitor's just-entered
        choices must not be silently lost either."""
        demo = DemoTemplate.objects.create(
            slug="edited-resubmit", category="ecommerce", title_fa="دموی ویرایش‌شده", title_en="Edited demo",
            tagline_fa="شرح", tagline_en="Description", fictional_brand_fa="فرضی",
            fictional_brand_en="FICTIONAL", style_key="minimal", default_features=[],
        )
        configure_url = reverse("projects:demo_configure", args=[demo.slug])
        self.client.post(configure_url, {
            "submission_token": "edited-token", "theme": "warm", "personality": "minimal", "features": [],
        })
        response = self.client.post(configure_url, {
            "submission_token": "edited-token", "theme": "sage", "personality": "editorial",
            "features": ["blog"], "brand_preview": "برند تازه",
        })

        self.assertEqual(DemoSelection.objects.count(), 1)
        self.assertEqual(DemoSelection.objects.get().selections["theme"], "warm")
        self.assertEqual(response.status_code, 302)
        redirect_url = response.url
        self.assertTrue(redirect_url.startswith(reverse("projects:demo_preview", args=[demo.slug]) + "?"))
        self.assertIn("stale=1", redirect_url)
        # The edited values are carried forward so nothing is silently lost —
        # the configurator restores exactly these from the URL on load.
        self.assertIn("theme=sage", redirect_url)
        self.assertIn("personality=editorial", redirect_url)
        self.assertIn("features=blog", redirect_url)
        self.assertIn("%D8%A8%D8%B1%D9%86%D8%AF+%D8%AA%D8%A7%D8%B2%D9%87", redirect_url)  # "برند تازه"

        follow_up = self.client.get(redirect_url)
        self.assertContains(follow_up, 'class="demo-notice"', html=False)
        self.assertNotContains(follow_up, 'class="demo-error"', html=False)
        en_follow_up = self.client.get(redirect_url.replace(f"/{demo.slug}/", f"/{demo.slug}/") + "&lang=en")
        self.assertContains(en_follow_up, "This page was refreshed and your choices were kept")

    def test_real_back_then_change_with_a_fresh_token_creates_a_second_valid_selection(self):
        """The path the pageshow/bfcache reload is meant to produce: the
        visitor's second submission already carries a token the server has
        never seen, so it succeeds immediately with no rejection at all."""
        demo = DemoTemplate.objects.create(
            slug="real-back-demo", category="ecommerce", title_fa="دموی بازگشت", title_en="Back demo",
            tagline_fa="شرح", tagline_en="Description", fictional_brand_fa="فرضی",
            fictional_brand_en="FICTIONAL", style_key="minimal", default_features=[],
        )
        configure_url = reverse("projects:demo_configure", args=[demo.slug])

        first = self.client.post(configure_url, {
            "submission_token": "back-token-1", "theme": "warm", "personality": "minimal", "features": [],
        })
        second = self.client.post(configure_url, {
            "submission_token": "back-token-2", "theme": "sage", "personality": "editorial", "features": ["blog"],
        })

        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        self.assertEqual(DemoSelection.objects.count(), 2)
        first_selection, second_selection = DemoSelection.objects.order_by("created_at")
        self.assertNotEqual(first_selection.selections, second_selection.selections)
        self.assertEqual(first_selection.selections["theme"], "warm")
        self.assertEqual(second_selection.selections["theme"], "sage")
        self.assertRedirects(
            second, reverse("leads:contact") + f"?demo={second_selection.public_token}&request_type=ecommerce",
            fetch_redirect_response=False,
        )

    def test_concurrent_race_on_the_same_token_falls_back_to_the_winning_row(self):
        """A near-simultaneous duplicate request commits its row a moment
        after this request's own existence check ran; the resulting
        IntegrityError from the real unique constraint must be recoverable
        via the nested transaction, with no duplicate row and no error page."""
        demo = DemoTemplate.objects.create(
            slug="race-demo", category="ecommerce", title_fa="دموی رقابتی", title_en="Race demo",
            tagline_fa="شرح", tagline_en="Description", fictional_brand_fa="فرضی",
            fictional_brand_en="FICTIONAL", style_key="minimal", default_features=[],
        )
        payload = {"submission_token": "race-token", "theme": "warm", "personality": "minimal", "features": []}
        configure_url = reverse("projects:demo_configure", args=[demo.slug])

        # Prime the session so the winner's row matches this request's own
        # session_key, then pre-create the "winner" row — the concurrent
        # request that committed a moment before this one's existence check.
        self.client.get(reverse("projects:demo_preview", args=[demo.slug]))
        session_key = self.client.session.session_key
        winner = DemoSelection.objects.create(
            template=demo, session_key=session_key, submission_token=payload["submission_token"],
            selections={"theme": "warm", "personality": "minimal", "features": [], "custom_color": "", "brand": demo.fictional_brand_fa},
        )

        # Simulate "the row did not exist yet" for exactly the first lookup,
        # so the view proceeds to create() and hits the real unique
        # constraint that `winner` already occupies.
        original_filter = DemoSelection.objects.filter
        seen = {"count": 0}

        def filter_missing_on_first_call(*args, **kwargs):
            seen["count"] += 1
            if seen["count"] == 1:
                return DemoSelection.objects.none()
            return original_filter(*args, **kwargs)

        with patch("projects.views.projects.DemoSelection.objects.filter", side_effect=filter_missing_on_first_call):
            response = self.client.post(configure_url, payload)

        self.assertEqual(DemoSelection.objects.count(), 1)
        self.assertRedirects(
            response, reverse("leads:contact") + f"?demo={winner.public_token}&request_type=ecommerce",
            fetch_redirect_response=False,
        )

    def test_integrity_error_inside_a_request_level_atomic_block_still_allows_recovery(self):
        """Reproduces what `DATABASES[...]['ATOMIC_REQUESTS'] = True` does to
        every real request — the whole view runs inside one atomic() block —
        without needing to flip that project-wide database setting. Without
        the create() being wrapped in its own nested `transaction.atomic()`,
        the IntegrityError below poisons this outer block and the very next
        query raises TransactionManagementError instead of completing."""
        demo = DemoTemplate.objects.create(
            slug="atomic-request-demo", category="ecommerce", title_fa="دموی تراکنش", title_en="Atomic demo",
            tagline_fa="شرح", tagline_en="Description", fictional_brand_fa="فرضی",
            fictional_brand_en="FICTIONAL", style_key="minimal", default_features=[],
        )
        payload = {"submission_token": "atomic-token", "theme": "warm", "personality": "minimal", "features": []}
        configure_url = reverse("projects:demo_configure", args=[demo.slug])

        self.client.get(reverse("projects:demo_preview", args=[demo.slug]))
        session_key = self.client.session.session_key
        winner = DemoSelection.objects.create(
            template=demo, session_key=session_key, submission_token=payload["submission_token"],
            selections={"theme": "warm", "personality": "minimal", "features": [], "custom_color": "", "brand": demo.fictional_brand_fa},
        )

        original_filter = DemoSelection.objects.filter
        seen = {"count": 0}

        def filter_missing_on_first_call(*args, **kwargs):
            seen["count"] += 1
            if seen["count"] == 1:
                return DemoSelection.objects.none()
            return original_filter(*args, **kwargs)

        with patch("projects.views.projects.DemoSelection.objects.filter", side_effect=filter_missing_on_first_call):
            with transaction.atomic():
                response = self.client.post(configure_url, payload)
            # If the internal create() were not wrapped in its own nested
            # atomic(), the IntegrityError raised while `in_atomic_block` is
            # True here would have marked this connection `needs_rollback`,
            # and this next ordinary query would raise
            # `TransactionManagementError` instead of returning a row.
            self.assertEqual(DemoSelection.objects.filter(pk=winner.pk).count(), 1)

        self.assertEqual(DemoSelection.objects.count(), 1)
        self.assertRedirects(
            response, reverse("leads:contact") + f"?demo={winner.public_token}&request_type=ecommerce",
            fetch_redirect_response=False,
        )


class DemoSelectionCleanupCommandTests(TestCase):
    """`cleanup_demo_selections`: safe, batch-safe lifecycle cleanup for
    abandoned DemoSelection rows."""

    def _make_selection(self, *, slug, session_key="cleanup-session"):
        template = DemoTemplate.objects.create(
            slug=slug, category="ecommerce", title_fa="دموی تست", title_en="Test demo",
            tagline_fa="فرضی", tagline_en="Fictional", fictional_brand_fa="برند فرضی مخفی",
            fictional_brand_en="Secret fictional brand", style_key="minimal",
        )
        return DemoSelection.objects.create(
            template=template, session_key=session_key, selections={"theme": "warm"},
        )

    def _backdate(self, selection, days):
        DemoSelection.objects.filter(pk=selection.pk).update(updated_at=timezone.now() - timedelta(days=days))

    def test_dry_run_reports_stale_unattached_selection_without_deleting_it(self):
        stale = self._make_selection(slug="cleanup-stale-1")
        self._backdate(stale, 31)
        out = StringIO()
        call_command("cleanup_demo_selections", stdout=out)
        self.assertIn("1", out.getvalue())
        self.assertTrue(DemoSelection.objects.filter(pk=stale.pk).exists())

    def test_apply_deletes_the_same_record_in_the_test_database(self):
        stale = self._make_selection(slug="cleanup-stale-2")
        self._backdate(stale, 31)
        call_command("cleanup_demo_selections", "--apply", stdout=StringIO())
        self.assertFalse(DemoSelection.objects.filter(pk=stale.pk).exists())

    def test_selection_attached_to_lead_is_never_reported_or_deleted_even_if_very_old(self):
        stale = self._make_selection(slug="cleanup-stale-3")
        self._backdate(stale, 365)
        Lead.objects.create(
            name="مشتری پیوسته", email_or_telegram="attached@example.com", message="پیام آزمایشی",
            privacy_accepted_at=timezone.now(), demo_selection=stale,
        )
        out = StringIO()
        call_command("cleanup_demo_selections", stdout=out)
        self.assertIn("0", out.getvalue())
        call_command("cleanup_demo_selections", "--apply", stdout=StringIO())
        self.assertTrue(DemoSelection.objects.filter(pk=stale.pk).exists())

    def test_fresh_unattached_selection_is_not_deleted(self):
        fresh = self._make_selection(slug="cleanup-fresh-1")
        call_command("cleanup_demo_selections", "--apply", stdout=StringIO())
        self.assertTrue(DemoSelection.objects.filter(pk=fresh.pk).exists())

    def test_invalid_older_than_days_raises_readable_error_and_changes_nothing(self):
        stale = self._make_selection(slug="cleanup-stale-4")
        self._backdate(stale, 31)
        with self.assertRaises(CommandError):
            call_command("cleanup_demo_selections", "--older-than-days", "0", "--apply", stdout=StringIO())
        with self.assertRaises(CommandError):
            call_command("cleanup_demo_selections", "--older-than-days", "-5", "--apply", stdout=StringIO())
        self.assertTrue(DemoSelection.objects.filter(pk=stale.pk).exists())

    def test_output_never_contains_token_session_key_or_brand(self):
        stale = self._make_selection(slug="cleanup-stale-5", session_key="super-secret-session-key")
        self._backdate(stale, 31)
        out = StringIO()
        call_command("cleanup_demo_selections", stdout=out)
        content = out.getvalue()
        self.assertNotIn(str(stale.public_token), content)
        self.assertNotIn("super-secret-session-key", content)
        self.assertNotIn("برند فرضی مخفی", content)
        self.assertNotIn("Secret fictional brand", content)
        self.assertNotIn("public_token", content)
        self.assertNotIn("session_key", content)
