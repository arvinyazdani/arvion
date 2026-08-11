from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from contracts.models import ContractProposal, ContractReview
from contracts.services import add_default_clauses, publish_version


class ContractWorkflowTests(TestCase):
    def setUp(self):
        self.root = User.objects.create_superuser(username="contract-root", email="contracts@example.com", password="safe-password")
        self.proposal = ContractProposal.objects.create(
            customer_name="مشتری نمونه", customer_phone="989120373271", project_title="سامانه نمونه",
            project_scope="تحلیل و توسعه نسخه اول", amount_irr=1_000_000_000,
            delivery_terms="۸ هفته", created_by=self.root,
        )
        add_default_clauses(self.proposal)

    def test_public_link_is_hidden_before_publish(self):
        response = self.client.get(reverse("contracts:public_contract", args=[self.proposal.token]))
        self.assertEqual(response.status_code, 404)

    def test_publish_creates_immutable_snapshot_and_public_noindex_page(self):
        version = publish_version(self.proposal, self.root)
        original = version.snapshot["project_scope"]
        self.proposal.project_scope = "متن تغییر یافته"
        self.proposal.save()
        version.refresh_from_db()
        self.assertEqual(version.snapshot["project_scope"], original)
        response = self.client.get(reverse("contracts:public_contract", args=[self.proposal.token]))
        self.assertContains(response, "noindex,nofollow,noarchive")
        self.assertContains(response, "سامانه نمونه")
        self.assertNotContains(response, "متن تغییر یافته")

    def test_customer_can_reject_clause_only_with_reason_and_suggest_clause(self):
        version = publish_version(self.proposal, self.root)
        accepted = [str(item["id"]) for item in version.snapshot["clauses"]][1:]
        url = reverse("contracts:public_contract", args=[self.proposal.token])
        invalid = self.client.post(url, {"accepted_clauses": accepted, "suggested_clause": "بند پیشنهادی"})
        self.assertContains(invalid, "برای بندهای مورد تأیید نبود")
        valid = self.client.post(url, {"accepted_clauses": accepted, "rejection_notes": "این بند نیازمند مذاکره است.", "suggested_clause": "بند پیشنهادی"})
        self.assertRedirects(valid, url)
        review = ContractReview.objects.get(version=version)
        self.assertEqual(review.suggested_clause, "بند پیشنهادی")
        self.assertEqual(len(review.rejected_clause_ids), 1)

    def test_non_superuser_cannot_manage_contracts(self):
        staff = User.objects.create_user(username="staff-c", email="staff-c@example.com", password="safe-password", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse("contracts:proposal_list")).status_code, 403)

    def test_manager_can_disable_and_add_clause_without_mutating_old_version(self):
        first = publish_version(self.proposal, self.root)
        old_count = len(first.snapshot["clauses"])
        self.client.force_login(self.root)
        kept = [str(item.pk) for item in self.proposal.clauses.all()[1:]]
        response = self.client.post(reverse("contracts:proposal_clauses", args=[self.proposal.pk]), {
            "enabled_clauses": kept, "custom_title": "بند اختصاصی", "custom_body": "متن بند اختصاصی",
        })
        self.assertRedirects(response, reverse("contracts:proposal_detail", args=[self.proposal.pk]))
        first.refresh_from_db()
        self.assertEqual(len(first.snapshot["clauses"]), old_count)
        second = publish_version(self.proposal, self.root)
        self.assertEqual(len(second.snapshot["clauses"]), old_count)
        self.assertEqual(second.snapshot["clauses"][-1]["title"], "بند اختصاصی")
