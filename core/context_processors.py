from django.conf import settings
from django.db import OperationalError, ProgrammingError

from .models import CompanyProfile


def assessment_flags(request):
    try:
        company = CompanyProfile.objects.first()
    except (OperationalError, ProgrammingError):
        company = None
    return {
        "assessment_free_checkout": settings.ASSESSMENT_FREE_CHECKOUT,
        "company": company,
    }
