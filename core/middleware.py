from django.utils import translation


class AdminPersianLocaleMiddleware:
    """Keep the operational admin Persian regardless of the public-site language cookie."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin/"):
            translation.activate("fa")
            request.LANGUAGE_CODE = "fa"
        return self.get_response(request)
