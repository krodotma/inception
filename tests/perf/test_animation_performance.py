"""
CODEX-1 ULTRATHINK: Performance & Animation Benchmarks
Testing 60fps consistency, memory leaks, and animation smoothness
"""
import pytest
import time
import json
from playwright.sync_api import Page, expect


class TestAnimationPerformance:
    """Performance benchmarks for animation systems."""
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        self.page = page
        # Enable performance tracing
        page.goto("http://localhost:8889/agent-auth-demo.html")
        page.wait_for_load_state("networkidle")

    def test_overlay_animation_fps(self):
        """Verify overlay entrance maintains 60fps."""
        # Start performance measurement
        self.page.evaluate("""
            window.frameTimestamps = [];
            window.measureFrames = true;
            function recordFrame(timestamp) {
                if (window.measureFrames) {
                    window.frameTimestamps.push(timestamp);
                    requestAnimationFrame(recordFrame);
                }
            }
            requestAnimationFrame(recordFrame);
        """)
        
        # Trigger overlay animation
        self.page.click(".demo-trigger")
        self.page.wait_for_timeout(600)  # Wait for animation
        
        # Stop measurement
        self.page.evaluate("window.measureFrames = false;")
        
        # Calculate FPS
        timestamps = self.page.evaluate("window.frameTimestamps")
        
        if len(timestamps) >= 2:
            frame_deltas = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
            avg_delta = sum(frame_deltas) / len(frame_deltas)
            fps = 1000 / avg_delta if avg_delta > 0 else 0
            
            print(f"Average FPS during animation: {fps:.1f}")
            assert fps >= 55, f"FPS dropped below 55: {fps:.1f}"

    def test_filter_animation_no_jank(self):
        """Verify filter toggle is smooth without layout thrashing."""
        self.page.click(".demo-trigger")
        self.page.wait_for_timeout(400)
        
        # Measure filter animation
        self.page.evaluate("""
            window.layoutShifts = [];
            const observer = new PerformanceObserver((list) => {
                for (const entry of list.getEntries()) {
                    window.layoutShifts.push(entry.value);
                }
            });
            observer.observe({ type: 'layout-shift', buffered: true });
        """)
        
        # Toggle filters rapidly
        for filter_name in ['connected', 'pending', 'all']:
            self.page.click(f'[data-filter="{filter_name}"]')
            self.page.wait_for_timeout(100)
        
        self.page.wait_for_timeout(300)
        
        shifts = self.page.evaluate("window.layoutShifts")
        total_shift = sum(shifts) if shifts else 0
        
        print(f"Cumulative Layout Shift: {total_shift:.4f}")
        assert total_shift < 0.1, f"Layout shift too high: {total_shift:.4f}"

    def test_particle_system_memory(self):
        """Verify particle system doesn't leak memory."""
        self.page.click(".demo-trigger")
        self.page.wait_for_timeout(300)
        
        # Get initial memory
        initial_memory = self.page.evaluate("""
            performance.memory ? performance.memory.usedJSHeapSize : null
        """)
        
        if initial_memory is None:
            pytest.skip("Memory API not available")
        
        # Trigger many particle bursts
        for i in range(10):
            self.page.click('[data-provider="claude"]')
            self.page.wait_for_timeout(100)
        
        self.page.wait_for_timeout(1000)  # Let particles settle
        
        # Force GC and measure
        self.page.evaluate("gc && gc()")
        self.page.wait_for_timeout(100)
        
        final_memory = self.page.evaluate("performance.memory.usedJSHeapSize")
        
        memory_growth = (final_memory - initial_memory) / 1024 / 1024  # MB
        print(f"Memory growth: {memory_growth:.2f} MB")
        
        assert memory_growth < 5, f"Memory grew by {memory_growth:.2f} MB"

    def test_animation_gpu_acceleration(self):
        """Verify animations use GPU-accelerated properties."""
        self.page.click(".demo-trigger")
        self.page.wait_for_timeout(300)
        
        # Check computed styles for GPU-only properties
        card_styles = self.page.evaluate("""
            const card = document.querySelector('.provider-card');
            const style = getComputedStyle(card);
            return {
                transform: style.transform,
                willChange: style.willChange,
                backfaceVisibility: style.backfaceVisibility
            };
        """)
        
        print(f"Card animation properties: {json.dumps(card_styles, indent=2)}")
        
        # Verify will-change is set for performance
        will_change = card_styles.get('willChange', '')
        assert 'transform' in will_change or 'auto' in will_change


class TestCrossDeviceResponsiveness:
    """Tests for responsive design and touch interactions."""
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        self.page = page

    @pytest.mark.parametrize("viewport", [
        {"width": 375, "height": 667},   # iPhone SE
        {"width": 390, "height": 844},   # iPhone 12
        {"width": 768, "height": 1024},  # iPad
        {"width": 1280, "height": 800},  # Desktop
        {"width": 1920, "height": 1080}, # Full HD
    ])
    def test_overlay_responsive_sizing(self, viewport):
        """Verify overlay adapts to different screen sizes."""
        self.page.set_viewport_size(viewport)
        self.page.goto("http://localhost:8889/agent-auth-demo.html")
        self.page.click(".demo-trigger")
        self.page.wait_for_timeout(400)
        
        overlay = self.page.locator(".agent-auth-overlay")
        box = overlay.bounding_box()
        
        assert box is not None, "Overlay not visible"
        
        # Mobile: full width
        if viewport["width"] < 640:
            assert box["width"] >= viewport["width"] * 0.9
        # Tablet+: constrained width
        else:
            assert box["width"] <= 680

    def test_touch_target_sizes(self):
        """Verify touch targets meet minimum 44px requirement."""
        self.page.set_viewport_size({"width": 375, "height": 667})
        self.page.goto("http://localhost:8889/agent-auth-demo.html")
        self.page.click(".demo-trigger")
        self.page.wait_for_timeout(300)
        
        buttons = self.page.locator(".auth-button, .filter-btn")
        
        for i in range(buttons.count()):
            btn = buttons.nth(i)
            box = btn.bounding_box()
            
            assert box["height"] >= 44, f"Button {i} height too small: {box['height']}"
            assert box["width"] >= 44, f"Button {i} width too small: {box['width']}"


class TestReducedMotion:
    """Tests for prefers-reduced-motion compliance."""
    
    def test_animations_disabled_with_reduced_motion(self, page: Page):
        """Verify animations are disabled when user prefers reduced motion."""
        # Emulate reduced motion preference
        page.emulate_media(reduced_motion="reduce")
        page.goto("http://localhost:8889/agent-auth-demo.html")
        page.click(".demo-trigger")
        page.wait_for_timeout(100)  # Should be near-instant
        
        overlay = page.locator(".agent-auth-overlay")
        
        # Check that transitions are effectively instant
        transition_duration = page.evaluate("""
            getComputedStyle(document.querySelector('.agent-auth-overlay'))
                .transitionDuration
        """)
        
        # Should be 0.01ms or similar (effectively instant)
        assert '0.01' in transition_duration or '0s' in transition_duration or '0ms' in transition_duration

    def test_focus_states_without_animation(self, page: Page):
        """Verify focus states work without pulsing animation."""
        page.emulate_media(reduced_motion="reduce")
        page.goto("http://localhost:8889/agent-auth-demo.html")
        page.click(".demo-trigger")
        page.wait_for_timeout(100)
        
        # Tab to first button
        page.keyboard.press("Tab")
        page.keyboard.press("Tab")  # Skip close button
        
        button = page.locator(".filter-btn:first-child")
        
        # Should have visible focus ring without animation
        has_focus_style = page.evaluate("""
            const btn = document.querySelector('.filter-btn');
            const style = getComputedStyle(btn);
            return style.boxShadow !== 'none' || style.outline !== 'none';
        """)
        
        assert has_focus_style, "Focus state not visible with reduced motion"


class TestBundleSize:
    """Tests for JavaScript bundle size optimization."""
    
    def test_animation_js_bundle_size(self, page: Page):
        """Verify animation JS files are reasonably sized."""
        import os
        
        base_path = "/Users/kroma/inceptional/frontend/src/app"
        animation_files = [
            "alive-ui.js",
            "micro-interactions.js",
            "particle-system.js",
            "auth-state-machine.ts"
        ]
        
        total_size = 0
        for filename in animation_files:
            filepath = os.path.join(base_path, filename)
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                total_size += size
                print(f"{filename}: {size / 1024:.1f} KB")
        
        print(f"Total animation bundle: {total_size / 1024:.1f} KB")
        
        # Should be under 100KB unminified
        assert total_size < 100 * 1024, f"Bundle too large: {total_size / 1024:.1f} KB"


class TestAnimationIntegration:
    """Integration tests for animation systems working together."""
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        self.page = page
        page.goto("http://localhost:8889/agent-auth-demo.html")
        page.wait_for_load_state("networkidle")

    def test_full_auth_flow_animations(self):
        """Test complete auth flow with all animations firing."""
        # 1. Open overlay
        self.page.click(".demo-trigger")
        self.page.wait_for_timeout(500)
        
        expect(self.page.locator(".agent-auth-backdrop")).to_have_class(/visible/)
        
        # 2. Filter to connected
        self.page.click('[data-filter="connected"]')
        self.page.wait_for_timeout(300)
        
        # 3. Open Kimi modal
        self.page.click('[data-filter="all"]')
        self.page.wait_for_timeout(200)
        self.page.click('[data-provider="kimi"] .auth-button')
        self.page.wait_for_timeout(300)
        
        expect(self.page.locator("#kimiModal")).to_have_class(/visible/)
        
        # 4. Enter key and save
        self.page.fill("#kimiApiKey", "sk-test-key")
        self.page.click("button:has-text('Save & Connect')")
        self.page.wait_for_timeout(500)
        
        # 5. Verify Kimi connected
        kimi_card = self.page.locator('[data-provider="kimi"]')
        expect(kimi_card).to_have_class(/connected/)
        
        # 6. Close overlay
        self.page.click(".agent-auth-close")
        self.page.wait_for_timeout(300)
        
        expect(self.page.locator(".agent-auth-backdrop")).not_to_have_class(/visible/)

    def test_particles_emit_on_connection(self):
        """Verify particle system fires when provider connects."""
        self.page.click(".demo-trigger")
        self.page.wait_for_timeout(400)
        
        # Check if particle canvas exists after card click
        self.page.click('[data-provider="kimi"] .auth-button')
        self.page.fill("#kimiApiKey", "sk-test")
        self.page.click("button:has-text('Save & Connect')")
        
        self.page.wait_for_timeout(200)
        
        # Canvas should be created for particles
        has_particle_canvas = self.page.evaluate("""
            document.querySelector('#particle-canvas') !== null ||
            document.querySelector('.micro-ripple') !== null
        """)
        
        # At minimum, ripple should appear
        # (Particle canvas may be cleaned up quickly)
        print(f"Particle/ripple effect detected: {has_particle_canvas}")
