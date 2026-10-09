from django.test import TestCase
class ProjectStartTests(TestCase):
    def test_persian_start_page_offers_nine_topics(self):
        response = self.client.get("/fa/start/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "چه چیزی می‌خواهید بسازید؟")
        self.assertContains(response, "/fa/start/?type=crm")
        self.assertContains(response, "/fa/start/?type=clinic")
        self.assertContains(response, "/fa/start/?type=other")
        self.assertEqual(response.content.decode().count('class="project-start-card'), 9)

    def test_english_start_page_is_not_mixed_with_persian_copy(self):
        response = self.client.get("/en/start/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("What would you like to build?", html)
        self.assertIn("/en/start/?type=crm", html)
        self.assertIn("/en/start/?type=clinic", html)
        self.assertIn("The specialist form is currently in Persian.", html)
        self.assertNotIn("چه چیزی می‌خواهید بسازید؟", html)
