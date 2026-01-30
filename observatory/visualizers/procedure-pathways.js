// ════════════════════════════════════════════════════════════════════════════
// VISUALIZER 7: PROCEDURE PATHWAYS
// Step-by-step flowchart with duration indicators
// ════════════════════════════════════════════════════════════════════════════

import { DataContracts } from '../lib/mock-data.js';

export class ProcedurePathwaysVisualizer {
    constructor(container) {
        this.container = container;
        this.data = DataContracts.getProcedurePathways();
        this.canvas = null;
        this.ctx = null;
        this.animationPhase = 0;
    }

    init() {
        this.canvas = document.createElement('canvas');
        this.canvas.width = this.container.clientWidth;
        this.canvas.height = this.container.clientHeight;
        this.canvas.style.cssText = 'position: absolute; top: 0; left: 0;';
        this.container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');

        this.animate();
    }

    parseDuration(durationStr) {
        // Parse duration strings like "5-30s", "100-500ms", "instant"
        if (!durationStr || durationStr === 'instant') return 0.1;
        const match = durationStr.match(/(\d+)(?:-(\d+))?(\w+)/);
        if (!match) return 1;

        const min = parseInt(match[1]);
        const max = match[2] ? parseInt(match[2]) : min;
        const unit = match[3];

        const avgSeconds = (min + max) / 2;
        return unit === 'ms' ? avgSeconds / 1000 : avgSeconds;
    }

    render(time) {
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;

        // Background
        const bgGrad = ctx.createLinearGradient(0, 0, w, h);
        bgGrad.addColorStop(0, '#050508');
        bgGrad.addColorStop(1, '#08080f');
        ctx.fillStyle = bgGrad;
        ctx.fillRect(0, 0, w, h);

        const procedures = this.data.procedures;
        const startY = 80;
        const procedureSpacing = 180;
        const stepSpacing = 200;
        const startX = 100;

        procedures.forEach((proc, pi) => {
            const y = startY + pi * procedureSpacing;

            // Procedure header
            ctx.fillStyle = '#bd93f9';
            ctx.font = 'bold 16px "Space Grotesk", sans-serif';
            ctx.fillText(proc.name, startX, y - 40);

            // Confidence indicator
            const confWidth = 100;
            ctx.fillStyle = 'rgba(100, 255, 218, 0.2)';
            ctx.fillRect(startX, y - 30, confWidth, 8);
            ctx.fillStyle = '#64ffda';
            ctx.fillRect(startX, y - 30, confWidth * proc.confidence, 8);
            ctx.fillStyle = '#8892b0';
            ctx.font = '10px "Space Grotesk", sans-serif';
            ctx.fillText(`${Math.round(proc.confidence * 100)}% confidence`, startX + confWidth + 10, y - 23);

            // Draw steps
            proc.steps.forEach((step, si) => {
                const x = startX + si * stepSpacing;
                const stepW = 160;
                const stepH = 80;

                // Duration determines visual weight
                const duration = this.parseDuration(step.duration);
                const pulsePhase = (time * 0.002 + si * 0.5) % (Math.PI * 2);
                const pulse = 1 + Math.sin(pulsePhase) * 0.1;

                // Step box
                const isActive = Math.floor((time * 0.0005) % proc.steps.length) === si;

                ctx.fillStyle = isActive
                    ? 'rgba(100, 255, 218, 0.3)'
                    : 'rgba(136, 146, 176, 0.15)';
                ctx.beginPath();
                ctx.roundRect(x, y, stepW * pulse, stepH, 12);
                ctx.fill();

                // Border
                ctx.strokeStyle = isActive ? '#64ffda' : '#8892b0';
                ctx.lineWidth = isActive ? 2 : 1;
                ctx.stroke();

                // Step number (circle)
                ctx.beginPath();
                ctx.arc(x + 20, y + 20, 12, 0, Math.PI * 2);
                ctx.fillStyle = '#bd93f9';
                ctx.fill();
                ctx.fillStyle = '#050508';
                ctx.font = 'bold 12px "Space Grotesk", sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText(step.order, x + 20, y + 24);
                ctx.textAlign = 'left';

                // Step action text
                ctx.fillStyle = '#e6f1ff';
                ctx.font = '11px "Space Grotesk", sans-serif';
                const words = step.action.split(' ');
                let line = '';
                let lineY = y + 40;
                words.forEach(word => {
                    const testLine = line + word + ' ';
                    if (ctx.measureText(testLine).width > stepW - 20) {
                        ctx.fillText(line, x + 10, lineY);
                        line = word + ' ';
                        lineY += 14;
                    } else {
                        line = testLine;
                    }
                });
                ctx.fillText(line, x + 10, lineY);

                // Duration bar
                const maxDuration = 30; // 30s max for scaling
                const barWidth = Math.min(duration / maxDuration, 1) * (stepW - 20);
                ctx.fillStyle = 'rgba(255, 217, 61, 0.3)';
                ctx.fillRect(x + 10, y + stepH - 15, stepW - 20, 6);
                ctx.fillStyle = duration < 1 ? '#64ffda' : duration < 10 ? '#ffd93d' : '#ff6b9d';
                ctx.fillRect(x + 10, y + stepH - 15, barWidth, 6);

                // Duration label
                ctx.fillStyle = '#8892b0';
                ctx.font = '9px "Space Grotesk", sans-serif';
                ctx.fillText(step.duration, x + 10, y + stepH + 8);

                // Arrow to next step
                if (si < proc.steps.length - 1) {
                    const arrowX = x + stepW + 5;
                    const arrowY = y + stepH / 2;

                    // Animated flow
                    const flowPhase = (time * 0.003 + si) % 1;
                    const flowX = arrowX + flowPhase * (stepSpacing - stepW - 10);

                    ctx.strokeStyle = 'rgba(100, 255, 218, 0.4)';
                    ctx.lineWidth = 2;
                    ctx.beginPath();
                    ctx.moveTo(arrowX, arrowY);
                    ctx.lineTo(arrowX + stepSpacing - stepW - 15, arrowY);
                    ctx.stroke();

                    // Flow particle
                    ctx.beginPath();
                    ctx.arc(flowX, arrowY, 4, 0, Math.PI * 2);
                    ctx.fillStyle = '#64ffda';
                    ctx.fill();

                    // Arrow head
                    ctx.beginPath();
                    const endX = arrowX + stepSpacing - stepW - 10;
                    ctx.moveTo(endX, arrowY);
                    ctx.lineTo(endX - 8, arrowY - 5);
                    ctx.lineTo(endX - 8, arrowY + 5);
                    ctx.closePath();
                    ctx.fillStyle = '#64ffda';
                    ctx.fill();
                }
            });
        });

        // Legend
        ctx.fillStyle = '#8892b0';
        ctx.font = '11px "Space Grotesk", sans-serif';
        ctx.fillText('Duration: ■ instant/fast   ■ medium   ■ slow', 20, h - 20);
    }

    animate() {
        this.render(Date.now());
        requestAnimationFrame(() => this.animate());
    }

    dispose() {
        this.canvas?.remove();
    }
}

export default ProcedurePathwaysVisualizer;
