

from django.urls import path
from .views.projects import DemoConfigureView, DemoGalleryView, DemoPreviewView, ProjectDetailView, ProjectListView

app_name = "projects"

urlpatterns = [
    path("demos/", DemoGalleryView.as_view(), name="demo_gallery"),
    path("demos/<slug:slug>/", DemoPreviewView.as_view(), name="demo_preview"),
    path("demos/<slug:slug>/configure/", DemoConfigureView.as_view(), name="demo_configure"),
    path("", ProjectListView.as_view(), name="list"),
    path("<slug:slug>/", ProjectDetailView.as_view(), name="detail"),
]
