from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from .models import ManagementNotification, NotificationReceipt
from .notifications import process_notifications


User = get_user_model()


class UrgentNotificationPolicyTests(TestCase):
    @override_settings(MANAGEMENT_ALERT_SMS_RECIPIENTS=["989120373271"])
    @patch("management_portal.notifications.send_sms")
    def test_account_alert_does_not_send_immediate_sms(self, mocked_sms):
        manager = User.objects.create_superuser(
            username="account-manager", email="account-manager@example.com",
            password="safe-password",
        )
        notification = ManagementNotification.objects.create(
            category="accounts",
            title="تأیید تلفنی شماره موبایل لازم است",
            description="customer@example.com",
            target_url="/fa/management/approvals/",
            source_key="alert:account:phone-check",
        )
        NotificationReceipt.objects.create(user=manager, notification=notification)

        result = process_notifications()

        self.assertEqual(result["push"], 0)
        self.assertEqual(result["sms"], 0)
        mocked_sms.assert_not_called()

    @override_settings(
        WEB_PUSH_VAPID_PRIVATE_KEY="test-key",
        MANAGEMENT_ALERT_SMS_RECIPIENTS=["989120373271"],
    )
    @patch("management_portal.notifications.send_sms")
    @patch("management_portal.notifications._send_user_push", return_value="")
    def test_seen_urgent_alert_does_not_send_redundant_sms(self, mocked_push, mocked_sms):
        manager = User.objects.create_superuser(
            username="seen-payment-manager",
            email="seen-payment@example.com",
            password="safe-password",
        )
        notification = ManagementNotification.objects.create(
            category="payments",
            title="رسید جدید",
            description="REF-SEEN",
            target_url="/fa/management/approvals/",
            source_key="alert:payment:seen",
        )
        NotificationReceipt.objects.create(
            user=manager,
            notification=notification,
            seen_at=timezone.now(),
            push_sent_at=timezone.now(),
        )

        result = process_notifications()

        self.assertEqual(result["sms"], 0)
        mocked_sms.assert_not_called()
        mocked_push.assert_not_called()
