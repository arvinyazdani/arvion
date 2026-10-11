"""Local studio proposal: accessible destinations, shared identity and no new data flow."""
from django.test import TestCase
from django.utils import translation
from core.models import CompanyProfile
from core.test_home import HomeStructureParser


class StudioHomeTests(TestCase):
    def setUp(self):
        translation.activate('fa')
        self.addCleanup(translation.deactivate_all)

    def test_six_rooms_and_illustrations_are_in_initial_html(self):
        for lang in ('fa', 'en'):
            response = self.client.get(f'/{lang}/')
            for room in ('workshop', 'tests', 'library', 'gallery', 'control', 'reception'):
                self.assertContains(response, f'data-studio-room="{room}"', count=1)
                self.assertContains(response, f'data-studio-art="{room}"', count=1)
            self.assertContains(response, 'viewBox="0 0 820 500"', count=6)
            self.assertNotContains(response, '<canvas')
            self.assertNotContains(response, 'rvion-entry-payload')
            self.assertContains(response, 'core/js/studio-motion.js')

    def test_all_room_anchors_have_real_targets(self):
        import re
        html = self.client.get('/en/').content.decode()
        directory = html.split('class="hs-directory shell"', 1)[1].split('</nav>', 1)[0]
        for href in HomeStructureParser(directory).links:
            self.assertTrue(href.startswith('#'))
            self.assertEqual(len(re.findall(r'id="' + re.escape(href[1:]) + '"', html)), 1)

    def test_empty_library_still_has_a_real_reading_destination(self):
        from blog.models import Post
        Post.objects.all().delete()
        html = self.client.get('/en/').content.decode()
        library = html.split('id="studio-library"', 1)[1].split('data-studio-room="gallery"', 1)[0]
        self.assertIn('href="/en/blog/"', library)

    def test_footer_uses_actual_company_phone_and_no_empty_phone(self):
        company = CompanyProfile.objects.get()
        company.phone = '02112345678'
        company.save(update_fields=['phone'])
        html = self.client.get('/fa/').content.decode().split('<footer', 1)[1]
        self.assertIn('href="tel:02112345678"', html)
        self.assertNotIn('tel:+989333021100', html)
        CompanyProfile.objects.all().delete()
        html = self.client.get('/en/').content.decode().split('<footer', 1)[1]
        self.assertNotIn('href="tel:', html)
        self.assertNotIn('Registered company', html)

    def test_menu_and_footer_keep_localized_account_and_settings(self):
        for lang in ('fa', 'en'):
            html = self.client.get(f'/{lang}/').content.decode()
            nav = html.split('id="site-nav"', 1)[1].split('</nav>', 1)[0]
            self.assertIn('class="menu-project"', nav)
            self.assertIn('data-theme-toggle', nav)
            self.assertIn('data-sound-toggle="all"', nav)
            self.assertIn(f'href="/{lang}/account/login/"', nav)
            footer = html.split('<footer', 1)[1]
            self.assertEqual(footer.count('<h2>'), 4)
            self.assertIn('data-theme-toggle', footer)
            self.assertIn(f'href="/{lang}/account/login/"', footer)
