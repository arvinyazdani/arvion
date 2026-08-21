import re
from pathlib import Path
from xml.etree import ElementTree

from django.test import SimpleTestCase


STATIC_ROOT = Path(__file__).resolve().parent / "static" / "core"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class UISystemFoundationTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tokens = (STATIC_ROOT / "css" / "tokens.css").read_text(encoding="utf-8")
        cls.components = (STATIC_ROOT / "css" / "components.css").read_text(encoding="utf-8")
        cls.site = (STATIC_ROOT / "css" / "site.css").read_text(encoding="utf-8")
        cls.shell = (STATIC_ROOT / "js" / "site-shell.js").read_text(encoding="utf-8")
        cls.sprite_path = STATIC_ROOT / "icons" / "ui-sprite.svg"

    def test_v3_tokens_cover_type_layout_controls_motion_and_layers(self):
        required_tokens = {
            "--font-family-fa",
            "--font-family-latin",
            "--font-weight-regular:400",
            "--font-weight-bold:700",
            "--font-weight-black:900",
            "--control-height-sm:44px",
            "--control-height-md:44px",
            "--layout-content-max",
            "--z-modal",
            "--z-loader",
            "--icon-size-md",
            "--motion-duration-fast",
            "--motion-duration-loop",
            "--motion-ease-standard",
            "--motion-distance-sm",
            "--status-success-surface",
            "--status-warning-surface",
            "--status-danger-surface",
            "--status-info-surface",
        }
        for token in required_tokens:
            with self.subTest(token=token):
                self.assertIn(token, self.tokens)
        self.assertIn("@media (prefers-reduced-motion:reduce)", self.tokens)

    def test_button_aliases_and_semantic_feedback_are_available(self):
        self.assertRegex(self.components, r"\.btn,\.button,\.button-ghost\{")
        self.assertIn(".btn-ghost,.button.ghost,.button-ghost", self.components)
        self.assertIn(".btn-secondary,.button.secondary", self.components)
        self.assertIn(".btn-danger,.button.danger", self.components)
        self.assertIn('.message.error,.message.danger', self.components)
        self.assertIn('.ui-status[data-status="warning"]', self.components)
        self.assertIn(".ui-icon", self.components)
        self.assertIn("@media(prefers-reduced-motion:reduce)", self.components)
        self.assertIn(".button", self.components.split("@media(forced-colors:active)", 1)[1])

    def test_icon_sprite_exposes_the_stable_public_and_management_contract(self):
        expected_ids = {
            "home", "customers", "forms", "contract", "more", "bell", "search",
            "globe", "theme", "external", "logout", "check", "close", "menu",
            "plus", "arrow", "message", "shield", "assessment", "payment",
            "settings", "content", "activity", "alert", "services", "work",
            "account", "contact", "receipt", "support",
        }
        root = ElementTree.parse(self.sprite_path).getroot()
        symbol_ids = {
            element.attrib["id"]
            for element in root.findall("{http://www.w3.org/2000/svg}symbol")
        }
        self.assertEqual(symbol_ids, expected_ids)

    def test_mobile_menu_shows_exactly_one_state_icon(self):
        # The component foundation loads after site.css, so these selectors
        # must outrank its generic `.ui-icon { display: inline-block }` rule.
        self.assertIn(".menu-button .menu-icon-close{display:none}", self.site)
        self.assertIn(".menu-button.is-open .menu-icon-open{display:none}", self.site)
        self.assertIn(".menu-button.is-open .menu-icon-close{display:block}", self.site)

    def test_project_cards_keep_edge_to_edge_visuals_after_components_load(self):
        self.assertIn(".card.project-card{padding:0;overflow:hidden}", self.site)

    def test_navigation_loader_is_delayed_and_reduced_motion_has_no_wait(self):
        reveal_delay = int(re.search(r"NAVIGATION_REVEAL_DELAY_MS = (\d+)", self.shell).group(1))
        failsafe = int(re.search(r"NAVIGATION_FAILSAFE_MS = (\d+)", self.shell).group(1))
        self.assertLessEqual(reveal_delay, 200)
        self.assertLessEqual(failsafe, 8000)
        self.assertIn('matchMedia?.("(prefers-reduced-motion: reduce)")', self.shell)
        self.assertIn("if (!prefersReducedMotion()) {", self.shell)
        self.assertIn("setMainBusy(true);", self.shell)
        self.assertIn("setWelcomeVisible(true);", self.shell)
        self.assertIn("setNavigationLocked(true);", self.shell)
        self.assertIn("scheduleNavigationLoader();", self.shell)
        self.assertNotIn("1050 -", self.shell)
        self.assertNotIn("15000", self.shell)

    def test_route_feedback_is_shared_by_every_primary_shell(self):
        self.assertIn(".navigation-pending .app-welcome[data-app-welcome]", self.components)
        self.assertIn('querySelectorAll("[data-route-shell]")', self.shell)
        shells = (
            PROJECT_ROOT / "core" / "templates" / "core" / "base.html",
            PROJECT_ROOT / "core" / "templates" / "core" / "flow_base.html",
            PROJECT_ROOT / "contracts" / "templates" / "contracts" / "contract_base.html",
            PROJECT_ROOT / "management_portal" / "templates" / "management_portal" / "v2" / "base.html",
        )
        for shell in shells:
            with self.subTest(shell=shell.name):
                source = shell.read_text(encoding="utf-8")
                self.assertIn('{% include "core/_route_loader.html" %}', source)
                self.assertIn("core/js/site-shell.js", source)

    def test_progressive_reveal_and_scrim_focus_recovery_are_real(self):
        self.assertIn('querySelectorAll("[data-ui-reveal]")', self.shell)
        self.assertIn('"IntersectionObserver" in window', self.shell)
        self.assertIn('item.classList.add("is-visible")', self.shell)
        self.assertIn('scrim.addEventListener("click", () => closeMenu(true))', self.shell)
        self.assertIn('querySelectorAll("main,.mobile-tabbar,.site-footer")', self.shell)
        self.assertIn("setMenuBackgroundInert(true);", self.shell)
        self.assertIn("setMenuBackgroundInert(false);", self.shell)
        self.assertIn(".has-ui-reveal [data-ui-reveal]", self.components)
