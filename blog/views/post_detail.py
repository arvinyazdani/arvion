# blog/views/post_detail.py
# جزئیات پست — کلاسی
from django.views.generic import DetailView
from django.shortcuts import get_object_or_404
from blog.models import Post

class PostDetailView(DetailView):
    """
    نمایش صفحه‌ی جزئیات یک پست با استفاده از slug ترجمه‌شده.
    """
    template_name = "blog/detail.html"
    context_object_name = "post"

    def get_object(self):
        slug = self.kwargs.get("slug")
        # فیلتر بر اساس شکست ترجمه و وضعیت انتشار
        return get_object_or_404(Post, translations__slug=slug, is_published=True)