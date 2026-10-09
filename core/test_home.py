"""Homepage clarity contracts: real catalogue, truthful identity and direct paths."""
from html.parser import HTMLParser

from django.test import TestCase
from django.utils import translation

from core.models import CompanyProfile
from core.tests_seo_contract import HeadParser
from projects.models import DemoTemplate
from services.models import Service


class HomeStructureParser(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.headings = []
        self.links = []
        self.heading = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('h1', 'h2'):
            self.heading = [tag, '']
        if tag == 'a':
            self.links.append(attrs.get('href'))

    def handle_data(self, data):
        if self.heading:
            self.heading[1] += data

    def handle_endtag(self, tag):
        if self.heading and self.heading[0] == tag:
            self.headings.append(tuple(self.heading))
            self.heading = None


class HomeClarityTests(TestCase):
    def setUp(self):
        translation.activate('fa')
        self.addCleanup(translation.deactivate_all)

    def test_approved_hero_and_unique_headings_in_both_languages(self):
        for lang, title in (
            ('fa', 'طراحی سایت، فروشگاه و CRM اختصاصی برای کسب‌وکار شما'),
            ('en', 'Custom websites, online stores and CRM for your business'),
        ):
            response = self.client.get(f'/{lang}/')
            parsed = HomeStructureParser(response.content.decode())
            self.assertEqual([text for tag, text in parsed.headings if tag == 'h1'], [title])
            sections = [text for tag, text in parsed.headings if tag == 'h2']
            self.assertEqual(len(sections), len(set(sections)))
            self.assertNotContains(response, 'data-home-journey')
            self.assertNotContains(response, 'class="home-paths')

    def test_six_service_cards_use_database_copy_and_requested_order(self):
        response = self.client.get('/fa/')
        cards = response.context['home_services']
        self.assertEqual([card['slug'] for card in cards], [
            'corporate-website-design', 'ecommerce-platform', 'custom-web-application',
            'crm', 'digital-product-consulting', 'maintenance-and-growth',
        ])
        for service in Service.objects.filter(is_active=True):
            card = next(card for card in cards if card['slug'] == service.slug)
            self.assertEqual(card['title'], service.title_fa)
            self.assertEqual(card['summary'], service.short_description_fa)
            self.assertEqual(card['url'], service.get_absolute_url())

    def test_catalogue_edits_and_inactive_rows_are_respected(self):
        service = Service.objects.get(slug='corporate-website-design')
        service.title_en = 'Edited catalogue title'
        service.short_description_en = 'Edited catalogue summary'
        service.save()
        response = self.client.get('/en/')
        self.assertContains(response, 'Edited catalogue title')
        self.assertContains(response, 'Edited catalogue summary')
        service.is_active = False
        service.save()
        self.assertNotContains(self.client.get('/en/'), 'Edited catalogue title')

    def test_renamed_slugs_fall_back_to_catalogue_order(self):
        for service in Service.objects.order_by('display_order', 'pk'):
            service.slug = f'renamed-{service.pk}'
            service.save(update_fields=['slug'])
        cards = self.client.get('/en/').context['home_services']
        self.assertEqual([card['slug'] for card in cards if card['slug'] != 'crm'],
                         list(Service.objects.filter(is_active=True).values_list('slug', flat=True)))

    def test_three_samples_and_real_category_links(self):
        response = self.client.get('/fa/')
        self.assertEqual(len(response.context['featured_demos']), 3)
        self.assertContains(response, 'نمونه تعاملی، نه پروژه مشتری')
        self.assertContains(response, 'پروژه‌های واقعی مشتریان نیستند')
        self.assertEqual(len(response.context['home_demo_categories']), 7)

    def test_empty_catalogue_still_has_safe_contact_and_crm_paths(self):
        Service.objects.update(is_active=False)
        DemoTemplate.objects.update(is_active=False)
        response = self.client.get('/en/')
        self.assertEqual(len(response.context['home_services']), 1)
        self.assertContains(response, 'Samples are being prepared')
        self.assertContains(response, 'href="/en/contact/"')
        self.assertContains(response, 'href="/en/crm/"')

    def test_public_identity_is_database_driven_and_not_fabricated(self):
        company = CompanyProfile.objects.get()
        for lang in ('fa', 'en'):
            response = self.client.get(f'/{lang}/')
            self.assertContains(response, getattr(company, f'legal_name_{lang}'))
            self.assertContains(response, getattr(company, f'address_{lang}'))
            self.assertContains(response, getattr(company, f'support_hours_{lang}'))
            self.assertContains(response, f'href="tel:{company.phone}"')
        CompanyProfile.objects.all().delete()
        response = self.client.get('/en/')
        self.assertNotContains(response, 'id="identity-title"')
        self.assertContains(response, 'href="/en/company/"')

    def test_main_required_targets_are_direct_and_available(self):
        from assessments.models import Exam
        for slug in ('english-placement-a1-c1', 'python-django-professional'):
            Exam.objects.get_or_create(slug=slug, defaults={
                'title_fa': 'آزمون آزمایشی', 'title_en': 'Fixture exam', 'is_active': True})
        for lang in ('fa', 'en'):
            response = self.client.get(f'/{lang}/')
            links = HomeStructureParser(response.content.decode()).links
            paths = ['crm/', 'projects/demos/', 'contact/', 'company/', 'blog/',
                     'assessments/english-placement-a1-c1/about/',
                     'assessments/python-django-professional/about/']
            paths += [f'services/{slug}/' for slug in Service.objects.filter(
                is_active=True).values_list('slug', flat=True)]
            for path in paths:
                url = f'/{lang}/{path}'
                self.assertIn(url, links)
                target = self.client.get(url, follow=False)
                self.assertEqual(target.status_code, 200, url)
                self.assertNotIn('Location', target.headers, url)

    def test_existing_home_metadata_and_schema_contract_are_preserved(self):
        expected = {
            'fa': ('طراحی و سفارش وب‌سایت اختصاصی | آرویون', 'نمونه سایت متناسب با کسب‌وکارتان را ببینید، زنده شخصی‌سازی کنید و با انتخاب‌های خودتان درخواست ساخت سایت بدهید.'),
            'en': ('Website design & development | Rvion', 'Explore website samples for your business, customise them live and start a project with your own choices.'),
        }
        for lang, (title, description) in expected.items():
            head = HeadParser(self.client.get(f'/{lang}/').content.decode())
            self.assertEqual(head.title, title)
            self.assertEqual(head.meta['description'], description)
            self.assertEqual([node['@type'] for node in head.json_ld[0]['@graph']],
                             ['Organization', 'WebSite', 'WebPage'])

    def test_header_destinations_and_persistent_action_preserve_shell(self):
        for lang in ('fa', 'en'):
            response = self.client.get(f'/{lang}/')
            html = response.content.decode()
            navigation = html.split('<div class="nav-primary">', 1)[1].split('</div>', 1)[0]
            self.assertEqual(HomeStructureParser(navigation).links, [
                f'/{lang}/services/', f'/{lang}/projects/demos/', f'/{lang}/crm/',
                f'/{lang}/assessments/', f'/{lang}/blog/', f'/{lang}/contact/',
            ])
            self.assertEqual(html.count('class="nav-cta"'), 1)
            self.assertLess(html.index('</nav>'), html.index('class="nav-cta"'))
            self.assertContains(response, 'core/js/welcome-sound.js')
            self.assertContains(response, 'data-install-dialog')
            tabs = html.split('<nav class="mobile-tabbar"', 1)[1].split('</nav>', 1)[0]
            self.assertEqual(tabs.count('<a '), 5)

    def test_english_main_and_removed_home_runtime(self):
        html = self.client.get('/en/').content.decode()
        main = html.split('<main id="main"', 1)[1].split('</main>', 1)[0]
        self.assertNotRegex(main, r'[\u0600-\u06ff]')
        self.assertNotIn('core/js/home-studio.js', html)
        self.assertNotIn('RVION / WORKFLOW', main)
        self.assertNotIn('RVION / ASSESSMENT', main)
