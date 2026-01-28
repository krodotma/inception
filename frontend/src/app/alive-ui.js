/**
 * ALIVE UI Controller - RHEOMODE KINESIS
 * 
 * Makes every interaction cause motion:
 * - Magnetic buttons that follow cursor
 * - 3D card tilt on mouse move
 * - Parallax layers
 * - Cursor glow trail
 * - Squishy press feedback
 */

class AliveUI {
    constructor(options = {}) {
        this.options = {
            enableCursorGlow: true,
            enableMagneticButtons: true,
            enable3DTilt: true,
            enableParallax: true,
            ...options
        };

        this.mouseX = 0;
        this.mouseY = 0;
        this.cursorGlow = null;

        this.init();
    }

    init() {
        // Track mouse globally
        document.addEventListener('mousemove', (e) => this.handleMouseMove(e));

        // Cursor glow
        if (this.options.enableCursorGlow) {
            this.createCursorGlow();
        }

        // Magnetic buttons
        if (this.options.enableMagneticButtons) {
            this.initMagneticButtons();
        }

        // 3D Tilt cards
        if (this.options.enable3DTilt) {
            this.init3DTilt();
        }

        // Parallax
        if (this.options.enableParallax) {
            this.initParallax();
        }

        console.log('[AliveUI] Initialized - UI is now alive ✨');
    }

    handleMouseMove(e) {
        this.mouseX = e.clientX;
        this.mouseY = e.clientY;

        // Update cursor glow position
        if (this.cursorGlow) {
            this.cursorGlow.style.left = `${e.clientX}px`;
            this.cursorGlow.style.top = `${e.clientY}px`;
        }

        // Update CSS custom properties for parallax
        document.documentElement.style.setProperty('--mouse-x', e.clientX - window.innerWidth / 2);
        document.documentElement.style.setProperty('--mouse-y', e.clientY - window.innerHeight / 2);
    }

    createCursorGlow() {
        this.cursorGlow = document.createElement('div');
        this.cursorGlow.className = 'alive-cursor-glow';
        document.body.appendChild(this.cursorGlow);
    }

    initMagneticButtons() {
        const buttons = document.querySelectorAll('.alive-btn-magnetic, .demo-trigger');

        buttons.forEach(btn => {
            btn.addEventListener('mousemove', (e) => {
                const rect = btn.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;

                const deltaX = (e.clientX - centerX) * 0.2;
                const deltaY = (e.clientY - centerY) * 0.2;

                btn.style.transform = `translate(${deltaX}px, ${deltaY}px) scale(1.02)`;
            });

            btn.addEventListener('mouseleave', () => {
                btn.style.transform = '';
            });
        });
    }

    init3DTilt() {
        const cards = document.querySelectorAll('.alive-card-3d, .provider-card');

        cards.forEach(card => {
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;

                const rotateY = ((e.clientX - centerX) / (rect.width / 2)) * 8;
                const rotateX = -((e.clientY - centerY) / (rect.height / 2)) * 8;

                card.style.setProperty('--rotateX', `${rotateX}deg`);
                card.style.setProperty('--rotateY', `${rotateY}deg`);
                card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.02)`;
            });

            card.addEventListener('mouseleave', () => {
                card.style.transform = '';
                card.style.setProperty('--rotateX', '0deg');
                card.style.setProperty('--rotateY', '0deg');
            });
        });
    }

    initParallax() {
        const containers = document.querySelectorAll('.alive-parallax-container');

        containers.forEach(container => {
            container.addEventListener('mousemove', (e) => {
                const rect = container.getBoundingClientRect();
                const x = (e.clientX - rect.left - rect.width / 2) / 10;
                const y = (e.clientY - rect.top - rect.height / 2) / 10;

                container.style.setProperty('--mouse-x', x);
                container.style.setProperty('--mouse-y', y);
            });
        });
    }

    /**
     * Add stagger animation to children
     */
    stagger(container, options = {}) {
        const { delay = 80, animation = 'alive-stagger-in' } = options;
        const children = container.children;

        Array.from(children).forEach((child, i) => {
            child.style.animationDelay = `${i * delay}ms`;
            child.classList.add(animation);
        });
    }

    /**
     * Trigger bounce animation
     */
    bounce(element) {
        element.style.animation = 'none';
        element.offsetHeight; // Trigger reflow
        element.style.animation = 'alive-stagger-in 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
    }

    /**
     * Create ripple effect at click position
     */
    ripple(element, e) {
        const rect = element.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const ripple = document.createElement('span');
        ripple.className = 'alive-ripple-effect';
        ripple.style.cssText = `
            position: absolute;
            left: ${x}px;
            top: ${y}px;
            width: 0;
            height: 0;
            background: radial-gradient(circle, rgba(255,255,255,0.4) 0%, transparent 60%);
            border-radius: 50%;
            transform: translate(-50%, -50%);
            pointer-events: none;
            animation: alive-ripple-expand 0.6s ease-out forwards;
        `;

        element.style.position = 'relative';
        element.style.overflow = 'hidden';
        element.appendChild(ripple);

        setTimeout(() => ripple.remove(), 600);
    }

    destroy() {
        if (this.cursorGlow) {
            this.cursorGlow.remove();
        }
    }
}

// Add ripple keyframes
const style = document.createElement('style');
style.textContent = `
    @keyframes alive-ripple-expand {
        to {
            width: 500px;
            height: 500px;
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Auto-initialize
document.addEventListener('DOMContentLoaded', () => {
    window.aliveUI = new AliveUI();
});

export { AliveUI };
export default AliveUI;
