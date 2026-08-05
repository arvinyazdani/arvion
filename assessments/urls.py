from django.urls import path

from .views import AudioPlayView, AttemptView, CertificateVerifyView, CertificateView, CheckoutView, CreateOrderView, ExamDetailView, ExamListView, FinishAttemptView, IntegrityEventView, ResultView, SandboxPayView, SaveAnswerView, StartAttemptView

app_name = "assessments"

urlpatterns = [
    path("", ExamListView.as_view(), name="list"),
    path("order/<uuid:pk>/", CheckoutView.as_view(), name="checkout"),
    path("order/<uuid:pk>/sandbox-pay/", SandboxPayView.as_view(), name="sandbox_pay"),
    path("entitlement/<int:pk>/start/", StartAttemptView.as_view(), name="start_attempt"),
    path("attempt/<uuid:pk>/", AttemptView.as_view(), name="attempt"),
    path("attempt/<uuid:pk>/answer/<int:item_pk>/", SaveAnswerView.as_view(), name="save_answer"),
    path("attempt/<uuid:pk>/audio/<int:item_pk>/play/", AudioPlayView.as_view(), name="audio_play"),
    path("attempt/<uuid:pk>/integrity/", IntegrityEventView.as_view(), name="integrity_event"),
    path("attempt/<uuid:pk>/finish/", FinishAttemptView.as_view(), name="finish_attempt"),
    path("result/<int:pk>/", ResultView.as_view(), name="result"),
    path("verify/", CertificateVerifyView.as_view(), name="verify_certificate"),
    path("certificate/<str:code>/", CertificateView.as_view(), name="certificate"),
    path("<slug:slug>/buy/", CreateOrderView.as_view(), name="create_order"),
    path("<slug:slug>/", ExamDetailView.as_view(), name="detail"),
]
