/**
 * KINESIS Integration Bundle
 * 
 * Master entry point for all ULTRATHINK animation systems:
 * - Alive UI (magnetic hover, 3D tilt)
 * - Micro Interactions (jelly physics, ripples)
 * - Particle System (connection bursts, trails)
 * - Auth State Machine (XState-like flow)
 * - Premium Motion CSS (auto-loaded)
 */

// Import all systems
import { AliveUI } from './alive-ui.js';
import { MicroInteractionEngine, ConfettiBurst } from './micro-interactions.js';
import { ParticleSystem } from './particle-system.js';

// Initialize all systems
class KinesisBundle {
    constructor() {
        this.aliveUI = null;
        this.microEngine = null;
        this.particles = null;
        this.confetti = null;
        this.initialized = false;
    }

    init() {
        if (this.initialized) return;

        console.log('[KINESIS] 🚀 Initializing ULTRATHINK Animation Bundle');

        // Initialize systems
        this.aliveUI = new AliveUI({
            enableCursorGlow: true,
            enableMagneticButtons: true,
            enable3DTilt: true,
            enableParallax: true
        });

        this.microEngine = new MicroInteractionEngine();
        this.particles = new ParticleSystem();
        this.confetti = new ConfettiBurst();

        // Expose globally
        window.kinesis = this;
        window.aliveUI = this.aliveUI;
        window.microEngine = this.microEngine;
        window.particleSystem = this.particles;
        window.confetti = this.confetti;

        // Load premium motion CSS
        this.loadStyles();

        // Connect to auth events
        this.connectAuthEvents();

        this.initialized = true;
        console.log('[KINESIS] ✅ All systems operational');
    }

    loadStyles() {
        const styles = [
            'src/styles/alive-animations.css',
            'src/styles/premium-motion.css',
            'src/styles/responsive.css'
        ];

        styles.forEach(href => {
            if (!document.querySelector(`link[href="${href}"]`)) {
                const link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = href;
                document.head.appendChild(link);
            }
        });
    }

    connectAuthEvents() {
        // Listen for provider connections
        document.addEventListener('provider-connected', (e) => {
            const { provider, x, y } = e.detail;

            // Fire connection particles
            this.particles.emitConnectionParticles(provider, x, y);

            // Celebrate with confetti
            this.confetti.fire(window.innerWidth / 2, window.innerHeight / 3);
        });

        // Listen for auth flow completion
        document.addEventListener('auth-complete', () => {
            console.log('[KINESIS] 🎉 All providers connected!');

            // Big celebration
            setTimeout(() => {
                this.confetti.fire(window.innerWidth / 4, window.innerHeight / 2);
            }, 0);
            setTimeout(() => {
                this.confetti.fire(window.innerWidth * 3 / 4, window.innerHeight / 2);
            }, 200);
            setTimeout(() => {
                this.confetti.fire(window.innerWidth / 2, window.innerHeight / 3);
            }, 400);
        });
    }

    // Public API methods

    /**
     * Trigger connection animation for a provider
     */
    celebrateConnection(provider, element) {
        const rect = element.getBoundingClientRect();
        const x = rect.left + rect.width / 2;
        const y = rect.top + rect.height / 2;

        document.dispatchEvent(new CustomEvent('provider-connected', {
            detail: { provider, x, y }
        }));
    }

    /**
     * Enable cursor trail effect
     */
    enableCursorTrail() {
        this.particles.startCursorTrail();
    }

    /**
     * Disable cursor trail
     */
    disableCursorTrail() {
        this.particles.stopCursorTrail();
    }

    /**
     * Start loading orbital animation
     */
    startLoading(element) {
        const rect = element.getBoundingClientRect();
        return this.particles.startLoadingOrbit(
            rect.left + rect.width / 2,
            rect.top + rect.height / 2,
            Math.min(rect.width, rect.height) / 2
        );
    }

    /**
     * Stop loading animation
     */
    stopLoading(orbitId) {
        this.particles.stopLoadingOrbit(orbitId);
    }

    /**
     * Cleanup all systems
     */
    destroy() {
        this.aliveUI?.destroy();
        this.microEngine?.destroy();
        this.particles?.destroy();
        this.initialized = false;
    }
}

// Auto-init on DOM ready
const kinesis = new KinesisBundle();

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => kinesis.init());
} else {
    kinesis.init();
}

export { KinesisBundle, kinesis };
export default kinesis;
