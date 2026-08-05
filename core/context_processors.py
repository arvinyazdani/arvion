from django.conf import settings


def assessment_flags(request):
    return {"assessment_free_checkout": settings.ASSESSMENT_FREE_CHECKOUT}
