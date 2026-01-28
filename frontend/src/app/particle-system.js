/**
 * OPUS-2 ULTRATHINK: Particle System Engine
 * 
 * Advanced particle effects:
 * - Provider connection particles
 * - Cursor trail particles
 * - Status change morphs
 * - Loading orbital system
 * - Success celebration
 */

class ParticleSystem {
    constructor(canvas) {
        this.canvas = typeof canvas === 'string' ? document.querySelector(canvas) : canvas;
        if (!this.canvas) {
            this.canvas = this.createCanvas();
        }
        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.emitters = [];
        this.running = false;
        this.mouseX = 0;
        this.mouseY = 0;

        this.providerColors = {
            claude: '#8B5CF6',
            gemini: '#4285F4',
            codex: '#10B981',
            kimi: '#F59E0B',
            default: '#FFFFFF'
        };

        this.resize();
        window.addEventListener('resize', () => this.resize());
        document.addEventListener('mousemove', (e) => {
            this.mouseX = e.clientX;
            this.mouseY = e.clientY;
        });
    }

    createCanvas() {
        const canvas = document.createElement('canvas');
        canvas.id = 'particle-canvas';
        canvas.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 9998;
        `;
        document.body.appendChild(canvas);
        return canvas;
    }

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    // ========================================
    // PROVIDER CONNECTION PARTICLES
    // ========================================

    emitConnectionParticles(provider, x, y) {
        const color = this.providerColors[provider] || this.providerColors.default;

        // Burst of particles
        for (let i = 0; i < 30; i++) {
            const angle = (Math.PI * 2 / 30) * i + Math.random() * 0.3;
            const speed = 3 + Math.random() * 5;

            this.particles.push({
                x, y,
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed,
                size: 3 + Math.random() * 4,
                color: color,
                alpha: 1,
                decay: 0.02 + Math.random() * 0.02,
                type: 'connection'
            });
        }

        // Ring explosion
        this.particles.push({
            x, y,
            size: 10,
            maxSize: 100,
            color: color,
            alpha: 0.8,
            decay: 0.03,
            type: 'ring'
        });

        this.start();
    }

    // ========================================
    // CURSOR TRAIL PARTICLES
    // ========================================

    startCursorTrail() {
        this.cursorTrailActive = true;

        const emit = () => {
            if (!this.cursorTrailActive) return;

            // Emit particle at cursor
            this.particles.push({
                x: this.mouseX + (Math.random() - 0.5) * 10,
                y: this.mouseY + (Math.random() - 0.5) * 10,
                vx: (Math.random() - 0.5) * 2,
                vy: (Math.random() - 0.5) * 2 - 1,
                size: 2 + Math.random() * 3,
                color: `hsl(${260 + Math.random() * 40}, 70%, 60%)`,
                alpha: 0.8,
                decay: 0.03,
                type: 'trail'
            });

            requestAnimationFrame(emit);
        };

        emit();
        this.start();
    }

    stopCursorTrail() {
        this.cursorTrailActive = false;
    }

    // ========================================
    // ORBITAL LOADING PARTICLES
    // ========================================

    startLoadingOrbit(centerX, centerY, radius = 50) {
        const orbitId = Date.now();

        // Create orbiting particles
        for (let i = 0; i < 8; i++) {
            this.emitters.push({
                id: orbitId,
                type: 'orbit',
                centerX, centerY,
                radius,
                angle: (Math.PI * 2 / 8) * i,
                speed: 0.03,
                color: Object.values(this.providerColors)[i % 4]
            });
        }

        this.start();
        return orbitId;
    }

    stopLoadingOrbit(orbitId) {
        this.emitters = this.emitters.filter(e => e.id !== orbitId);
    }

    // ========================================
    // STATUS CHANGE MORPH
    // ========================================

    morphStatus(fromProvider, toProvider, x, y) {
        const fromColor = this.providerColors[fromProvider] || '#888';
        const toColor = this.providerColors[toProvider] || '#FFF';

        // Dissolve old status
        for (let i = 0; i < 20; i++) {
            this.particles.push({
                x: x + (Math.random() - 0.5) * 40,
                y: y + (Math.random() - 0.5) * 20,
                vx: (Math.random() - 0.5) * 3,
                vy: -Math.random() * 2 - 1,
                size: 4 + Math.random() * 4,
                color: fromColor,
                alpha: 1,
                decay: 0.04,
                type: 'morph-out'
            });
        }

        // Coalesce new status (delayed)
        setTimeout(() => {
            for (let i = 0; i < 20; i++) {
                const startX = x + (Math.random() - 0.5) * 100;
                const startY = y + (Math.random() - 0.5) * 100;

                this.particles.push({
                    x: startX,
                    y: startY,
                    targetX: x + (Math.random() - 0.5) * 40,
                    targetY: y + (Math.random() - 0.5) * 20,
                    size: 4 + Math.random() * 4,
                    color: toColor,
                    alpha: 0,
                    fadeIn: 0.05,
                    type: 'morph-in'
                });
            }
        }, 200);

        this.start();
    }

    // ========================================
    // ANIMATION LOOP
    // ========================================

    start() {
        if (this.running) return;
        this.running = true;
        this.animate();
    }

    animate() {
        if (!this.running) return;

        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // Update emitters
        this.emitters.forEach(emitter => {
            if (emitter.type === 'orbit') {
                emitter.angle += emitter.speed;
                const x = emitter.centerX + Math.cos(emitter.angle) * emitter.radius;
                const y = emitter.centerY + Math.sin(emitter.angle) * emitter.radius;

                // Draw orbiting particle
                this.ctx.beginPath();
                this.ctx.arc(x, y, 4, 0, Math.PI * 2);
                this.ctx.fillStyle = emitter.color;
                this.ctx.fill();

                // Trail
                this.particles.push({
                    x, y,
                    vx: 0, vy: 0,
                    size: 3,
                    color: emitter.color,
                    alpha: 0.5,
                    decay: 0.08,
                    type: 'orbit-trail'
                });
            }
        });

        // Update particles
        this.particles = this.particles.filter(p => {
            // Update based on type
            switch (p.type) {
                case 'connection':
                case 'trail':
                case 'orbit-trail':
                    p.x += p.vx;
                    p.y += p.vy;
                    p.vy += 0.1; // Gravity
                    p.alpha -= p.decay;
                    break;

                case 'ring':
                    p.size += (p.maxSize - p.size) * 0.1;
                    p.alpha -= p.decay;
                    break;

                case 'morph-out':
                    p.x += p.vx;
                    p.y += p.vy;
                    p.alpha -= p.decay;
                    p.size *= 0.95;
                    break;

                case 'morph-in':
                    p.x += (p.targetX - p.x) * 0.1;
                    p.y += (p.targetY - p.y) * 0.1;
                    p.alpha = Math.min(1, p.alpha + p.fadeIn);
                    if (p.alpha >= 1) p.decay = 0.05;
                    if (p.decay) p.alpha -= p.decay;
                    break;
            }

            // Draw
            if (p.type === 'ring') {
                this.ctx.beginPath();
                this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                this.ctx.strokeStyle = p.color;
                this.ctx.globalAlpha = p.alpha;
                this.ctx.lineWidth = 3;
                this.ctx.stroke();
                this.ctx.globalAlpha = 1;
            } else {
                this.ctx.beginPath();
                this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                this.ctx.fillStyle = p.color;
                this.ctx.globalAlpha = p.alpha;
                this.ctx.fill();
                this.ctx.globalAlpha = 1;
            }

            return p.alpha > 0;
        });

        // Continue if particles or emitters exist
        if (this.particles.length > 0 || this.emitters.length > 0) {
            requestAnimationFrame(() => this.animate());
        } else {
            this.running = false;
        }
    }

    destroy() {
        this.running = false;
        this.particles = [];
        this.emitters = [];
        if (this.canvas.parentNode) {
            this.canvas.remove();
        }
    }
}

// Auto-initialize
const particleSystem = new ParticleSystem();
window.particleSystem = particleSystem;

export { ParticleSystem };
export default particleSystem;
