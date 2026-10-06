from pathlib import Path

from django.test import SimpleTestCase


STATIC_ROOT = Path(__file__).resolve().parent / "static" / "management_portal" / "v2"


class ManagementUIContractsTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dashboard = (STATIC_ROOT / "today.css").read_text(encoding="utf-8")
        cls.shell = (STATIC_ROOT / "management.css").read_text(encoding="utf-8")

    def test_mobile_quick_actions_are_all_visible_without_horizontal_discovery(self):
        mobile = self.dashboard.split("@media(max-width:760px){", 1)[1]
        self.assertIn("grid-template-columns:repeat(2,minmax(0,1fr))", mobile)
        self.assertIn(".today-row{grid-template-columns:minmax(0,1fr) auto", mobile)
        self.assertNotIn("scroll-snap-type", mobile)

    def test_management_touch_controls_are_at_least_44_pixels(self):
        self.assertIn("min-height:44px", self.dashboard)
        self.assertIn(".m-icon-action,.m-language,.theme-toggle{width:44px;min-width:44px;height:44px}", self.shell)
