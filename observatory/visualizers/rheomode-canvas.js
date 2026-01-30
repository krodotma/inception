// ════════════════════════════════════════════════════════════════════════════
// VISUALIZER 10: RHEOMODE CANVAS
// Dynamic process visualization - knowledge as flowing verb-forms
// Inspired by David Bohm's Rheomode concept
// ════════════════════════════════════════════════════════════════════════════

import { DataContracts } from '../lib/mock-data.js';

export class RheomodeCanvasVisualizer {
    constructor(container) {
        this.container = container;
        this.data = DataContracts.getRheomodeCanvas();
        this.canvas = null;
        this.ctx = null;
        this.particles = [];
        this.flows = [];
    }

    init() {
        this.canvas = document.createElement('canvas');
        this.canvas.width = this.container.clientWidth;
        this.canvas.height = this.container.clientHeight;
        this.canvas.style.cssText = 'position: absolute; top: 0; left: 0;';
        this.container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');

        this.initializeParticles();
        this.initializeFlows();
        this.animate();
    }

    initializeParticles() {
        // Create flowing particles that represent knowledge in motion
        for (let i = 0; i < 200; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                vx: (Math.random() - 0.5) * 2,
                vy: (Math.random() - 0.5) * 2,
                size: 1 + Math.random() * 2,
                life: Math.random(),
                hue: 160 + Math.random() * 40, // Cyan range
            });
        }
    }

    initializeFlows() {
        // Convert process steps into flow fields
        const w = this.canvas.width;
        const h = this.canvas.height;

        this.data.processes.forEach(process => {
            this.flows.push({
                id: process.id,
                x: 100 + (process.order - 1) * 180,
                y: 150 + process.y,
                action: process.action,
                duration: process.duration,
                targetX: 100 + process.order * 180,
                targetY: 150 + process.y,
            });
        });
    }

    updateParticles(time) {
        const w = this.canvas.width;
        const h = this.canvas.height;

        this.particles.forEach(p => {
            // Flow field influence
            let fx = 0, fy = 0;
            this.flows.forEach(flow => {
                const dx = flow.x - p.x;
                const dy = flow.y - p.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < 150 && dist > 10) {
                    const force = 0.5 / dist;
                    fx += (dx / dist) * force;
                    fy += (dy / dist) * force;
                }
            });

            // Apply forces
            p.vx += fx + Math.sin(time * 0.001 + p.y * 0.01) * 0.05;
            p.vy += fy + Math.cos(time * 0.001 + p.x * 0.01) * 0.05;

            // Damping
            p.vx *= 0.98;
            p.vy *= 0.98;

            // Update position
            p.x += p.vx;
            p.y += p.vy;

            // Wrap around
            if (p.x < 0) p.x = w;
            if (p.x > w) p.x = 0;
            if (p.y < 0) p.y = h;
            if (p.y > h) p.y = 0;

            // Life cycle
            p.life -= 0.002;
            if (p.life <= 0) {
                p.x = Math.random() * w;
                p.y = Math.random() * h;
                p.life = 1;
            }
        });
    }

    render(time) {
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;

        // Fade trail effect
        ctx.fillStyle = 'rgba(3, 3, 8, 0.1)';
        ctx.fillRect(0, 0, w, h);

        // Draw flow connection curves
        ctx.strokeStyle = 'rgba(100, 255, 218, 0.1)';
        ctx.lineWidth = 40;
        ctx.lineCap = 'round';

        this.data.flows.forEach(flow => {
            const from = this.flows.find(f => f.id === flow.from);
            const to = this.flows.find(f => f.id === flow.to);

            if (from && to) {
                ctx.beginPath();
                ctx.moveTo(from.x, from.y);
                ctx.lineTo(to.x, to.y);
                ctx.stroke();
            }
        });

        // Draw particles
        this.particles.forEach(p => {
            const alpha = p.life * 0.8;
            ctx.fillStyle = `hsla(${p.hue}, 100%, 70%, ${alpha})`;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fill();
        });

        // Draw process nodes (verbs in motion)
        this.flows.forEach((flow, i) => {
            const pulsePhase = (time * 0.002 + i * 0.5) % (Math.PI * 2);
            const pulse = 1 + Math.sin(pulsePhase) * 0.1;
            const radius = 30 * pulse;

            // Outer glow
            const glowGrad = ctx.createRadialGradient(flow.x, flow.y, 0, flow.x, flow.y, radius * 2);
            glowGrad.addColorStop(0, 'rgba(189, 147, 249, 0.3)');
            glowGrad.addColorStop(1, 'rgba(189, 147, 249, 0)');
            ctx.fillStyle = glowGrad;
            ctx.beginPath();
            ctx.arc(flow.x, flow.y, radius * 2, 0, Math.PI * 2);
            ctx.fill();

            // Core
            const coreGrad = ctx.createRadialGradient(flow.x, flow.y, 0, flow.x, flow.y, radius);
            coreGrad.addColorStop(0, 'rgba(100, 255, 218, 0.9)');
            coreGrad.addColorStop(0.7, 'rgba(189, 147, 249, 0.7)');
            coreGrad.addColorStop(1, 'rgba(189, 147, 249, 0)');
            ctx.fillStyle = coreGrad;
            ctx.beginPath();
            ctx.arc(flow.x, flow.y, radius, 0, Math.PI * 2);
            ctx.fill();

            // Action text (verb-form)
            ctx.fillStyle = '#e6f1ff';
            ctx.font = '10px "Space Grotesk", sans-serif';
            ctx.textAlign = 'center';
            const words = flow.action.split(' ').slice(0, 4).join(' ');
            ctx.fillText(words + (flow.action.split(' ').length > 4 ? '...' : ''), flow.x, flow.y + radius + 15);
        });

        // Rheomode title
        ctx.fillStyle = 'rgba(189, 147, 249, 0.8)';
        ctx.font = 'bold 24px "Space Grotesk", sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('R H E O M O D E', w / 2, 50);

        ctx.fillStyle = 'rgba(136, 146, 176, 0.6)';
        ctx.font = 'italic 12px "Space Grotesk", sans-serif';
        ctx.fillText('Knowledge as flowing verb-forms', w / 2, 75);

        // Process indicator
        ctx.textAlign = 'left';
        ctx.fillStyle = 'rgba(100, 255, 218, 0.7)';
        ctx.font = '11px "Space Grotesk", sans-serif';
        ctx.fillText('Active Processes: ' + this.flows.length, 20, h - 20);
    }

    animate() {
        const time = Date.now();
        this.updateParticles(time);
        this.render(time);
        requestAnimationFrame(() => this.animate());
    }

    dispose() {
        this.canvas?.remove();
    }
}

export default RheomodeCanvasVisualizer;
