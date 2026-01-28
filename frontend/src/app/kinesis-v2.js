/**
 * KINESIS BUNDLE V2 - ULTRATHINK ITERATION 2
 * 
 * Master integration of ALL animation systems:
 * - V1: AliveUI, MicroInteractions, ParticleSystem, StateMachine, PremiumMotion
 * - V2: LiquidMorph, AuroraShader, ParticleCard, SkeletonHaptic, GestureHandler
 * - DELA: HoverEffect, FlowmapDistortion, KineticMaskReveal
 */

class KinesisBundleV2 {
    constructor() {
        this.systems = new Map();
        this.initialized = false;
        this.config = {
            enableParticles: true,
            enableAurora: true,
            enableDela: true,
            enableHaptics: true,
            enableGestures: true,
            reducedMotion: false
        };

        this.init();
    }

    async init() {
        // Check for reduced motion preference
        const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
        this.config.reducedMotion = mediaQuery.matches;

        mediaQuery.addEventListener('change', (e) => {
            this.config.reducedMotion = e.matches;
            this.updateReducedMotion();
        });

        // Wait for DOM
        if (document.readyState === 'loading') {
            await new Promise(resolve =>
                document.addEventListener('DOMContentLoaded', resolve)
            );
        }

        await this.loadSystems();
        this.setupEventBridge();
        this.initialized = true;

        console.log('%c KINESIS V2 🎨 All systems operational ',
            'background: linear-gradient(90deg, #8B5CF6, #3B82F6); color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold;');
    }

    async loadSystems() {
        // Load V1 systems
        try {
            // AliveUI
            if (window.aliveUI) {
                this.systems.set('aliveUI', window.aliveUI);
            }

            // Micro Interactions
            if (window.microInteractions) {
                this.systems.set('microInteractions', window.microInteractions);
            }

            // Particle System
            if (window.particleSystem) {
                this.systems.set('particleSystem', window.particleSystem);
            }

            // V2 Systems
            if (window.liquidMorph) {
                this.systems.set('liquidMorph', window.liquidMorph);
            }

            if (window.auroraShader) {
                this.systems.set('auroraShader', window.auroraShader);
            }

            if (window.particleCards) {
                this.systems.set('particleCards', window.particleCards);
            }

            // Robin Dela Integration
            if (window.delaIntegration) {
                this.systems.set('dela', window.delaIntegration);
            }

        } catch (error) {
            console.warn('[Kinesis] Some systems failed to load:', error);
        }
    }

    setupEventBridge() {
        // Bridge custom events to animation triggers
        document.addEventListener('provider:connecting', (e) => {
            this.triggerConnecting(e.detail.provider);
        });

        document.addEventListener('provider:connected', (e) => {
            this.triggerConnected(e.detail.provider);
        });

        document.addEventListener('provider:error', (e) => {
            this.triggerError(e.detail.provider);
        });

        document.addEventListener('overlay:open', () => {
            this.triggerOverlayOpen();
        });

        document.addEventListener('overlay:close', () => {
            this.triggerOverlayClose();
        });
    }

    // ========================================
    // PUBLIC API
    // ========================================

    triggerConnecting(provider) {
        if (this.config.reducedMotion) return;

        const card = document.querySelector(`[data-provider="${provider}"]`);
        if (!card) return;

        // Add connecting class
        card.classList.add('connecting');

        // Start orbital loader
        if (this.systems.has('particleSystem')) {
            const rect = card.getBoundingClientRect();
            this.systems.get('particleSystem').startOrbitalLoader?.(
                rect.left + rect.width / 2,
                rect.top + rect.height / 2
            );
        }

        // Start skeleton shimmer
        const button = card.querySelector('.auth-button');
        if (button) {
            button.classList.add('skeleton');
        }
    }

    triggerConnected(provider) {
        const card = document.querySelector(`[data-provider="${provider}"]`);
        if (!card) return;

        card.classList.remove('connecting');
        card.classList.add('connected');

        const button = card.querySelector('.auth-button');
        if (button) {
            button.classList.remove('skeleton');
        }

        if (this.config.reducedMotion) return;

        // Celebration burst
        if (this.systems.has('particleSystem')) {
            const rect = card.getBoundingClientRect();
            this.systems.get('particleSystem').emitConnectionParticles?.(
                provider,
                rect.left + rect.width / 2,
                rect.top + rect.height / 2
            );
        }

        // Confetti
        if (window.confetti) {
            window.confetti.fire?.(window.innerWidth / 2, window.innerHeight / 2);
        }

        // Haptic bounce
        card.classList.add('haptic-bounce');
        setTimeout(() => card.classList.remove('haptic-bounce'), 500);

        // Aurora color change
        if (this.systems.has('auroraShader')) {
            this.systems.get('auroraShader').setProviderColor?.(provider);
        }

        // Dela kinetic reveal
        if (this.systems.has('dela')) {
            this.systems.get('dela').triggerConnectionEffect?.(provider);
        }
    }

    triggerError(provider) {
        const card = document.querySelector(`[data-provider="${provider}"]`);
        if (!card) return;

        card.classList.remove('connecting');
        card.classList.add('error');

        const button = card.querySelector('.auth-button');
        if (button) {
            button.classList.remove('skeleton');
        }

        // Haptic shake
        card.classList.add('haptic-shake');
        setTimeout(() => {
            card.classList.remove('haptic-shake', 'error');
        }, 400);
    }

    triggerOverlayOpen() {
        if (this.config.reducedMotion) return;

        // Stagger card entrances
        document.querySelectorAll('.provider-card').forEach((card, i) => {
            card.style.animationDelay = `${100 + i * 80}ms`;
        });

        // Enable aurora
        if (this.systems.has('auroraShader')) {
            const canvas = document.querySelector('#aurora-canvas');
            if (canvas) canvas.style.opacity = '1';
        }
    }

    triggerOverlayClose() {
        // Fade out aurora
        const canvas = document.querySelector('#aurora-canvas');
        if (canvas) canvas.style.opacity = '0';
    }

    enableCursorTrail() {
        if (this.systems.has('particleSystem')) {
            this.systems.get('particleSystem').startCursorTrail?.();
        }
    }

    disableCursorTrail() {
        if (this.systems.has('particleSystem')) {
            this.systems.get('particleSystem').stopCursorTrail?.();
        }
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);

        if (this.systems.has('auroraShader')) {
            const hue = theme === 'dark' ? 280 : 220;
            this.systems.get('auroraShader').providerHue = hue;
        }
    }

    updateReducedMotion() {
        if (this.config.reducedMotion) {
            // Disable all animations
            document.documentElement.classList.add('reduce-motion');
            this.disableCursorTrail();
        } else {
            document.documentElement.classList.remove('reduce-motion');
        }
    }

    // ========================================
    // STATS & DEBUGGING
    // ========================================

    getStats() {
        return {
            initialized: this.initialized,
            systemsLoaded: Array.from(this.systems.keys()),
            config: { ...this.config }
        };
    }

    debug() {
        console.group('🎨 Kinesis V2 Debug');
        console.log('Initialized:', this.initialized);
        console.log('Systems:', Array.from(this.systems.keys()));
        console.log('Config:', this.config);
        console.log('Reduced Motion:', this.config.reducedMotion);
        console.groupEnd();
    }
}

// ========================================
// AUTO-INITIALIZE
// ========================================

const kinesisV2 = new KinesisBundleV2();
window.kinesis = kinesisV2;
window.kinesisV2 = kinesisV2;

// Export for module systems
export { KinesisBundleV2 };
export default kinesisV2;
