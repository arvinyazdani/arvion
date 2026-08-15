from django.urls import path

from .views import CrmOrderCreateView, CrmOrderThanksView, specialist_discovery, specialist_done

app_name = "crm_orders"

urlpatterns = [
    path("", CrmOrderCreateView.as_view(), name="create"),
    path("thanks/<str:code>/", CrmOrderThanksView.as_view(), name="thanks"),
    path("specialist/<str:code>/done/", specialist_done, name="specialist_done"),
    path("specialist/<str:code>/", specialist_discovery, name="specialist"),
    path("specialist/<str:code>/<str:section>/", specialist_discovery, name="specialist_section"),
]
