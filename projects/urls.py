

from django.urls import path
from .views import projects as list_views
from .views import projects as detail_views

app_name = "projects"

urlpatterns = [
    path("", list_views.ProjectListView.as_view(), name="list"),
    path("<int:pk>/", detail_views.ProjectDetailView.as_view(), name="detail"),
]