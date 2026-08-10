from django.urls import path
from .views import ClinicOrderCreateView, ClinicOrderThanksView

app_name = "clinic_orders"
urlpatterns = [
    path("", ClinicOrderCreateView.as_view(), name="create"),
    path("thanks/<str:code>/", ClinicOrderThanksView.as_view(), name="thanks"),
]
