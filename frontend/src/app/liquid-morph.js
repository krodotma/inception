/**
 * OPUS-1 ITERATION 2: Liquid Morph Engine
 * 
 * Fluid transformations between states:
 * - SVG path morphing
 * - Metaball effects
 * - Liquid button fills
 * - Blob shape animations
 * - Gooey filter effects
 */

class LiquidMorphEngine {
    constructor() {
        this.morphingElements = new Map();
        this.blobCanvas = null;
        this.blobCtx = null;
        this.blobs = [];
        this.gooeyFilter = null;

        this.init();
    }

    init() {
        this.createGooeyFilter();
        this.setupLiquidButtons();
        this.setupBlobBackground();
        console.log('[LiquidMorphEngine] 🌊 Fluid systems active');
    }

    // ========================================
    // GOOEY SVG FILTER
    // ========================================

    createGooeyFilter() {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('style', 'position: absolute; width: 0; height: 0;');
        svg.innerHTML = `
            <defs>
                <filter id="gooey-filter">
                    <feGaussianBlur in="SourceGraphic" stdDeviation="10" result="blur" />
                    <feColorMatrix in="blur" mode="matrix" 
                        values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 19 -9" 
                        result="gooey" />
                    <feComposite in="SourceGraphic" in2="gooey" operator="atop" />
                </filter>
                <filter id="liquid-distort">
                    <feTurbulence type="fractalNoise" baseFrequency="0.01" numOctaves="3" result="noise" />
                    <feDisplacementMap in="SourceGraphic" in2="noise" scale="20" xChannelSelector="R" yChannelSelector="G" />
                </filter>
                <filter id="glass-blur">
                    <feGaussianBlur stdDeviation="4" />
                    <feColorMatrix type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 0.7 0"/>
                </filter>
            </defs>
        `;
        document.body.appendChild(svg);
        this.gooeyFilter = svg;
    }

    // ========================================
    // LIQUID BUTTON FILLS
    // ========================================

    setupLiquidButtons() {
        const buttons = document.querySelectorAll('.liquid-fill-btn, .auth-button');

        buttons.forEach(btn => {
            // Create liquid fill element
            const fill = document.createElement('div');
            fill.className = 'liquid-fill';
            fill.style.cssText = `
                position: absolute;
                bottom: 0;
                left: 0;
                width: 100%;
                height: 0%;
                background: linear-gradient(
                    180deg,
                    rgba(255, 255, 255, 0.3) 0%,
                    rgba(255, 255, 255, 0.1) 100%
                );
                transition: height 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                pointer-events: none;
                z-index: 0;
            `;

            // Create wave effect
            const wave = document.createElement('div');
            wave.className = 'liquid-wave';
            wave.style.cssText = `
                position: absolute;
                top: -5px;
                left: 0;
                width: 200%;
                height: 10px;
                background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 120' preserveAspectRatio='none'%3E%3Cpath d='M0,0V46.29c47.79,22.2,103.59,32.17,158,28,70.36-5.37,136.33-33.31,206.8-37.5C438.64,32.43,512.34,53.67,583,72.05c69.27,18,138.3,24.88,209.4,13.08,36.15-6,69.85-17.84,104.45-29.34C989.49,25,1113-14.29,1200,52.47V0Z' fill='rgba(255,255,255,0.2)'/%3E%3C/svg%3E");
                background-size: 50% 100%;
                animation: wave-move 3s linear infinite;
            `;

            fill.appendChild(wave);
            btn.style.position = 'relative';
            btn.style.overflow = 'hidden';
            btn.insertBefore(fill, btn.firstChild);

            // Hover events
            btn.addEventListener('mouseenter', () => {
                fill.style.height = '100%';
            });

            btn.addEventListener('mouseleave', () => {
                fill.style.height = '0%';
            });
        });

        // Add wave animation CSS
        if (!document.querySelector('#liquid-keyframes')) {
            const style = document.createElement('style');
            style.id = 'liquid-keyframes';
            style.textContent = `
                @keyframes wave-move {
                    0% { transform: translateX(0); }
                    100% { transform: translateX(-50%); }
                }
            `;
            document.head.appendChild(style);
        }
    }

    // ========================================
    // METABALL BLOB BACKGROUND
    // ========================================

    setupBlobBackground() {
        this.blobCanvas = document.createElement('canvas');
        this.blobCanvas.id = 'blob-canvas';
        this.blobCanvas.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: -1;
            opacity: 0.3;
        `;

        document.body.insertBefore(this.blobCanvas, document.body.firstChild);
        this.blobCtx = this.blobCanvas.getContext('2d');

        this.resizeCanvas();
        window.addEventListener('resize', () => this.resizeCanvas());

        // Create initial blobs
        this.createBlobs();
        this.animateBlobs();
    }

    resizeCanvas() {
        this.blobCanvas.width = window.innerWidth;
        this.blobCanvas.height = window.innerHeight;
    }

    createBlobs() {
        const colors = [
            'rgba(139, 92, 246, 0.6)',   // Claude purple
            'rgba(66, 133, 244, 0.6)',    // Gemini blue
            'rgba(16, 185, 129, 0.6)',    // Codex green
            'rgba(245, 158, 11, 0.6)'     // Kimi amber
        ];

        for (let i = 0; i < 4; i++) {
            this.blobs.push({
                x: Math.random() * window.innerWidth,
                y: Math.random() * window.innerHeight,
                radius: 80 + Math.random() * 120,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                color: colors[i],
                phase: Math.random() * Math.PI * 2
            });
        }
    }

    animateBlobs() {
        const { width, height } = this.blobCanvas;
        const ctx = this.blobCtx;

        ctx.clearRect(0, 0, width, height);

        // Update blob positions
        this.blobs.forEach(blob => {
            blob.x += blob.vx;
            blob.y += blob.vy;
            blob.phase += 0.02;

            // Bounce off edges
            if (blob.x < 0 || blob.x > width) blob.vx *= -1;
            if (blob.y < 0 || blob.y > height) blob.vy *= -1;

            // Breathing radius
            const breathe = Math.sin(blob.phase) * 20;

            // Draw blob with gradient
            const gradient = ctx.createRadialGradient(
                blob.x, blob.y, 0,
                blob.x, blob.y, blob.radius + breathe
            );
            gradient.addColorStop(0, blob.color);
            gradient.addColorStop(1, 'transparent');

            ctx.beginPath();
            ctx.arc(blob.x, blob.y, blob.radius + breathe, 0, Math.PI * 2);
            ctx.fillStyle = gradient;
            ctx.fill();
        });

        requestAnimationFrame(() => this.animateBlobs());
    }

    // ========================================
    // SVG PATH MORPHING
    // ========================================

    morphPath(element, fromPath, toPath, duration = 500) {
        const path = element.querySelector('path') || element;
        const startTime = performance.now();

        const fromPoints = this.parsePath(fromPath);
        const toPoints = this.parsePath(toPath);

        const animate = (time) => {
            const elapsed = time - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = this.easeOutElastic(progress);

            const currentPoints = fromPoints.map((point, i) => ({
                x: point.x + (toPoints[i].x - point.x) * eased,
                y: point.y + (toPoints[i].y - point.y) * eased
            }));

            path.setAttribute('d', this.pointsToPath(currentPoints));

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    parsePath(d) {
        // Simplified path parsing for demo
        const points = [];
        const matches = d.match(/[\d.]+/g) || [];
        for (let i = 0; i < matches.length; i += 2) {
            points.push({ x: parseFloat(matches[i]), y: parseFloat(matches[i + 1] || 0) });
        }
        return points;
    }

    pointsToPath(points) {
        if (points.length === 0) return '';
        let d = `M ${points[0].x} ${points[0].y}`;
        for (let i = 1; i < points.length; i++) {
            d += ` L ${points[i].x} ${points[i].y}`;
        }
        return d + ' Z';
    }

    easeOutElastic(x) {
        const c4 = (2 * Math.PI) / 3;
        return x === 0
            ? 0
            : x === 1
                ? 1
                : Math.pow(2, -10 * x) * Math.sin((x * 10 - 0.75) * c4) + 1;
    }

    // ========================================
    // CARD MORPH TRANSITION
    // ========================================

    morphCard(fromCard, toCard) {
        const fromRect = fromCard.getBoundingClientRect();
        const toRect = toCard.getBoundingClientRect();

        // Create morph element
        const morph = document.createElement('div');
        morph.className = 'card-morph';
        morph.style.cssText = `
            position: fixed;
            left: ${fromRect.left}px;
            top: ${fromRect.top}px;
            width: ${fromRect.width}px;
            height: ${fromRect.height}px;
            background: ${getComputedStyle(fromCard).background};
            border-radius: ${getComputedStyle(fromCard).borderRadius};
            z-index: 10000;
            pointer-events: none;
            filter: url(#gooey-filter);
        `;

        document.body.appendChild(morph);

        // Animate morph
        morph.animate([
            {
                left: `${fromRect.left}px`,
                top: `${fromRect.top}px`,
                width: `${fromRect.width}px`,
                height: `${fromRect.height}px`
            },
            {
                left: `${toRect.left}px`,
                top: `${toRect.top}px`,
                width: `${toRect.width}px`,
                height: `${toRect.height}px`
            }
        ], {
            duration: 600,
            easing: 'cubic-bezier(0.16, 1, 0.3, 1)'
        }).onfinish = () => morph.remove();
    }

    destroy() {
        if (this.gooeyFilter) this.gooeyFilter.remove();
        if (this.blobCanvas) this.blobCanvas.remove();
    }
}

// Auto-initialize
const liquidMorph = new LiquidMorphEngine();
window.liquidMorph = liquidMorph;

export { LiquidMorphEngine };
export default liquidMorph;
