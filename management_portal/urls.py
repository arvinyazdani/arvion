from django.urls import path

from .views import dashboard, notification_feed, notification_list, notification_status, request_detail, request_list, request_update, sms_send, staff_create, staff_edit, staff_list
from contracts.views import proposal_clauses, proposal_create, proposal_detail, proposal_list, proposal_publish

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("staff/", staff_list, name="staff_list"),
    path("staff/new/", staff_create, name="staff_create"),
    path("staff/<int:user_id>/", staff_edit, name="staff_edit"),
    path("notifications/", notification_list, name="notification_list"),
    path("notifications/feed/", notification_feed, name="notification_feed"),
    path("notifications/<int:notification_id>/<str:status>/", notification_status, name="notification_status"),
    path("sms/", sms_send, name="sms_send"),
    path("requests/", request_list, name="request_list"),
    path("requests/<str:kind>/<int:object_id>/", request_detail, name="request_detail"),
    path("requests/<str:kind>/<int:object_id>/update/", request_update, name="request_update"),
    path("contracts/", proposal_list, name="contract_list"),
    path("contracts/new/", proposal_create, name="contract_create"),
    path("contracts/<int:proposal_id>/", proposal_detail, name="contract_detail"),
    path("contracts/<int:proposal_id>/clauses/", proposal_clauses, name="contract_clauses"),
    path("contracts/<int:proposal_id>/publish/", proposal_publish, name="contract_publish"),
]
