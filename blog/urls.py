from django.urls import path
from blog.views.post_list import PostListView
from blog.views.post_detail import PostDetailView

app_name = "blog"

urlpatterns = [
    path('', PostListView.as_view(), name='list'),
    path('<slug:slug>/', PostDetailView.as_view(), name='detail'),
]