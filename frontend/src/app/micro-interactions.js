/**
 * OPUS-1 ULTRATHINK: Micro-Interaction Physics Engine
 * 
 * Every interaction is alive:
 * - Jelly physics on buttons
 * - Magnetic hover attraction
 * - Provider-colored ripples
 * - Parallax card layers
 * - Heartbeat pulse sync
 */

// Physics constants
const SPRING = {
    STIFFNESS: 150,
    DAMPING: 15,
    MASS: 1
};

const JELLY = {
    WOBBLE_INTENSITY: 0.15,
    RECOVERY_SPEED: 0.08,
    MAX_DEFORM: 0.3
};

class MicroInteractionEngine {
    constructor() {
        this.elements = new Map();
        this.rafId = null;
        this.lastTime = 0;
        this.heartbeatPhase = 0;

        // Provider colors for ripples
        this.providerColors = {
            claude: { r: 139, g: 92, b: 246 },    // #8B5CF6
            gemini: { r: 66, g: 133, b: 244 },    // #4285F4
            codex: { r: 16, g: 185, b: 129 },     // #10B981
            kimi: { r: 245, g: 158, b: 11 }       // #F59E0B
        };

        this.init();
    }

    init() {
        this.setupJellyButtons();
        this.setupMagneticHover();
        this.setupProviderRipples();
        this.setupParallaxCards();
        this.startHeartbeat();

        console.log('[MicroInteractionEngine] 🎯 200% ULTRATHINK Active');
    }

    // ========================================
    // JELLY PHYSICS - Buttons wobble on press
    // ========================================

    setupJellyButtons() {
        const buttons = document.querySelectorAll('.auth-button, .filter-btn, .demo-trigger');

        buttons.forEach(btn => {
            const state = {
                scaleX: 1,
                scaleY: 1,
                velocityX: 0,
                velocityY: 0,
                isPressed: false
            };

            this.elements.set(btn, { type: 'jelly', state });

            btn.addEventListener('pointerdown', () => {
                state.isPressed = true;
                state.velocityX = -JELLY.WOBBLE_INTENSITY;
                state.velocityY = JELLY.WOBBLE_INTENSITY * 1.5;
            });

            btn.addEventListener('pointerup', () => {
                state.isPressed = false;
                state.velocityX = JELLY.WOBBLE_INTENSITY * 0.5;
                state.velocityY = -JELLY.WOBBLE_INTENSITY;
            });

            btn.addEventListener('pointerleave', () => {
                state.isPressed = false;
            });
        });

        this.startPhysicsLoop();
    }

    updateJellyPhysics(element, state, dt) {
        // Spring physics
        const targetX = state.isPressed ? 1 - JELLY.MAX_DEFORM * 0.3 : 1;
        const targetY = state.isPressed ? 1 + JELLY.MAX_DEFORM * 0.2 : 1;

        // Calculate spring force
        const forceX = (targetX - state.scaleX) * SPRING.STIFFNESS;
        const forceY = (targetY - state.scaleY) * SPRING.STIFFNESS;

        // Apply damping
        state.velocityX += (forceX / SPRING.MASS) * dt;
        state.velocityY += (forceY / SPRING.MASS) * dt;
        state.velocityX *= Math.pow(1 - SPRING.DAMPING * 0.01, dt * 60);
        state.velocityY *= Math.pow(1 - SPRING.DAMPING * 0.01, dt * 60);

        // Update position
        state.scaleX += state.velocityX * dt;
        state.scaleY += state.velocityY * dt;

        // Apply transform
        element.style.transform = `scale(${state.scaleX}, ${state.scaleY})`;
    }

    // ========================================
    // MAGNETIC HOVER - Elements attracted to cursor
    // ========================================

    setupMagneticHover() {
        const magneticElements = document.querySelectorAll('.demo-trigger, .agent-auth-close');

        magneticElements.forEach(el => {
            const state = {
                baseX: 0,
                baseY: 0,
                currentX: 0,
                currentY: 0,
                isHovering: false
            };

            this.elements.set(el, { ...this.elements.get(el), magnetic: state });

            el.addEventListener('mousemove', (e) => {
                const rect = el.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;

                // Calculate attraction (stronger near center)
                const distX = e.clientX - centerX;
                const distY = e.clientY - centerY;
                const maxDist = Math.max(rect.width, rect.height);
                const strength = Math.max(0, 1 - Math.hypot(distX, distY) / maxDist);

                state.currentX = distX * 0.3 * strength;
                state.currentY = distY * 0.3 * strength;
                state.isHovering = true;

                el.style.transform = `translate(${state.currentX}px, ${state.currentY}px)`;
            });

            el.addEventListener('mouseleave', () => {
                state.isHovering = false;
                // Smooth return with spring
                this.animateReturn(el, state);
            });
        });
    }

    animateReturn(el, state) {
        const animate = () => {
            if (state.isHovering) return;

            state.currentX *= 0.85;
            state.currentY *= 0.85;

            el.style.transform = `translate(${state.currentX}px, ${state.currentY}px)`;

            if (Math.abs(state.currentX) > 0.1 || Math.abs(state.currentY) > 0.1) {
                requestAnimationFrame(animate);
            } else {
                el.style.transform = '';
            }
        };
        requestAnimationFrame(animate);
    }

    // ========================================
    // PROVIDER-COLORED RIPPLES
    // ========================================

    setupProviderRipples() {
        const cards = document.querySelectorAll('.provider-card');

        cards.forEach(card => {
            card.addEventListener('click', (e) => {
                const provider = card.dataset.provider;
                const color = this.providerColors[provider] || { r: 255, g: 255, b: 255 };

                this.createRipple(card, e, color);
            });
        });
    }

    createRipple(container, event, color) {
        const rect = container.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        const ripple = document.createElement('div');
        ripple.className = 'micro-ripple';
        ripple.style.cssText = `
            position: absolute;
            left: ${x}px;
            top: ${y}px;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: radial-gradient(circle, 
                rgba(${color.r}, ${color.g}, ${color.b}, 0.6) 0%, 
                rgba(${color.r}, ${color.g}, ${color.b}, 0) 70%);
            transform: translate(-50%, -50%);
            pointer-events: none;
            z-index: 100;
        `;

        container.style.position = 'relative';
        container.style.overflow = 'hidden';
        container.appendChild(ripple);

        // Animate ripple expansion
        ripple.animate([
            { width: '0px', height: '0px', opacity: 1 },
            { width: '400px', height: '400px', opacity: 0 }
        ], {
            duration: 600,
            easing: 'cubic-bezier(0.22, 1, 0.36, 1)'
        }).onfinish = () => ripple.remove();
    }

    // ========================================
    // PARALLAX CARD LAYERS
    // ========================================

    setupParallaxCards() {
        const cards = document.querySelectorAll('.provider-card');

        cards.forEach(card => {
            const logo = card.querySelector('.provider-logo');
            const info = card.querySelector('.provider-info');
            const badge = card.querySelector('.connection-badge');

            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = (e.clientX - rect.left - rect.width / 2) / rect.width;
                const y = (e.clientY - rect.top - rect.height / 2) / rect.height;

                // Different depths for different elements
                if (logo) {
                    logo.style.transform = `translate(${x * 15}px, ${y * 15}px) scale(1.1)`;
                }
                if (info) {
                    info.style.transform = `translate(${x * 8}px, ${y * 8}px)`;
                }
                if (badge) {
                    badge.style.transform = `translate(${x * -5}px, ${y * -5}px)`;
                }

                // Card tilt
                card.style.transform = `
                    perspective(1000px) 
                    rotateX(${-y * 10}deg) 
                    rotateY(${x * 10}deg)
                    scale(1.02)
                `;
            });

            card.addEventListener('mouseleave', () => {
                card.style.transform = '';
                if (logo) logo.style.transform = '';
                if (info) info.style.transform = '';
                if (badge) badge.style.transform = '';
            });
        });
    }

    // ========================================
    // HEARTBEAT PULSE SYNC
    // ========================================

    startHeartbeat() {
        const connectedBadges = document.querySelectorAll('.connection-badge.connected');

        const pulse = () => {
            this.heartbeatPhase += 0.05;

            // Two-beat pattern (lub-dub)
            const t = this.heartbeatPhase % (Math.PI * 2);
            const beat1 = Math.sin(t) > 0.8 ? 1 : 0;
            const beat2 = Math.sin(t + 0.4) > 0.9 ? 0.7 : 0;
            const intensity = beat1 + beat2;

            connectedBadges.forEach(badge => {
                const glow = 5 + intensity * 15;
                badge.style.boxShadow = `0 0 ${glow}px rgba(34, 197, 94, ${0.4 + intensity * 0.3})`;
            });

            requestAnimationFrame(pulse);
        };

        pulse();
    }

    // ========================================
    // PHYSICS LOOP
    // ========================================

    startPhysicsLoop() {
        const loop = (time) => {
            const dt = Math.min((time - this.lastTime) / 1000, 0.1);
            this.lastTime = time;

            this.elements.forEach((data, element) => {
                if (data.type === 'jelly') {
                    this.updateJellyPhysics(element, data.state, dt);
                }
            });

            this.rafId = requestAnimationFrame(loop);
        };

        this.rafId = requestAnimationFrame(loop);
    }

    destroy() {
        if (this.rafId) {
            cancelAnimationFrame(this.rafId);
        }
    }
}

// ========================================
// SUCCESS CELEBRATION - Confetti burst
// ========================================

class ConfettiBurst {
    constructor() {
        this.particles = [];
        this.canvas = null;
        this.ctx = null;
    }

    fire(x, y, color) {
        if (!this.canvas) {
            this.createCanvas();
        }

        // Create 50 particles
        for (let i = 0; i < 50; i++) {
            this.particles.push({
                x, y,
                vx: (Math.random() - 0.5) * 20,
                vy: -Math.random() * 15 - 5,
                size: Math.random() * 8 + 4,
                color: color || `hsl(${Math.random() * 360}, 70%, 60%)`,
                rotation: Math.random() * 360,
                rotationSpeed: (Math.random() - 0.5) * 20,
                life: 1
            });
        }

        this.animate();
    }

    createCanvas() {
        this.canvas = document.createElement('canvas');
        this.canvas.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 10000;
        `;
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        document.body.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');
    }

    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        this.particles = this.particles.filter(p => {
            p.x += p.vx;
            p.y += p.vy;
            p.vy += 0.5; // Gravity
            p.rotation += p.rotationSpeed;
            p.life -= 0.02;

            if (p.life <= 0) return false;

            this.ctx.save();
            this.ctx.translate(p.x, p.y);
            this.ctx.rotate(p.rotation * Math.PI / 180);
            this.ctx.globalAlpha = p.life;
            this.ctx.fillStyle = p.color;
            this.ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size);
            this.ctx.restore();

            return true;
        });

        if (this.particles.length > 0) {
            requestAnimationFrame(() => this.animate());
        } else if (this.canvas) {
            this.canvas.remove();
            this.canvas = null;
        }
    }
}

// Auto-initialize
const microEngine = new MicroInteractionEngine();
const confetti = new ConfettiBurst();

// Export for use
window.microInteractionEngine = microEngine;
window.confetti = confetti;

export { MicroInteractionEngine, ConfettiBurst };
