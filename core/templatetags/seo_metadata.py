"""Bounded, render-only metadata composition for demo previews and briefings."""
import re

from django import template
from django.utils.html import strip_tags

register = template.Library()


def _part(value):
    # A source sentence owns its content, not the separator between parts.
    return ' '.join(strip_tags(str(value)).split()).rstrip(' .؛;:،,!؟?…')


def _title(candidates, brand):
    titles = [f'{_part(candidate)} | {_part(brand)}' for candidate in candidates]
    return next((value for value in titles if len(value) <= 60), titles[-1])


def _description(candidates):
    # Choose complete existing parts, never truncate a word/sentence to fit.
    return next((value for value in candidates if 90 <= len(value) <= 155), candidates[-1])


@register.simple_tag
def demo_metadata(demo, lang, brand):
    fa = lang == 'fa'
    name = _part(demo.title_fa if fa else demo.title_en)
    tagline = _part(demo.tagline_fa if fa else demo.tagline_en)
    category = _part(demo.category_label)
    if fa:
        category = re.sub(r'^وب[\s\u200c-]?سایت\s+', '', category)
        short = {'restaurant': 'رستوران', 'jewelry': 'طلافروشی',
                 'ecommerce': 'فروشگاه', 'education': 'آموزش'}.get(demo.category, category)
        titles = [f'طراحی سایت {category} با نمونه زنده {name}',
                  f'طراحی سایت {category}: {name}', f'طراحی سایت {short}: {name}', name]
        action = 'نمونه را شخصی‌سازی کنید و درخواست طراحی بفرستید.'
        descriptions = [f'{name}؛ {tagline}. {action}',
                        f'{name}؛ {_part(demo.fit_label)}. {action}']
    else:
        category = re.sub(r'\s+website$', '', category, flags=re.I)
        short = {'restaurant': 'Restaurant', 'jewelry': 'Jewellery',
                 'ecommerce': 'Store', 'education': 'Education'}.get(demo.category, category)
        titles = [f'{category} website design: live {name} sample',
                  f'{category} website design: {name}', f'{short} website design: {name}', name]
        action = 'Customise this sample and send a design enquiry.'
        descriptions = [f'{name}: {tagline}. {action}',
                        f'{name}: {_part(demo.fit_label)}. {action}']
    return {'title': _title(titles, brand), 'description': _description(descriptions)}


@register.simple_tag
def briefing_metadata(exam, lang, brand):
    fa = lang == 'fa'
    name = _part(exam.title_fa if fa else exam.title_en)
    description = _part(exam.description_fa if fa else exam.description_en)
    if fa:
        titles = [f'پیش از شروع {name}', f'راهنمای {name}', name]
        # The shorter existing briefing topic, expressed as a complete instruction.
        guide = 'پیش از شروع با پایش آزمون و بررسی پاسخ‌ها آشنا شوید.'
        descriptions = [f'راهنمای {name}: {description}. {guide}',
                        f'راهنمای {name}. {guide}']
    else:
        titles = [f'Before you start {name}', f'Guide to {name}', name]
        guide = 'Learn about integrity monitoring and answer review before starting.'
        descriptions = [f'Guide to {name}: {description}. {guide}',
                        f'Guide to {name}. {guide}']
    return {'title': _title(titles, brand), 'description': _description(descriptions)}
