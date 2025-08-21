# blog/views/post_list.py
# لیست پست‌ها با جستجو و فیلتر برچسب — کلاسی
from django.views.generic import ListView
from django.db.models import Q
from blog.models import Post

class PostListView(ListView):
    """
    نمایش لیست پست‌ها با:
    - صفحه‌بندی
    - جستجو (q) در عنوان/خلاصه
    - فیلتر برچسب (tag)
    """
    template_name = "blog/list.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        qs = Post.objects.published()
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(title_fa__icontains=q) |
                Q(title_en__icontains=q) |
                Q(summary_fa__icontains=q) |
                Q(summary_en__icontains=q)
            )
        tag = self.request.GET.get("tag")
        if tag:
            qs = qs.filter(tags__name__iexact=tag)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lang = self.request.GET.get("lang", "fa")  # پیش‌فرض: فارسی
        context["lang"] = lang
        return context