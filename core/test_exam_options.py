from django.test import TestCase
from django.utils import translation
from assessments.models import Exam, ExamVersion, ExamSection
from assessments.catalogue import PUBLIC_EXAM_SLUGS, public_exam_catalogue


class ExamOptionsTests(TestCase):
    def setUp(self):
        translation.activate("fa")
        self.addCleanup(translation.deactivate_all)
        Exam.objects.filter(slug__in=PUBLIC_EXAM_SLUGS).update(is_active=False)
        self.exam, _ = Exam.objects.update_or_create(slug=PUBLIC_EXAM_SLUGS[0], defaults={"title_fa": "سنجش مدرسان", "title_en": "Teacher assessment", "description_fa": "مهارت زبان", "description_en": "Language skills", "question_count": 41, "duration_minutes": 63, "is_active": True, "language_mode": "en"})
        version = ExamVersion.objects.create(exam=self.exam, version=105, is_published=True)
        ExamSection.objects.create(version=version, code="skills", title_fa="مهارت", title_en="Skills", question_count=41)

    def test_only_official_active_choices_and_real_facts_are_shown(self):
        Exam.objects.create(slug="unlisted-private-test", title_fa="آزمون پنهان", title_en="Unlisted private test", is_active=True)
        response = self.client.get("/en/assessments/")
        self.assertContains(response, 'value="english-placement-a1-c1"')
        self.assertNotContains(response, 'value="python-django-professional"')
        self.assertNotContains(response, "Unlisted private test")
        self.assertContains(response, '<b>41</b>', html=True)
        self.assertContains(response, '<b>63</b>', html=True)
        self.assertContains(response, "Skills")
        self.assertContains(response, "Advanced screening")
        self.assertNotContains(response, "50 randomized")
        self.assertNotContains(response, "مهارت")

    def test_no_js_selection_goes_to_briefing_not_pricing_or_list_loop(self):
        response = self.client.get("/en/assessments/", {"exam": self.exam.slug})
        self.assertEqual(response.url, "/en/assessments/english-placement-a1-c1/about/")
        self.assertEqual(self.client.get(response.url).status_code, 200)

    def test_unknown_external_inactive_slugs_never_redirect(self):
        for slug in ("https://foreign/", "unlisted-private-test", PUBLIC_EXAM_SLUGS[1]):
            self.assertEqual(self.client.get("/fa/assessments/", {"exam": slug}).status_code, 200)

    def test_empty_catalogue_has_recovery_not_dead_submit(self):
        self.exam.is_active = False
        self.exam.save(update_fields=["is_active"])
        response = self.client.get("/en/assessments/")
        self.assertContains(response, "No assessment is currently available")
        self.assertNotContains(response, 'type="submit"')

    def test_catalogue_localized_urls_and_no_question_content_with_constant_queries(self):
        with self.assertNumQueries(3):
            rows = public_exam_catalogue("en")
        self.assertTrue(rows[0]["url"].startswith("/en/"))
        self.assertEqual(set(rows[0]["sections"][0]), {"title", "count"})
        self.assertFalse(any(key in str(rows) for key in ("prompt_fa", "prompt_en", "correct_choice", "session_key", "explanation_en")))
