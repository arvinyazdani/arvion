"""The old entry/gateway is retired, without retiring shared loading or home routes."""
from pathlib import Path
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone, translation
from blog.models import Post


class HomeArrivalTests(TestCase):
    def setUp(self):
        translation.activate('fa')
        self.addCleanup(translation.deactivate_all)

    def test_home_arrival_and_reload_use_only_the_shared_loader_for_staff_and_visitors(self):
        user = get_user_model().objects.create_user(username='arrival@example.test', email='arrival@example.test', password='unused', is_staff=True)
        for staff in (False, True):
            if staff:
                self.client.force_login(user)
            for lang in ('fa', 'en'):
                html = self.client.get(f'/{lang}/?entry_seek=0').content.decode()
                self.assertEqual(html.count('data-navigation-loader'), 1)
                self.assertIn("data-arrival-loading", html)
                self.assertIn('rvion-code-glyph', html)
                for retired in ('rvion-entry', 'entry.css', 'js/entry.js', 'ar-gate'):
                    self.assertNotIn(retired, html)

    def test_other_pages_use_the_same_arrival_feedback_without_a_second_intro(self):
        html = self.client.get('/en/about/').content.decode()
        self.assertIn('data-navigation-loader', html)
        self.assertIn('rvion-code-glyph', html)
        self.assertIn('data-arrival-loading', html)
        self.assertIn('route-loader__progress', html)
        self.assertNotIn('welcome-orbit', html)

    def test_all_independent_shells_include_one_shared_arrival_bootstrap(self):
        root = Path(settings.BASE_DIR)
        for path in ('core/templates/core/base.html', 'core/templates/core/flow_base.html',
                     'contracts/templates/contracts/contract_base.html',
                     'management_portal/templates/management_portal/v2/base.html'):
            source = (root / path).read_text()
            self.assertEqual(source.count("include 'core/includes/arrival_loader.html'"), 1, path)
            self.assertEqual(source.count('core/_route_loader.html'), 1, path)
            self.assertIn('site-shell.js\' %}?v=18', source)

    def test_direct_manager_launch_uses_the_same_loader(self):
        user = get_user_model().objects.create_user(
            username='loader-manager@example.test', email='loader-manager@example.test',
            password='unused', is_staff=True, is_superuser=True)
        self.client.force_login(user)
        for lang in ('fa', 'en'):
            response = self.client.get(f'/{lang}/management/')
            self.assertEqual(response.status_code, 200)
            html = response.content.decode()
            self.assertEqual(html.count('data-navigation-loader'), 1)
            self.assertIn('data-arrival-loading', html)
            self.assertIn('route-loader__progress', html)
            self.assertNotIn('welcome-orbit', html)

    def test_article_and_order_links_still_exist_in_the_home_itself(self):
        Post.objects.create(title_fa='راهنمای سفارش', slug_fa='arrival-guide', body_fa='متن',
                            is_published=True, published_at=timezone.now())
        html = self.client.get('/fa/').content.decode()
        self.assertIn('href="/fa/blog/arrival-guide/"', html)
        self.assertIn('href="/fa/start/"', html)
        self.assertIn('/fa/assessments/english-placement-a1-c1/about/', html)

    def test_retired_assets_and_setting_are_not_left_as_dead_code(self):
        root = Path(settings.BASE_DIR)
        for path in ('core/templates/core/_entry_scene.html', 'core/templatetags/entry_ui.py',
                     'core/static/core/js/entry.js', 'core/static/core/css/entry.css'):
            self.assertFalse((root / path).exists())
        self.assertNotIn('RVION_ENTRY_ENABLED', (root / 'arvion/settings/base.py').read_text())
        shell = (root / 'core/static/core/js/site-shell.js').read_text()
        self.assertNotIn('rvion-entry', shell)
        self.assertNotIn('rvion:entry-closed', (root / 'core/static/core/studio/tour.js').read_text())
