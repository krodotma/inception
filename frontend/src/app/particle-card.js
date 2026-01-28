/**
 * GEMINI-1 ITERATION 2: 3D Particle Card Effect
 * 
 * Inspired by Robin Dela's CodePen jVddbq
 * 3D cards with particles that flow across the surface
 * - Mouse-following 3D rotation
 * - Particle trails on card surface
 * - Glowing edge highlights
 * - Depth-based shadows
 */

class ParticleCardEngine {
    constructor() {
        this.cards = new Map();
        this.particlePool = [];
        this.maxParticles = 100;
        this.animationId = null;

        this.init();
    }

    init() {
        this.setupCards();
        this.startAnimation();
        console.log('[ParticleCardEngine] 🃏 3D particle cards active');
    }

    setupCards() {
        const cards = document.querySelectorAll('.provider-card, .particle-card');

        cards.forEach(card => {
            const state = {
                rotateX: 0,
                rotateY: 0,
                targetRotateX: 0,
                targetRotateY: 0,
                particles: [],
                glowIntensity: 0,
                isHovered: false
            };

            // Create particle container
            const particleContainer = document.createElement('div');
            particleContainer.className = 'card-particles';
            particleContainer.style.cssText = `
                position: absolute;
                inset: 0;
                overflow: hidden;
                pointer-events: none;
                border-radius: inherit;
            `;
            card.appendChild(particleContainer);

            // Create glow border
            const glowBorder = document.createElement('div');
            glowBorder.className = 'card-glow-border';
            glowBorder.style.cssText = `
                position: absolute;
                inset: -2px;
                border-radius: inherit;
                background: linear-gradient(
                    var(--glow-angle, 135deg),
                    transparent 30%,
                    var(--provider-color, rgba(139, 92, 246, 0.5)) 50%,
                    transparent 70%
                );
                opacity: 0;
                transition: opacity 0.3s ease;
                pointer-events: none;
                z-index: -1;
            `;
            card.appendChild(glowBorder);

            this.cards.set(card, { state, particleContainer, glowBorder });

            // Event listeners
            card.addEventListener('mousemove', (e) => this.handleMouseMove(card, e));
            card.addEventListener('mouseenter', () => this.handleMouseEnter(card));
            card.addEventListener('mouseleave', () => this.handleMouseLeave(card));

            // Apply base styles
            card.style.transformStyle = 'preserve-3d';
            card.style.transition = 'transform 0.1s ease-out';
        });
    }

    handleMouseMove(card, e) {
        const data = this.cards.get(card);
        if (!data) return;

        const rect = card.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;

        // Calculate rotation based on mouse position
        const mouseX = e.clientX - centerX;
        const mouseY = e.clientY - centerY;

        const rotateY = (mouseX / (rect.width / 2)) * 15;
        const rotateX = -(mouseY / (rect.height / 2)) * 15;

        data.state.targetRotateX = rotateX;
        data.state.targetRotateY = rotateY;

        // Calculate glow angle
        const angle = Math.atan2(mouseY, mouseX) * (180 / Math.PI) + 90;
        data.glowBorder.style.setProperty('--glow-angle', `${angle}deg`);

        // Spawn particles
        if (data.state.isHovered && Math.random() > 0.7) {
            this.spawnParticle(data, e.clientX - rect.left, e.clientY - rect.top);
        }
    }

    handleMouseEnter(card) {
        const data = this.cards.get(card);
        if (!data) return;

        data.state.isHovered = true;
        data.glowBorder.style.opacity = '1';

        // Initial particle burst
        const rect = card.getBoundingClientRect();
        for (let i = 0; i < 10; i++) {
            this.spawnParticle(
                data,
                Math.random() * rect.width,
                Math.random() * rect.height
            );
        }
    }

    handleMouseLeave(card) {
        const data = this.cards.get(card);
        if (!data) return;

        data.state.isHovered = false;
        data.state.targetRotateX = 0;
        data.state.targetRotateY = 0;
        data.glowBorder.style.opacity = '0';
    }

    spawnParticle(data, x, y) {
        if (data.state.particles.length >= 20) return;

        const particle = document.createElement('div');
        const size = 2 + Math.random() * 4;
        const hue = this.getProviderHue(data.particleContainer.parentElement);

        particle.style.cssText = `
            position: absolute;
            left: ${x}px;
            top: ${y}px;
            width: ${size}px;
            height: ${size}px;
            background: hsla(${hue}, 70%, 60%, 0.8);
            border-radius: 50%;
            pointer-events: none;
            box-shadow: 0 0 ${size * 2}px hsla(${hue}, 70%, 60%, 0.5);
            transform: translate(-50%, -50%);
        `;

        data.particleContainer.appendChild(particle);

        const particleData = {
            element: particle,
            x, y,
            vx: (Math.random() - 0.5) * 3,
            vy: (Math.random() - 0.5) * 3 - 1,
            life: 1,
            decay: 0.02 + Math.random() * 0.02
        };

        data.state.particles.push(particleData);
    }

    getProviderHue(card) {
        const provider = card.dataset?.provider;
        const hues = {
            claude: 280,
            gemini: 220,
            codex: 160,
            kimi: 40
        };
        return hues[provider] || 280;
    }

    startAnimation() {
        const animate = () => {
            this.cards.forEach((data, card) => {
                const { state, particleContainer } = data;

                // Smooth rotation interpolation
                state.rotateX += (state.targetRotateX - state.rotateX) * 0.1;
                state.rotateY += (state.targetRotateY - state.rotateY) * 0.1;

                // Apply transform
                card.style.transform = `
                    perspective(1000px)
                    rotateX(${state.rotateX}deg)
                    rotateY(${state.rotateY}deg)
                    scale(${state.isHovered ? 1.05 : 1})
                `;

                // Update particles
                state.particles = state.particles.filter(p => {
                    p.x += p.vx;
                    p.y += p.vy;
                    p.vy += 0.05; // Gravity
                    p.life -= p.decay;

                    p.element.style.left = `${p.x}px`;
                    p.element.style.top = `${p.y}px`;
                    p.element.style.opacity = p.life.toString();
                    p.element.style.transform = `translate(-50%, -50%) scale(${p.life})`;

                    if (p.life <= 0) {
                        p.element.remove();
                        return false;
                    }
                    return true;
                });
            });

            this.animationId = requestAnimationFrame(animate);
        };

        animate();
    }

    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        this.cards.clear();
    }
}

// Auto-initialize
const particleCards = new ParticleCardEngine();
window.particleCards = particleCards;

export { ParticleCardEngine };
export default particleCards;
