from django.urls import path

from .views import dashboard, staff_create, staff_edit, staff_list

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("staff/", staff_list, name="staff_list"),
    path("staff/new/", staff_create, name="staff_create"),
    path("staff/<int:user_id>/", staff_edit, name="staff_edit"),
]
