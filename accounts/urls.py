from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import AccountLoginView, AccountOrdersView, AccountPasswordResetCompleteView, AccountPasswordResetConfirmView, AccountPasswordResetDoneView, AccountPasswordResetView, AccountReceiptView, AccountResultsView, PhoneVerificationView, ProfileIdentityView, RegisterView, ResendVerificationView, dashboard, verification_sent, verify_email

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-phone/", PhoneVerificationView.as_view(), name="verify_phone"),
    path("login/", AccountLoginView.as_view(), name="login"),
    path("password/reset/", AccountPasswordResetView.as_view(), name="password_reset"),
    path("password/reset/sent/", AccountPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("password/reset/<uidb64>/<token>/", AccountPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("password/reset/complete/", AccountPasswordResetCompleteView.as_view(), name="password_reset_complete"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("verification-sent/", verification_sent, name="verification_sent"),
    path("verification/resend/", ResendVerificationView.as_view(), name="resend_verification"),
    path("verify/<uidb64>/<token>/", verify_email, name="verify"),
    path("dashboard/", dashboard, name="dashboard"),
    path("results/", AccountResultsView.as_view(), name="results_history"),
    path("orders/", AccountOrdersView.as_view(), name="orders_history"),
    path("orders/<uuid:pk>/receipt/", AccountReceiptView.as_view(), name="payment_receipt"),
    path("profile/identity/", ProfileIdentityView.as_view(), name="profile_identity"),
]
