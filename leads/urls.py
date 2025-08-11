# leads/urls.py
from django.urls import path
from .views import LeadCreateView, LeadThanksView

app_name = "leads"
urlpatterns = [
    path("", LeadCreateView.as_view(), name="contact"),
    path("thanks/", LeadThanksView.as_view(), name="thanks"),
]