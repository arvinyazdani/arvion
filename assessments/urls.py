from django.urls import path

from .views import CheckoutView, CreateOrderView, ExamDetailView, ExamListView, SandboxPayView

app_name = "assessments"

urlpatterns = [
    path("", ExamListView.as_view(), name="list"),
    path("order/<uuid:pk>/", CheckoutView.as_view(), name="checkout"),
    path("order/<uuid:pk>/sandbox-pay/", SandboxPayView.as_view(), name="sandbox_pay"),
    path("<slug:slug>/buy/", CreateOrderView.as_view(), name="create_order"),
    path("<slug:slug>/", ExamDetailView.as_view(), name="detail"),
]
