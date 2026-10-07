"""Public, model-backed schema and matching navigation; no session/PII reads."""
import json
from urllib.parse import urlsplit

from django import template
from django.templatetags.static import static
from django.urls import reverse
from django.utils.safestring import mark_safe

register = template.Library()

# The public route allow-list keeps customer/private contexts out of the graph.
LABELS = {
    'home': ('خانه', 'Home'),
    'about': ('درباره شرکت', 'About the company'),
    'company_info': ('اطلاعات حقوقی شرکت', 'Company information'),
    'crm_product': ('CRM سازمانی', 'Enterprise CRM'),
    'services:list': ('راهکارها', 'Solutions'),
    'projects:demo_gallery': ('نمونه‌ها', 'Samples'),
    'blog:list': ('دیدگاه‌ها', 'Insights'),
    'assessments:list': ('آزمون‌ها', 'Assessments'),
    'leads:contact': ('مشاوره و سفارش پروژه', 'Project enquiry'),
    'privacy': ('حریم خصوصی', 'Privacy policy'),
    'service_terms': ('شرایط خدمات', 'Service terms'),
    'refund_policy': ('لغو و بازپرداخت', 'Cancellation and refunds'),
    'crm_orders:create': ('نیازسنجی CRM', 'CRM discovery'),
    'clinic_orders:create': ('نیازسنجی کلینیک', 'Clinic discovery'),
    'assessments:terms': ('شرایط آزمون', 'Assessment terms'),
    'project_start': ('شروع پروژه', 'Start a project'),
}
DETAILS = {
    'services:detail': ('service', 'services:list'),
    'blog:detail': ('post', 'blog:list'),
    'projects:demo_preview': ('demo', 'projects:demo_gallery'),
    'assessments:briefing': ('exam', 'assessments:list'),
}


def _json_for_script(value):
    # JSON escaping, not escapejs (which can emit invalid JSON escapes).
    return mark_safe(json.dumps(value, ensure_ascii=False, separators=(',', ':')).replace('&', '\\u0026')
                     .replace('<', '\\u003c').replace('>', '\\u003e'))


@register.simple_tag(takes_context=True)
def seo_documents(context):
    request = context.get('request')
    match = getattr(request, 'resolver_match', None)
    route = getattr(match, 'view_name', '')
    if context.get('seo_noindex') or route not in LABELS and route not in DETAILS:
        return {}
    language = context.get('lang', 'fa')
    index = 0 if language == 'fa' else 1
    origin = context['site_url'].rstrip('/')
    canonical = context['canonical_url']
    brand = context['brand_name']
    org_id, site_id = origin + '/#organization', origin + '/#website'
    organization = {
        '@type': 'Organization', '@id': org_id, 'name': brand,
        'alternateName': 'Rvion', 'url': origin + '/',
        'logo': origin + static('core/icons/icon-512.png'),
        'areaServed': 'IR',
    }
    # No inferred legal/address values or social accounts when profile is absent.
    company = context.get('company')
    if company:
        for key, value in (
            ('legalName', getattr(company, 'legal_name_' + language)),
            ('telephone', company.phone), ('identifier', company.national_id),
        ):
            if value:
                organization[key] = value
        address = getattr(company, 'address_' + language)
        if address:
            organization['address'] = {'@type': 'PostalAddress', 'streetAddress': address,
                                       'addressCountry': 'IR'}
            if company.postal_code:
                organization['address']['postalCode'] = company.postal_code
    graph = [organization, {
        '@type': 'WebSite', '@id': site_id, 'name': brand,
        'url': origin + '/', 'inLanguage': language, 'publisher': {'@id': org_id},
    }]
    breadcrumbs = []
    if route in DETAILS:
        object_key, parent = DETAILS[route]
        obj = context.get(object_key)
        label = getattr(obj, 'title_' + language, '')
    else:
        label = LABELS[route][index]
        parent = None
    if route != 'home':
        breadcrumbs.append({'name': LABELS['home'][index], 'url': origin + reverse('home')})
        if parent:
            breadcrumbs.append({'name': LABELS[parent][index], 'url': origin + reverse(parent)})
        breadcrumbs.append({'name': label, 'url': canonical})
        graph.append({
            '@type': 'BreadcrumbList', '@id': canonical + '#breadcrumb',
            'itemListElement': [
                {'@type': 'ListItem', 'position': position, 'name': item['name'], 'item': item['url']}
                for position, item in enumerate(breadcrumbs, start=1)
            ],
        })
    page = {'@type': 'WebPage', '@id': canonical + '#webpage', 'url': canonical,
            'name': label, 'inLanguage': language, 'isPartOf': {'@id': site_id}}
    if breadcrumbs:
        page['breadcrumb'] = {'@id': canonical + '#breadcrumb'}
    graph.append(page)
    if route in {'services:detail', 'crm_product'}:
        graph.append({'@type': 'Service', '@id': canonical + '#service', 'name': label,
                      'serviceType': label, 'url': canonical, 'areaServed': 'IR',
                      'provider': {'@id': org_id}})
        page['mainEntity'] = {'@id': canonical + '#service'}
    if route == 'blog:detail':
        post = context['post']
        article = {'@type': 'BlogPosting', '@id': canonical + '#article',
                   'url': canonical, 'headline': label,
                   'description': getattr(post, 'summary_' + language) or '',
                   'inLanguage': language, 'publisher': {'@id': org_id},
                   'mainEntityOfPage': {'@id': page['@id']}}
        if post.published_at:
            article['datePublished'] = post.published_at.isoformat()
        graph.append(article)
        page['mainEntity'] = {'@id': article['@id']}
    for item in breadcrumbs:
        item['path'] = urlsplit(item['url']).path
    return {'json_ld': _json_for_script({'@context': 'https://schema.org', '@graph': graph}),
            'breadcrumbs': breadcrumbs}
