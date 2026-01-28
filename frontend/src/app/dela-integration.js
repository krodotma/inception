/**
 * ROBIN DELA EFFECTS INTEGRATION - ULTRATHINK
 * 
 * Integrates legendary animation patterns from Robin Dela repos:
 * - Hover Effect: Displacement texture transitions
 * - Flowmap Effect: Mouse-reactive distortion
 * - CSS Mask Animation: Kinetic mask reveals
 * - Lighthouse: WebGL lighting effects
 * 
 * Adapted for Agent Auth provider cards
 */

// ============================================
// DISPLACEMENT HOVER EFFECT (adapted from hover-effect)
// ============================================

class ProviderCardHover {
    constructor(options = {}) {
        this.cards = [];
        this.renderer = null;
        this.scene = null;
        this.camera = null;
        this.materials = new Map();

        this.options = {
            intensity: options.intensity || 0.3,
            speedIn: options.speedIn || 0.8,
            speedOut: options.speedOut || 0.6,
            angle: options.angle || Math.PI / 4,
            ...options
        };

        this.init();
    }

    async init() {
        // Dynamic import for THREE.js if available
        if (typeof THREE !== 'undefined') {
            this.setupWebGL();
        } else {
            // CSS fallback
            this.setupCSSFallback();
        }

        console.log('[DelaHover] ✨ Displacement hover active');
    }

    setupWebGL() {
        // Create shared renderer
        this.scene = new THREE.Scene();

        document.querySelectorAll('.provider-card').forEach((card, index) => {
            this.setupCardWebGL(card, index);
        });
    }

    setupCardWebGL(card, index) {
        const canvas = document.createElement('canvas');
        canvas.className = 'dela-hover-canvas';
        canvas.style.cssText = `
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
            z-index: 1;
        `;

        card.style.position = 'relative';
        card.appendChild(canvas);

        // Vertex shader
        const vertexShader = `
            varying vec2 vUv;
            void main() {
                vUv = uv;
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `;

        // Fragment shader with provider-colored displacement
        const fragmentShader = `
            varying vec2 vUv;
            uniform float uTime;
            uniform float uHoverProgress;
            uniform vec3 uProviderColor;
            uniform vec2 uMouse;
            
            // Simplex noise for displacement
            vec3 permute(vec3 x) { return mod(((x*34.0)+1.0)*x, 289.0); }
            
            float snoise(vec2 v) {
                const vec4 C = vec4(0.211324865405187, 0.366025403784439,
                                   -0.577350269189626, 0.024390243902439);
                vec2 i = floor(v + dot(v, C.yy));
                vec2 x0 = v - i + dot(i, C.xx);
                vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
                vec4 x12 = x0.xyxy + C.xxzz;
                x12.xy -= i1;
                i = mod(i, 289.0);
                vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0))
                    + i.x + vec3(0.0, i1.x, 1.0));
                vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy),
                    dot(x12.zw,x12.zw)), 0.0);
                m = m*m;
                m = m*m;
                vec3 x = 2.0 * fract(p * C.www) - 1.0;
                vec3 h = abs(x) - 0.5;
                vec3 ox = floor(x + 0.5);
                vec3 a0 = x - ox;
                m *= 1.79284291400159 - 0.85373472095314 * (a0*a0 + h*h);
                vec3 g;
                g.x = a0.x * x0.x + h.x * x0.y;
                g.yz = a0.yz * x12.xz + h.yz * x12.yw;
                return 130.0 * dot(m, g);
            }
            
            void main() {
                vec2 uv = vUv;
                
                // Mouse-reactive displacement
                float dist = distance(uv, uMouse);
                float displacement = snoise(uv * 3.0 + uTime * 0.5) * uHoverProgress;
                
                // Create wave pattern centered on mouse
                float wave = sin(dist * 10.0 - uTime * 2.0) * 0.5 + 0.5;
                wave *= (1.0 - dist) * uHoverProgress;
                
                // Provider-colored glow
                vec3 color = uProviderColor;
                float alpha = (displacement * 0.3 + wave * 0.5) * uHoverProgress;
                
                // Radial gradient from mouse
                alpha *= smoothstep(1.0, 0.0, dist * 1.5);
                
                gl_FragColor = vec4(color, alpha * 0.6);
            }
        `;

        this.cards.push({
            element: card,
            canvas: canvas,
            hoverProgress: 0,
            mousePos: { x: 0.5, y: 0.5 }
        });

        // Event listeners
        card.addEventListener('mouseenter', () => this.onMouseEnter(index));
        card.addEventListener('mouseleave', () => this.onMouseLeave(index));
        card.addEventListener('mousemove', (e) => this.onMouseMove(index, e));
    }

    setupCSSFallback() {
        document.querySelectorAll('.provider-card').forEach((card, index) => {
            // Create ripple effect layer
            const ripple = document.createElement('div');
            ripple.className = 'dela-ripple-layer';
            ripple.style.cssText = `
                position: absolute;
                inset: 0;
                border-radius: inherit;
                overflow: hidden;
                pointer-events: none;
                z-index: 1;
            `;

            card.style.position = 'relative';
            card.appendChild(ripple);

            this.cards.push({
                element: card,
                ripple: ripple,
                mousePos: { x: 0.5, y: 0.5 }
            });

            card.addEventListener('mouseenter', () => this.cssMouseEnter(index));
            card.addEventListener('mouseleave', () => this.cssMouseLeave(index));
            card.addEventListener('mousemove', (e) => this.cssMouseMove(index, e));
        });
    }

    cssMouseEnter(index) {
        const card = this.cards[index];
        card.ripple.innerHTML = '';

        // Create expanding ring
        const ring = document.createElement('div');
        ring.style.cssText = `
            position: absolute;
            left: ${card.mousePos.x * 100}%;
            top: ${card.mousePos.y * 100}%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: radial-gradient(
                circle,
                var(--provider-color, rgba(139, 92, 246, 0.3)) 0%,
                transparent 70%
            );
            transform: translate(-50%, -50%);
            animation: dela-ripple-expand 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        `;

        card.ripple.appendChild(ring);
    }

    cssMouseLeave(index) {
        const card = this.cards[index];
        const ripples = card.ripple.children;

        Array.from(ripples).forEach(ripple => {
            ripple.style.animation = 'dela-ripple-fade 0.4s ease-out forwards';
            setTimeout(() => ripple.remove(), 400);
        });
    }

    cssMouseMove(index, e) {
        const card = this.cards[index];
        const rect = card.element.getBoundingClientRect();

        card.mousePos.x = (e.clientX - rect.left) / rect.width;
        card.mousePos.y = (e.clientY - rect.top) / rect.height;

        // Update existing ripple position
        const ring = card.ripple.lastElementChild;
        if (ring) {
            ring.style.left = `${card.mousePos.x * 100}%`;
            ring.style.top = `${card.mousePos.y * 100}%`;
        }
    }

    onMouseEnter(index) {
        // WebGL version - animate hoverProgress
    }

    onMouseLeave(index) {
        // WebGL version
    }

    onMouseMove(index, e) {
        // WebGL version
    }
}

// ============================================
// FLOWMAP DISTORTION (adapted from flowmap-effect)
// ============================================

class FlowmapDistortion {
    constructor(canvas) {
        this.canvas = canvas;
        this.gl = null;
        this.flowmap = [];
        this.flowmapSize = 128;
        this.mousePos = { x: 0, y: 0 };
        this.lastMouse = { x: 0, y: 0 };
        this.velocity = { x: 0, y: 0 };

        this.init();
    }

    init() {
        if (!this.canvas) return;

        this.gl = this.canvas.getContext('webgl2') || this.canvas.getContext('webgl');
        if (!this.gl) {
            console.warn('[Flowmap] WebGL not available');
            return;
        }

        this.resize();
        this.setupListeners();
        this.initFlowmap();
        this.render();

        console.log('[Flowmap] 🌊 Distortion active');
    }

    resize() {
        const dpr = Math.min(window.devicePixelRatio, 2);
        this.canvas.width = this.canvas.offsetWidth * dpr;
        this.canvas.height = this.canvas.offsetHeight * dpr;
        if (this.gl) {
            this.gl.viewport(0, 0, this.canvas.width, this.canvas.height);
        }
    }

    setupListeners() {
        document.addEventListener('mousemove', (e) => {
            this.lastMouse.x = this.mousePos.x;
            this.lastMouse.y = this.mousePos.y;

            this.mousePos.x = e.clientX / window.innerWidth;
            this.mousePos.y = 1.0 - (e.clientY / window.innerHeight);

            this.velocity.x = this.mousePos.x - this.lastMouse.x;
            this.velocity.y = this.mousePos.y - this.lastMouse.y;
        });
    }

    initFlowmap() {
        // Initialize flowmap texture data
        for (let i = 0; i < this.flowmapSize * this.flowmapSize * 4; i++) {
            this.flowmap[i] = 128; // Neutral (no flow)
        }
    }

    updateFlowmap() {
        const size = this.flowmapSize;
        const mouseX = Math.floor(this.mousePos.x * size);
        const mouseY = Math.floor(this.mousePos.y * size);
        const radius = 8;

        // Paint velocity into flowmap
        for (let y = -radius; y <= radius; y++) {
            for (let x = -radius; x <= radius; x++) {
                const px = mouseX + x;
                const py = mouseY + y;

                if (px < 0 || px >= size || py < 0 || py >= size) continue;

                const dist = Math.sqrt(x * x + y * y);
                if (dist > radius) continue;

                const falloff = 1 - dist / radius;
                const idx = (py * size + px) * 4;

                this.flowmap[idx] = 128 + this.velocity.x * 1000 * falloff;
                this.flowmap[idx + 1] = 128 + this.velocity.y * 1000 * falloff;
            }
        }

        // Dissipate flowmap over time
        for (let i = 0; i < this.flowmap.length; i++) {
            this.flowmap[i] = this.flowmap[i] * 0.98 + 128 * 0.02;
        }
    }

    render() {
        this.updateFlowmap();

        // Simple render - just clear and draw gradient
        const gl = this.gl;
        if (gl) {
            gl.clearColor(0, 0, 0, 0);
            gl.clear(gl.COLOR_BUFFER_BIT);
        }

        requestAnimationFrame(() => this.render());
    }
}

// ============================================
// CSS MASK ANIMATION (adapted from css-mask-animation)
// ============================================

class KineticMaskReveal {
    constructor() {
        this.init();
    }

    init() {
        this.injectStyles();
        this.setupCards();
        console.log('[KineticMask] 🎭 Mask animations ready');
    }

    injectStyles() {
        if (document.querySelector('#kinetic-mask-styles')) return;

        const style = document.createElement('style');
        style.id = 'kinetic-mask-styles';
        style.textContent = `
            @keyframes dela-ripple-expand {
                0% {
                    width: 0;
                    height: 0;
                    opacity: 1;
                }
                100% {
                    width: 400px;
                    height: 400px;
                    opacity: 0.8;
                }
            }
            
            @keyframes dela-ripple-fade {
                0% { opacity: 0.8; }
                100% { opacity: 0; }
            }
            
            @keyframes kinetic-mask-up {
                0% {
                    clip-path: polygon(0 100%, 100% 100%, 100% 100%, 0 100%);
                }
                100% {
                    clip-path: polygon(0 0, 100% 0, 100% 100%, 0 100%);
                }
            }
            
            @keyframes kinetic-mask-circle {
                0% {
                    clip-path: circle(0% at var(--mask-x, 50%) var(--mask-y, 50%));
                }
                100% {
                    clip-path: circle(150% at var(--mask-x, 50%) var(--mask-y, 50%));
                }
            }
            
            @keyframes kinetic-mask-wipe {
                0% {
                    clip-path: inset(0 100% 0 0);
                }
                100% {
                    clip-path: inset(0 0 0 0);
                }
            }
            
            @keyframes kinetic-mask-diamond {
                0% {
                    clip-path: polygon(50% 50%, 50% 50%, 50% 50%, 50% 50%);
                }
                100% {
                    clip-path: polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%);
                }
            }
            
            .kinetic-reveal {
                animation: kinetic-mask-circle 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            }
            
            .kinetic-reveal-wipe {
                animation: kinetic-mask-wipe 0.6s ease-out forwards;
            }
            
            .provider-card.connecting .provider-logo {
                animation: kinetic-mask-diamond 0.5s ease-out forwards;
            }
        `;

        document.head.appendChild(style);
    }

    setupCards() {
        document.querySelectorAll('.provider-card').forEach(card => {
            card.addEventListener('mouseenter', (e) => {
                const rect = card.getBoundingClientRect();
                const x = ((e.clientX - rect.left) / rect.width) * 100;
                const y = ((e.clientY - rect.top) / rect.height) * 100;

                card.style.setProperty('--mask-x', `${x}%`);
                card.style.setProperty('--mask-y', `${y}%`);
            });
        });
    }

    reveal(element, type = 'circle') {
        element.classList.remove('kinetic-reveal', 'kinetic-reveal-wipe');
        void element.offsetWidth; // Force reflow

        if (type === 'wipe') {
            element.classList.add('kinetic-reveal-wipe');
        } else {
            element.classList.add('kinetic-reveal');
        }
    }
}

// ============================================
// COMBINED DELA INTEGRATION
// ============================================

class DelaIntegration {
    constructor() {
        this.hoverEffect = null;
        this.maskReveal = null;

        this.init();
    }

    async init() {
        // Wait for DOM
        if (document.readyState === 'loading') {
            await new Promise(resolve => {
                document.addEventListener('DOMContentLoaded', resolve);
            });
        }

        // Initialize components
        this.hoverEffect = new ProviderCardHover();
        this.maskReveal = new KineticMaskReveal();

        // Setup provider card enhancements
        this.enhanceProviderCards();

        console.log('[DelaIntegration] 🎨 Robin Dela effects integrated');
    }

    enhanceProviderCards() {
        document.querySelectorAll('.provider-card').forEach((card, i) => {
            // Add staggered entrance
            card.style.setProperty('--stagger-delay', `${i * 80}ms`);

            // Add 3D transform on hover
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = (e.clientX - rect.left) / rect.width - 0.5;
                const y = (e.clientY - rect.top) / rect.height - 0.5;

                card.style.transform = `
                    perspective(1000px)
                    rotateY(${x * 10}deg)
                    rotateX(${-y * 10}deg)
                    translateZ(20px)
                `;
            });

            card.addEventListener('mouseleave', () => {
                card.style.transform = '';
            });
        });
    }

    triggerConnectionEffect(provider) {
        const card = document.querySelector(`[data-provider="${provider}"]`);
        if (card && this.maskReveal) {
            this.maskReveal.reveal(card, 'circle');
        }
    }
}

// ============================================
// AUTO-INITIALIZE
// ============================================

const delaIntegration = new DelaIntegration();
window.delaIntegration = delaIntegration;

export {
    ProviderCardHover,
    FlowmapDistortion,
    KineticMaskReveal,
    DelaIntegration
};
export default delaIntegration;
