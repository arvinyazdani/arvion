from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import AccountLoginView, ProfileIdentityView, RegisterView, ResendVerificationView, dashboard, verification_sent, verify_email

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", AccountLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("verification-sent/", verification_sent, name="verification_sent"),
    path("verification/resend/", ResendVerificationView.as_view(), name="resend_verification"),
    path("verify/<uidb64>/<token>/", verify_email, name="verify"),
    path("dashboard/", dashboard, name="dashboard"),
    path("profile/identity/", ProfileIdentityView.as_view(), name="profile_identity"),
]
