import logging

from django.test import RequestFactory, TestCase

from .logging_handlers import PersianSystemLogHandler
from .models import SystemLog


class SystemLogPrivacyTests(TestCase):
    def test_server_log_stores_route_pattern_not_contract_token(self):
        request = RequestFactory().get("/contract/private-customer-token/")
        record = logging.LogRecord(
            "django.request", logging.ERROR, __file__, 1,
            "Internal Server Error: /contract/private-customer-token/", (), None,
        )
        record.request = request

        PersianSystemLogHandler().emit(record)

        item = SystemLog.objects.get()
        self.assertEqual(item.path, "/contract/<str:token>/")
        self.assertNotIn("private-customer-token", item.path)
        self.assertNotIn("private-customer-token", item.detail)
        self.assertNotIn("private-customer-token", item.message_fa)
