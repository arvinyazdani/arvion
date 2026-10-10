from django import template
from assessments.catalogue import public_exam_catalogue

register = template.Library()


@register.simple_tag(takes_context=True)
def path_intro_data(context):
    request = context.get("request")
    if not request or request.GET.get("from") != "entry":
        return None
    match = request.resolver_match
    if not match:
        return None
    project = match.view_name == "project_start"
    if not project and match.view_name != "assessments:list":
        return None
    lang = context.get("lang", "fa")
    return {"kind": "project" if project else "exam", "lang": lang,
            "exams": [] if project else public_exam_catalogue(lang)}
