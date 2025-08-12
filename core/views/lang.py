

from django.views.generic import View
from django.utils.translation import activate

class LanguageViewMixin(View):
    """
    میکسین مدیریت زبان برای ویوها

    این میکسین وظیفه دارد زبان فعلی سایت را بر اساس اولویت‌های زیر تعیین کند:
      1. بررسی پارامتر GET به نام lang (مثلاً ?lang=fa یا ?lang=en)
      2. اگر نبود، استفاده از مقدار ذخیره شده در سشن کاربر
      3. اگر هیچ‌کدام نبود، استفاده از زبان پیش‌فرض (fa)

    همچنین زبان انتخاب شده را در سشن ذخیره می‌کند تا درخواست‌های بعدی
    هم به همان زبان باشند.

    این میکسین مقدار `lang` را به قالب پاس می‌دهد تا بتوان از آن
    برای شرط‌گذاری در نمایش محتوای چندزبانه استفاده کرد.
    """

    default_lang = 'fa'  # زبان پیش‌فرض سایت

    def dispatch(self, request, *args, **kwargs):
        """
        متد dispatch قبل از هر متد دیگری اجرا می‌شود
        و زبان را تشخیص داده و فعال می‌کند.
        """
        # 1) گرفتن زبان از GET
        lang = request.GET.get('lang')

        # 2) اگر نبود از سشن
        if not lang:
            lang = request.session.get('lang')

        # 3) اگر باز هم نبود، زبان پیش‌فرض
        if not lang:
            lang = self.default_lang

        # اطمینان از اینکه فقط fa یا en داریم
        lang = lang.lower()
        if lang not in ('fa', 'en'):
            lang = self.default_lang

        # ذخیره در سشن
        request.session['lang'] = lang

        # فعال‌سازی زبان (برای ترجمه‌های django)
        activate(lang)

        # ذخیره در شیء ویو
        self.lang = lang

        # ادامه پردازش ویو
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        پاس دادن مقدار زبان به قالب
        """
        context = super().get_context_data(**kwargs)
        context['lang'] = self.lang
        return context