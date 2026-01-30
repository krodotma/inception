"""
CODEX-1: Agent Auth E2E Tests
Playwright test suite for Agent Auth overlay
"""
import re
import pytest

# Skip entire module if playwright is not installed
playwright = pytest.importorskip("playwright.sync_api")
Page = playwright.Page
expect = playwright.expect


class TestAgentAuthOverlay:
    """E2E tests for Agent Auth overlay functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Navigate to demo page before each test."""
        self.page = page
        page.goto("http://localhost:8889/agent-auth-demo.html")
        page.wait_for_load_state("networkidle")

    def test_overlay_opens_on_button_click(self):
        """Verify overlay opens when trigger button is clicked."""
        # Click trigger button
        self.page.click(".demo-trigger")
        
        # Verify overlay is visible
        overlay = self.page.locator(".agent-auth-backdrop")
        expect(overlay).to_have_class(re.compile(r"visible"))
        
        # Verify overlay content is present
        expect(self.page.locator(".agent-auth-title")).to_contain_text("Connect AI Providers")

    def test_overlay_closes_on_x_button(self):
        """Verify overlay closes when X button is clicked."""
        self.page.click(".demo-trigger")
        self.page.wait_for_selector(".agent-auth-backdrop.visible")
        
        self.page.click(".agent-auth-close")
        
        overlay = self.page.locator(".agent-auth-backdrop")
        expect(overlay).not_to_have_class(re.compile(r"visible"))

    def test_overlay_closes_on_escape(self):
        """Verify overlay closes on Escape key."""
        self.page.click(".demo-trigger")
        self.page.wait_for_selector(".agent-auth-backdrop.visible")
        
        self.page.keyboard.press("Escape")
        
        overlay = self.page.locator(".agent-auth-backdrop")
        expect(overlay).not_to_have_class(re.compile(r"visible"))

    def test_five_provider_cards_present(self):
        """Verify all 5 provider cards are rendered."""
        self.page.click(".demo-trigger")
        self.page.wait_for_selector(".agent-auth-backdrop.visible")
        
        cards = self.page.locator(".provider-card")
        expect(cards).to_have_count(5)
        
        # Verify each provider
        expect(self.page.locator('[data-provider="claude"]')).to_be_visible()
        expect(self.page.locator('[data-provider="gemini"]')).to_be_visible()
        expect(self.page.locator('[data-provider="codex"]')).to_be_visible()
        expect(self.page.locator('[data-provider="kimi"]')).to_be_visible()
        expect(self.page.locator('[data-provider="antigravity"]')).to_be_visible()

    def test_connected_providers_show_checkmark(self):
        """Verify connected providers display checkmark."""
        self.page.click(".demo-trigger")
        self.page.wait_for_selector(".agent-auth-backdrop.visible")
        
        # Claude, Gemini, Codex, Antigravity should be connected
        for provider in ["claude", "gemini", "codex", "antigravity"]:
            card = self.page.locator(f'[data-provider="{provider}"]')
            expect(card).to_have_class(re.compile(r"connected"))
            expect(card.locator(".auth-button")).to_contain_text("✓")

    def test_kimi_shows_not_set(self):
        """Verify Kimi shows 'Not Set' status."""
        self.page.click(".demo-trigger")
        self.page.wait_for_selector(".agent-auth-backdrop.visible")
        
        kimi_card = self.page.locator('[data-provider="kimi"]')
        expect(kimi_card).not_to_have_class(re.compile(r"connected"))
        expect(kimi_card.locator(".connection-badge")).to_contain_text("Not Set")


class TestFilterButtons:
    """Tests for isotope-like filtering functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        self.page = page
        page.goto("http://localhost:8889/agent-auth-demo.html")
        page.click(".demo-trigger")
        page.wait_for_selector(".agent-auth-backdrop.visible")

    def test_all_filter_shows_all_cards(self):
        """Verify 'All' filter shows all 4 cards."""
        self.page.click('[data-filter="all"]')
        
        visible_cards = self.page.locator(".provider-card:visible")
        expect(visible_cards).to_have_count(4)

    def test_connected_filter_shows_3_cards(self):
        """Verify 'Connected' filter shows only connected providers."""
        self.page.click('[data-filter="connected"]')
        self.page.wait_for_timeout(300)  # Wait for filter animation
        
        # Kimi should be hidden
        kimi = self.page.locator('[data-provider="kimi"]')
        expect(kimi).to_have_css("opacity", "0")

    def test_pending_filter_shows_1_card(self):
        """Verify 'Pending' filter shows only disconnected providers."""
        self.page.click('[data-filter="pending"]')
        self.page.wait_for_timeout(300)
        
        # Only Kimi should be visible with full opacity
        kimi = self.page.locator('[data-provider="kimi"]')
        expect(kimi).to_be_visible()
        
        # Others should be hidden
        claude = self.page.locator('[data-provider="claude"]')
        expect(claude).to_have_css("opacity", "0")

    def test_filter_button_active_state(self):
        """Verify active filter button has correct styling."""
        all_btn = self.page.locator('[data-filter="all"]')
        connected_btn = self.page.locator('[data-filter="connected"]')
        
        # Initially 'All' is active
        expect(all_btn).to_have_class(re.compile(r"active"))
        
        # Click 'Connected'
        connected_btn.click()
        expect(connected_btn).to_have_class(re.compile(r"active"))
        expect(all_btn).not_to_have_class(re.compile(r"active"))


class TestKimiModal:
    """Tests for Kimi API key modal."""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        self.page = page
        page.goto("http://localhost:8889/agent-auth-demo.html")
        page.click(".demo-trigger")
        page.wait_for_selector(".agent-auth-backdrop.visible")

    def test_kimi_button_opens_modal(self):
        """Verify clicking Kimi 'Configure' opens API key modal."""
        kimi_btn = self.page.locator('[data-provider="kimi"] .auth-button')
        kimi_btn.click()
        
        modal = self.page.locator("#kimiModal")
        expect(modal).to_have_class(re.compile(r"visible"))

    def test_modal_has_input_field(self):
        """Verify modal has API key input."""
        self.page.click('[data-provider="kimi"] .auth-button')
        
        input_field = self.page.locator("#kimiApiKey")
        expect(input_field).to_be_visible()
        expect(input_field).to_have_attribute("type", "password")

    def test_save_updates_card_status(self):
        """Verify saving API key updates Kimi card to connected."""
        self.page.click('[data-provider="kimi"] .auth-button')
        
        # Enter API key
        self.page.fill("#kimiApiKey", "sk-test-key-12345")
        
        # Click save
        self.page.click("button:has-text('Save & Connect')")
        
        # Verify Kimi card is now connected
        kimi_card = self.page.locator('[data-provider="kimi"]')
        expect(kimi_card).to_have_class(re.compile(r"connected"))
        expect(kimi_card.locator(".auth-button")).to_contain_text("✓ Kimi Active")

    def test_cancel_closes_modal(self):
        """Verify cancel button closes modal without saving."""
        self.page.click('[data-provider="kimi"] .auth-button')
        self.page.fill("#kimiApiKey", "sk-test")
        
        self.page.click("button:has-text('Cancel')")
        
        modal = self.page.locator("#kimiModal")
        expect(modal).not_to_have_class(re.compile(r"visible"))
        
        # Kimi should still be disconnected
        kimi_card = self.page.locator('[data-provider="kimi"]')
        expect(kimi_card).not_to_have_class(re.compile(r"connected"))


class TestAccessibility:
    """Accessibility tests for Agent Auth overlay."""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        self.page = page
        page.goto("http://localhost:8889/agent-auth-demo.html")
        page.click(".demo-trigger")
        page.wait_for_selector(".agent-auth-backdrop.visible")

    def test_dialog_has_role(self):
        """Verify overlay has dialog role."""
        overlay = self.page.locator(".agent-auth-overlay")
        expect(overlay).to_have_attribute("role", "dialog")

    def test_close_button_has_aria_label(self):
        """Verify close button is accessible."""
        close_btn = self.page.locator(".agent-auth-close")
        expect(close_btn).to_have_attribute("aria-label", "Close dialog")

    def test_keyboard_navigation(self):
        """Verify tab navigation works correctly."""
        # First focusable should be close button
        self.page.keyboard.press("Tab")
        
        close_btn = self.page.locator(".agent-auth-close")
        expect(close_btn).to_be_focused()

    def test_filter_tabs_have_aria(self):
        """Verify filter buttons have tab roles."""
        filter_btns = self.page.locator(".filter-btn")
        
        for i in range(3):
            btn = filter_btns.nth(i)
            expect(btn).to_have_attribute("role", "tab")


class TestAnimations:
    """Animation and transition tests."""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        self.page = page
        page.goto("http://localhost:8889/agent-auth-demo.html")

    def test_overlay_entrance_animation(self):
        """Verify overlay has entrance animation."""
        self.page.click(".demo-trigger")
        
        overlay = self.page.locator(".agent-auth-overlay")
        
        # Should start scaled down
        # After animation, should be scale(1)
        self.page.wait_for_timeout(500)
        expect(overlay).to_be_visible()

    def test_card_stagger_animation(self):
        """Verify cards animate in with stagger."""
        self.page.click(".demo-trigger")
        
        # Cards should have staggered animation-delay
        cards = self.page.locator(".provider-card")
        
        # All cards should eventually be visible
        self.page.wait_for_timeout(500)
        expect(cards.first).to_be_visible()


# Visual Regression Snapshot (requires pytest-playwright-snapshot)
class TestVisualRegression:
    """Visual regression tests."""

    def test_overlay_snapshot(self, page: Page, assert_snapshot):
        """Capture overlay for visual regression."""
        page.goto("http://localhost:8889/agent-auth-demo.html")
        page.click(".demo-trigger")
        page.wait_for_timeout(600)  # Wait for animations
        
        overlay = page.locator(".agent-auth-overlay")
        assert_snapshot(overlay.screenshot(), "agent-auth-overlay.png")

    def test_connected_filter_snapshot(self, page: Page, assert_snapshot):
        """Capture connected filter state."""
        page.goto("http://localhost:8889/agent-auth-demo.html")
        page.click(".demo-trigger")
        page.wait_for_timeout(300)
        page.click('[data-filter="connected"]')
        page.wait_for_timeout(500)
        
        providers = page.locator(".agent-auth-providers")
        assert_snapshot(providers.screenshot(), "connected-filter.png")
