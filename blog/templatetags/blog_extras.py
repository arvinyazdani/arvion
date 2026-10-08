from django import template
from blog.presentation import reading_minutes

register = template.Library()


@register.filter
def read_minutes(post, language):
    source = post.body_as_html() if language == "fa" else post.body_as_html_en()
    return reading_minutes(source, language)
