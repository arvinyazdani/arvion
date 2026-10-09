from django import template
from blog.presentation import reading_minutes
from blog.covers import cover_alt as editorial_cover_alt

register = template.Library()

@register.filter
def cover_alt(post, language):
    return editorial_cover_alt(post, language)

@register.filter
def contains_persian(value):
    return any('\u0600' <= char <= '\u06ff' for char in str(value))


@register.filter
def read_minutes(post, language):
    source = post.body_as_html() if language == "fa" else post.body_as_html_en()
    return reading_minutes(source, language)
