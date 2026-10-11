"""Local studio proposal: accessible destinations, shared identity and no new data flow."""
from django.test import TestCase, override_settings
from django.utils import translation
from core.models import CompanyProfile
from core.test_home import HomeStructureParser


@override_settings(RVION_STUDIO_3D_ENABLED=True)
class StudioHomeTests(TestCase):
    def setUp(self):
        translation.activate('fa')
        self.addCleanup(translation.deactivate_all)

    def test_four_stops_and_poster_are_in_initial_html(self):
        for lang in ('fa', 'en'):
            response = self.client.get(f'/{lang}/')
            for room in ('workshop', 'tests', 'library', 'reception'):
                self.assertContains(response, f'data-studio-room="{room}"', count=1)
            for stop in ('workshop', 'exam', 'library', 'reception'):
                self.assertContains(response, f'data-stop="{stop}"', count=1)
            self.assertContains(response, 'data-studio-poster', count=1)
            self.assertContains(response, '<canvas data-studio-canvas>', count=1)
            self.assertNotContains(response, 'rvion-entry-payload')
            self.assertContains(response, 'core/studio/tour.js')
            self.assertNotContains(response, '<script src="/static/core/studio/vendor/')
            self.assertNotContains(response, 'data-stop="showroom"')
            self.assertNotContains(response, 'id="choose-demo"')
            self.assertContains(response, 'data-assessment-film', count=1)
            self.assertContains(response, 'data-film-scene', count=4)
            self.assertContains(response, f'/{lang}/contact/?service=digital-product-consulting')

    def test_all_room_anchors_have_real_targets(self):
        import re
        html = self.client.get('/en/').content.decode()
        directory = html.split('class="hp-routes shell"', 1)[1].split('</nav>', 1)[0]
        for href in HomeStructureParser(directory).links:
            if href.startswith('#'):
                self.assertEqual(len(re.findall(r'id="' + re.escape(href[1:]) + '"', html)), 1)
            else:
                self.assertTrue(href.startswith('/en/contact/'))

    def test_workshop_has_only_the_customisation_action_in_both_modes_and_languages(self):
        for enabled in (False, True):
            with self.settings(RVION_STUDIO_3D_ENABLED=enabled):
                for lang in ('fa', 'en'):
                    html = self.client.get(f'/{lang}/').content.decode()
                    workshop = html.split('<section id="services"', 1)[1].split('</section>', 1)[0]
                    self.assertEqual(HomeStructureParser(workshop).links, [f'/{lang}/start/'])
                    self.assertNotIn('hp-service-links', workshop)

    @override_settings(RVION_STUDIO_3D_ENABLED=False)
    def test_unapproved_engine_does_not_ship_or_preload(self):
        response = self.client.get('/fa/')
        self.assertNotContains(response, 'data-studio-tour')
        self.assertNotContains(response, 'core/studio/')
        self.assertContains(response, 'id="home-title"', count=1)

    def test_empty_library_still_has_a_real_reading_destination(self):
        from blog.models import Post
        Post.objects.all().delete()
        html = self.client.get('/en/').content.decode()
        library = html.split('id="studio-library"', 1)[1].split('</section>', 1)[0]
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

    def test_library_uses_published_article_cover_and_current_language_only(self):
        from blog.models import Post
        from django.utils import timezone
        post = Post.objects.create(title_fa='راهنمای سفارش', title_en='Project guide',
            slug_fa='project-guide-fa', slug_en='project-guide-en', body_fa='متن', body_en='Text',
            hero_image='articles/real-cover.jpg', is_published=True, published_at=timezone.now())
        Post.objects.create(title_fa='پیش‌نویس خصوصی', slug_fa='private-draft', is_published=False)
        for lang in ('fa', 'en'):
            html = self.client.get(f'/{lang}/').content.decode()
            library = html.split('id="studio-library"', 1)[1].split('</section>', 1)[0]
            self.assertIn(post.hero_image.url, library)
            self.assertIn('loading="lazy"', library)
            self.assertIn(f'/{lang}/blog/project-guide-{lang}/', library)
            self.assertNotIn('private-draft', library)
            self.assertNotIn('studio_art', library)
            self.assertNotIn('core/studio/posters', library)

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
