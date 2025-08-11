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
                Q(translations__title__icontains=q) |
                Q(translations__summary__icontains=q)
            )
        tag = self.request.GET.get("tag")
        if tag:
            qs = qs.filter(tags__name__iexact=tag)
        return qs