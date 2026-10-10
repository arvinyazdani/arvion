from django.test import TestCase
from assessments.models import Exam, ExamVersion, ExamSection


class PathIntroTests(TestCase):
    def test_intro_assets_only_on_explicit_entry_visit_to_two_destinations(self):
        for lang in ("fa", "en"):
            for path in ("start", "assessments"):
                self.assertNotContains(self.client.get(f"/{lang}/{path}/"), 'os-path-data')
                response = self.client.get(f"/{lang}/{path}/?from=entry")
                self.assertContains(response, 'os-path-data')
                self.assertContains(response, 'path-intro.js')
            self.assertNotContains(self.client.get(f"/{lang}/about/?from=entry"), 'os-path-data')

    def test_exam_intro_uses_published_database_facts_only(self):
        from assessments.catalogue import public_exam_catalogue
        exam, _ = Exam.objects.update_or_create(slug="english-placement-a1-c1", defaults={"title_fa": "آزمون", "title_en": "Assessment", "question_count": 37, "duration_minutes": 49, "is_active": True})
        version = ExamVersion.objects.create(exam=exam, version=99, is_published=True)
        ExamSection.objects.create(version=version, code="test", title_fa="بخش آزمایش", title_en="Test section", question_count=37)
        row = next(r for r in public_exam_catalogue("en") if r["slug"] == exam.slug)
        self.assertEqual((row["questions"], row["minutes"]), (37, 49))
        self.assertEqual(row["sections"], [{"title": "Test section", "count": 37}])
        self.assertEqual(row["bank_count"], 0)
        self.assertNotIn("prompt", str(row))
        self.assertNotIn("answer", str(row))
        self.assertContains(self.client.get("/en/assessments/?from=entry"), 'Test section')
