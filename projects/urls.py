

from django.urls import path
from .views.projects import DemoConfigureView, DemoFullView, DemoGalleryView, DemoPreviewView, KimiaMedicalCrmView, ProjectDetailView, ProjectListView

app_name = "projects"

urlpatterns = [
    path("demos/", DemoGalleryView.as_view(), name="demo_gallery"),
    path("demos/kimia-medical-crm/", KimiaMedicalCrmView.as_view(), name="kimia_medical_crm"),
    path("demos/<slug:slug>/", DemoPreviewView.as_view(), name="demo_preview"),
    path("demos/<slug:slug>/full/", DemoFullView.as_view(), name="demo_full"),
    path("demos/<slug:slug>/configure/", DemoConfigureView.as_view(), name="demo_configure"),
    path("", ProjectListView.as_view(), name="list"),
    path("<slug:slug>/", ProjectDetailView.as_view(), name="detail"),
]
