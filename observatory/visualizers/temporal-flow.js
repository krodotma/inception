// ════════════════════════════════════════════════════════════════════════════
// VISUALIZER 1: TEMPORAL FLOW
// Allen's Interval Algebra timeline for knowledge versioning
// ════════════════════════════════════════════════════════════════════════════

import { DataContracts } from '../lib/mock-data.js';

export class TemporalFlowVisualizer {
    constructor(container) {
        this.container = container;
        this.data = DataContracts.getTemporalData();
        this.canvas = null;
        this.ctx = null;
        this.timeline = { start: new Date('2010-01-01'), end: new Date('2025-12-31') };
    }

    init() {
        this.canvas = document.createElement('canvas');
        this.canvas.width = this.container.clientWidth;
        this.canvas.height = this.container.clientHeight;
        this.canvas.style.cssText = 'position: absolute; top: 0; left: 0;';
        this.container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');

        this.render();
        this.animate();
    }

    dateToX(date) {
        const d = new Date(date);
        const range = this.timeline.end - this.timeline.start;
        return ((d - this.timeline.start) / range) * this.canvas.width;
    }

    render() {
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;

        // Clear with void gradient
        const grad = ctx.createLinearGradient(0, 0, 0, h);
        grad.addColorStop(0, '#050508');
        grad.addColorStop(1, '#0a0a10');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, w, h);

        // Draw timeline axis
        ctx.strokeStyle = 'rgba(100, 255, 218, 0.3)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(50, h - 50);
        ctx.lineTo(w - 50, h - 50);
        ctx.stroke();

        // Draw year markers
        ctx.fillStyle = 'rgba(136, 146, 176, 0.8)';
        ctx.font = '12px "Space Grotesk", sans-serif';
        for (let year = 2010; year <= 2025; year++) {
            const x = this.dateToX(`${year}-01-01`);
            ctx.fillText(year, x - 15, h - 30);
            ctx.beginPath();
            ctx.moveTo(x, h - 50);
            ctx.lineTo(x, h - 55);
            ctx.stroke();
        }

        // Draw entity intervals as flowing rivers
        const entityY = 100;
        const entitySpacing = 60;

        this.data.entities.forEach((entity, i) => {
            const y = entityY + i * entitySpacing;
            const startX = this.dateToX(entity.intervals[0].from);
            const endX = entity.intervals[0].until ? this.dateToX(entity.intervals[0].until) : w - 50;

            // Confidence-based opacity
            const alpha = entity.confidence;

            // Draw interval bar with gradient
            const barGrad = ctx.createLinearGradient(startX, 0, endX, 0);
            barGrad.addColorStop(0, `rgba(100, 255, 218, ${alpha * 0.3})`);
            barGrad.addColorStop(0.5, `rgba(189, 147, 249, ${alpha * 0.5})`);
            barGrad.addColorStop(1, `rgba(100, 255, 218, ${alpha * 0.3})`);

            ctx.fillStyle = barGrad;
            ctx.beginPath();
            ctx.roundRect(startX, y - 15, endX - startX, 30, 8);
            ctx.fill();

            // Entity label
            ctx.fillStyle = '#e6f1ff';
            ctx.font = 'bold 14px "Space Grotesk", sans-serif';
            ctx.fillText(entity.name, startX + 10, y + 5);

            // Uncertainty visualization (fuzzy edges)
            if (entity.uncertainty) {
                ctx.strokeStyle = `rgba(255, 107, 157, ${entity.uncertainty.epistemic})`;
                ctx.lineWidth = 3;
                ctx.setLineDash([5, 5]);
                ctx.strokeRect(startX, y - 15, endX - startX, 30);
                ctx.setLineDash([]);
            }
        });

        // Draw timeline events as pulses
        this.data.events.forEach(event => {
            const x = this.dateToX(event.timestamp);
            const y = h - 80;

            ctx.beginPath();
            ctx.arc(x, y, 8, 0, Math.PI * 2);
            ctx.fillStyle = event.type === 'creation' ? '#64ffda' :
                event.type === 'supersession' ? '#ffd93d' : '#ff6b9d';
            ctx.fill();

            // Event label
            ctx.save();
            ctx.translate(x, y - 15);
            ctx.rotate(-Math.PI / 4);
            ctx.fillStyle = 'rgba(204, 214, 246, 0.7)';
            ctx.font = '10px "Space Grotesk", sans-serif';
            ctx.fillText(event.event.substring(0, 25), 0, 0);
            ctx.restore();
        });
    }

    animate() {
        // Subtle flowing animation
        const time = Date.now() * 0.001;
        // Animation logic would update here
        requestAnimationFrame(() => this.animate());
    }

    dispose() {
        this.canvas?.remove();
    }
}

export default TemporalFlowVisualizer;
