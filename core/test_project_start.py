from django.test import TestCase
class ProjectStartTests(TestCase):
    def test_persian_start_page_offers_three_clear_paths(self):
        response = self.client.get("/fa/start/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "چه چیزی می‌خواهید بسازید؟")
        self.assertContains(response, "/fa/crm-order/")
        self.assertContains(response, "/fa/clinic-order/")
        self.assertContains(response, "/fa/contact/")
        self.assertEqual(response.content.decode().count('class="project-start-card'), 3)

    def test_english_start_page_is_not_mixed_with_persian_copy(self):
        response = self.client.get("/en/start/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("What would you like to build?", html)
        self.assertIn("/fa/crm-order/", html)
        self.assertIn("/fa/clinic-order/", html)
        self.assertNotIn("چه چیزی می‌خواهید بسازید؟", html)
