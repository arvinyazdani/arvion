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

    def test_short_film_has_localized_narration_and_complete_readable_guide(self):
        for lang in ('fa', 'en'):
            html = self.client.get(f'/{lang}/').content.decode()
            film = html.split('data-assessment-film', 1)[1].split('</details>', 1)[0]
            self.assertIn(f'data-film-lang="{lang}"', film)
            self.assertIn('۹٫۶' if lang == 'fa' else '9.6', film)
            self.assertNotIn('00:36', film)
            self.assertIn('data-film-sound aria-pressed="false"', film)
            self.assertIn('data-film-replay hidden', film)
            self.assertNotIn('data-film-play', film)
            self.assertNotIn('data-film-chapter', film)
            self.assertEqual(film.count('data-film-scene'), 4)
            self.assertIn('class="af-transcript"', film)
            for text in (('گواهی غیررسمی', 'اثبات قطعی تقلب', 'دلیل آن') if lang == 'fa'
                         else ('unofficial', 'do not prove cheating', 'explanations')):
                self.assertIn(text, film)

    def test_cinematic_home_reuses_inline_styles_without_loading_legacy_hero_css(self):
        from pathlib import Path
        from django.conf import settings
        from core.templatetags.studio_ui import STYLES
        html = self.client.get('/fa/').content.decode()
        self.assertIn('<style data-studio-styles>', html)
        self.assertNotIn('href="/static/core/css/home-studio.css', html)
        self.assertNotIn('href="/static/core/studio/tour.css', html)
        for name in STYLES:
            app, relative = name.split('/', 1)
            self.assertIn((Path(settings.BASE_DIR) / app / 'static' / name).read_text(), html)
        self.assertIn('<style data-studio-shell-styles>', html)
        self.assertNotIn('href="/static/core/css/site.css', html)
        self.assertIn('url("/static/core/fonts/Vazirmatn-Regular.woff2")', html)
        self.assertNotIn('url("../fonts/', html)

    def test_generated_home_shell_is_tied_to_canonical_css_and_retains_menu_states(self):
        import hashlib
        from pathlib import Path
        from django.conf import settings
        root = Path(settings.BASE_DIR) / 'core/static/core/css'
        source = (root / 'site.css').read_bytes()
        generated = (root / 'home-shell.generated.css').read_text()
        self.assertIn(hashlib.sha256(source).hexdigest(), generated)
        self.assertIn(hashlib.sha256((Path(settings.BASE_DIR) / 'ops/build_home_shell_css.py').read_bytes()).hexdigest(), generated)
        self.assertLess(len(generated), len(source) // 3)
        for selector in ('.site-header', '.nav-wrap', '.site-nav.is-open',
                         '.menu-button', '.mobile-tabbar', '.install-sheet',
                         '.skip-link', '.button', '.ui-icon', '.eyebrow', '@media'):
            self.assertIn(selector, generated)
        self.assertNotIn('.question-stage', generated)

    def test_studio_font_subsets_are_current_and_keep_full_fonts_as_fallback(self):
        import hashlib
        import json
        from pathlib import Path
        from django.conf import settings
        root = Path(settings.BASE_DIR) / 'core/static/core/fonts'
        manifest = json.loads((root / 'studio/manifest.json').read_text())
        self.assertEqual(len(manifest), 3)
        for filename, hashes in manifest.items():
            self.assertEqual(hashlib.sha256((Path(settings.BASE_DIR) / 'ops/build_studio_fonts.py').read_bytes()).hexdigest(), hashes['builder'])
            self.assertEqual(hashlib.sha256((root / filename).read_bytes()).hexdigest(), hashes['source'])
            self.assertEqual(hashlib.sha256((root / 'studio' / filename).read_bytes()).hexdigest(), hashes['subset'])
            self.assertLess((root / 'studio' / filename).stat().st_size, (root / filename).stat().st_size)
        html = self.client.get('/fa/').content.decode()
        self.assertIn('unicode-range:U+0000-00FF,U+0600-06FF,U+2000-206F,U+FB50-FEFF', html)
        import re
        faces = re.findall(r'@font-face\{font-family:Vazirmatn;[^}]+\}', html)
        self.assertEqual(len(faces), 6)
        self.assertTrue(all('unicode-range:' in face for face in faces))
        self.assertIn('U+0100', html)  # Extended Latin still uses the original face.
        self.assertIn('url("/static/core/fonts/Vazirmatn-Regular.woff2")', html)
        self.assertIn('href="/static/core/fonts/studio/Vazirmatn-Regular.woff2"', html)
        self.assertEqual(html.count('fetchpriority="low"'), 3)
        with self.settings(RVION_STUDIO_3D_ENABLED=False):
            self.assertNotContains(self.client.get('/fa/'), 'fonts/studio/')

    def test_avif_posters_preserve_webp_fallback_and_asset_dimensions(self):
        from pathlib import Path
        import struct
        from PIL import Image
        from django.conf import settings
        root = Path(settings.BASE_DIR) / 'core/static/core/studio/posters'
        for room in ('workshop', 'exam', 'library', 'reception'):
            for device in ('mobile', 'desktop'):
                avif = root / f'{room}-{device}.avif'
                webp = root / f'{room}-{device}.webp'
                self.assertLess(avif.stat().st_size, webp.stat().st_size)
                with Image.open(webp) as image:
                    # Read the ISO-BMFF image spatial-extents property without
                    # adding an AVIF decoder to application dependencies.
                    data = avif.read_bytes()
                    extents = data.index(b'ispe') + 8
                    size = struct.unpack('>II', data[extents:extents + 8])
                    self.assertEqual(size, (675, 1200) if device == 'mobile' else image.size)
                    self.assertEqual(size[0] * image.height, size[1] * image.width)
        response = self.client.get('/fa/')
        self.assertContains(response, 'type="image/avif"', count=4)
        self.assertContains(response, 'data-studio-mobile')
        self.assertContains(response, 'workshop-mobile.webp')
        self.assertContains(response, 'workshop-mobile.avif')

    def test_production_static_resolution_never_requests_a_manifest_directory(self):
        from unittest.mock import patch
        def strict_url(name):
            self.assertFalse(name.endswith('/'), 'A directory is not a manifest asset')
            return '/static/' + name
        with patch('django.contrib.staticfiles.storage.staticfiles_storage.url', side_effect=strict_url):
            response = self.client.get('/fa/')
        self.assertContains(response, 'data-assets="/static/core/studio/"')
        self.assertContains(response, 'data-font-bold="/static/core/fonts/studio/Vazirmatn-Bold.woff2"')

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

    def test_footer_groups_localized_call_button_with_project_action(self):
        company = CompanyProfile.objects.get()
        company.phone = '02112345678'
        company.save(update_fields=['phone'])
        for lang, label in (('fa', 'تماس با ما'), ('en', 'Call us')):
            with self.subTest(lang=lang):
                html = self.client.get(f'/{lang}/').content.decode().split('<footer', 1)[1]
                actions = html.split('<div class="footer-actions">', 1)[1].split('</div>', 1)[0]
                self.assertEqual(actions.count('<a '), 2)
                self.assertIn(f'href="/{lang}/start/"', actions)
                self.assertIn('class="footer-phone" href="tel:02112345678"', actions)
                self.assertIn('#contact', actions)
                self.assertIn('aria-hidden="true"', actions)
                self.assertIn(label, actions)
                self.assertIn('<bdi dir="ltr">', actions)

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
