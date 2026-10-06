"""Stage 1 shell regression tests; no payment or assessment mutations."""
from html.parser import HTMLParser

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import translation

from accounts.models import User


class BottomParentParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.bottom_parent = None

    def handle_starttag(self, tag, attrs):
        if tag == "nav" and "m-bottom" in dict(attrs).get("class", "").split():
            self.bottom_parent = self.stack[-1] if self.stack else None
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.stack:
            del self.stack[len(self.stack) - 1 - self.stack[::-1].index(tag):]


class ManagementNavigationTests(TestCase):
    def setUp(self):
        translation.activate("fa")
        self.addCleanup(translation.deactivate_all)
        self.root = User.objects.create_superuser(
            username="navigation-root", email="navigation-root@example.test", password="test-only-password",
        )

    def staff(self, *permissions):
        user = User.objects.create_user(
            username="navigation-staff", email="navigation-staff@example.test",
            password="test-only-password", is_staff=True,
        )
        for app, codename in permissions:
            user.user_permissions.add(Permission.objects.get(content_type__app_label=app, codename=codename))
        self.client.force_login(user)
        return user

    def test_root_has_distinct_destinations_and_five_mobile_items(self):
        self.client.force_login(self.root)
        response = self.client.get("/fa/management/")
        desktop = response.context["management_primary_nav"]
        mobile = response.context["management_mobile_nav"]
        self.assertEqual(len(desktop), 6)
        self.assertEqual(len(mobile), 4)  # Plus the More trigger.
        self.assertEqual([item["label"] for item in mobile], ["امروز", "مشتریان", "آزمون‌ها", "پرداخت‌ها"])
        self.assertContains(response, "سفارش و قرارداد")
        self.assertNotContains(response, "فرم‌ها و آزمون‌ها")
        self.assertNotContains(response, "آماده‌سازی و ارسال")
        parser = BottomParentParser()
        parser.feed(response.content.decode())
        self.assertEqual(parser.bottom_parent, "body")

    def test_payment_role_gets_approval_shortcut_not_exam_or_enquiry(self):
        self.staff(("assessments", "view_manualpaymentsubmission"))
        response = self.client.get("/fa/management/")
        labels = [item["label"] for item in response.context["management_primary_nav"]]
        self.assertIn("پرداخت و تأیید", labels)
        self.assertNotIn("آزمون‌ها", labels)
        self.assertNotIn("درخواست و نیازسنجی", labels)
        self.assertEqual(self.client.get("/fa/management/approvals/").status_code, 200)
        self.assertEqual(self.client.get("/fa/management/assessment-support/").status_code, 403)
        self.assertEqual(self.client.get("/fa/management/requests/").status_code, 403)

    def test_exam_role_gets_assessment_shortcut_not_payment(self):
        self.staff(("assessments", "view_exam"))
        response = self.client.get("/fa/management/")
        labels = [item["label"] for item in response.context["management_mobile_nav"]]
        self.assertIn("آزمون‌ها", labels)
        self.assertNotIn("پرداخت‌ها", labels)
        self.assertEqual(self.client.get("/fa/management/assessment-support/").status_code, 200)
        self.assertEqual(self.client.get("/fa/management/approvals/").status_code, 403)

    def test_sales_role_keeps_enquiries_and_contracts_in_mobile(self):
        self.staff(("crm_orders", "view_crmorder"))
        response = self.client.get("/fa/management/")
        self.assertEqual([item["label"] for item in response.context["management_mobile_nav"]],
                         ["امروز", "مشتریان", "درخواست‌ها", "قراردادها"])

    def test_active_item_tracks_actual_destination_in_both_shells(self):
        self.client.force_login(self.root)
        for path, label in (("approvals/", "پرداخت و تأیید"), ("assessment-support/", "آزمون‌ها"),
                            ("requests/", "درخواست و نیازسنجی"), ("workspaces/", "سفارش و قرارداد")):
            with self.subTest(path=path):
                response = self.client.get("/fa/management/" + path)
                self.assertEqual(response.status_code, 200)
                active = [item["label"] for item in response.context["management_primary_nav"] if item["active"]]
                self.assertEqual(active, [label])
                self.assertEqual(response.context["management_more_mobile_active"], path in {"requests/", "workspaces/"})
                self.assertFalse(response.context["management_more_desktop_active"])

    def test_english_navigation_and_search_are_localized_and_escape_input(self):
        self.client.force_login(self.root)
        response = self.client.get("/en/management/customers/", {"q": '<script>alert(1)</script>'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["label"] for item in response.context["management_mobile_nav"]],
                         ["Today", "Customers", "Exams", "Approvals"])
        self.assertContains(response, 'action="/en/management/customers/" method="get" role="search"')
        self.assertContains(response, "Name, phone or email")
        self.assertContains(response, 'value="&lt;script&gt;alert(1)&lt;/script&gt;"')
        self.assertNotContains(response, '<script>alert(1)</script>')

    def test_no_privileged_shortcuts_for_plain_staff_or_customer(self):
        user = self.staff()
        response = self.client.get("/fa/management/")
        self.assertEqual([item["label"] for item in response.context["management_primary_nav"]],
                         ["امروز", "مشتریان", "سفارش و قرارداد"])
        user.is_staff = False
        user.save(update_fields=["is_staff"])
        self.assertEqual(self.client.get("/fa/management/").status_code, 302)
