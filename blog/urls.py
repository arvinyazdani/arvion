from django.urls import path, re_path
from blog.views.post_list import PostListView
from blog.views.post_detail import PostDetailView

app_name = "blog"

urlpatterns = [
    path('', PostListView.as_view(), name='list'),
    re_path(r'^(?P<slug>[-\w\u0600-\u06FF]+)/$', PostDetailView.as_view(), name='detail'),
]
