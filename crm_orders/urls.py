from django.urls import path

from .views import CrmOrderCreateView, CrmOrderThanksView

app_name = "crm_orders"

urlpatterns = [
    path("", CrmOrderCreateView.as_view(), name="create"),
    path("thanks/<str:code>/", CrmOrderThanksView.as_view(), name="thanks"),
]
