// ════════════════════════════════════════════════════════════════════════════
// VISUALIZER 3: SOURCE WEB
// Radial spider graph showing provenance flow from sources to claims
// ════════════════════════════════════════════════════════════════════════════

import { DataContracts } from '../lib/mock-data.js';

export class SourceWebVisualizer {
    constructor(container) {
        this.container = container;
        this.data = DataContracts.getProvenanceWeb();
        this.canvas = null;
        this.ctx = null;
    }

    init() {
        this.canvas = document.createElement('canvas');
        this.canvas.width = this.container.clientWidth;
        this.canvas.height = this.container.clientHeight;
        this.canvas.style.cssText = 'position: absolute; top: 0; left: 0;';
        this.container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');

        this.calculateLayout();
        this.animate();
    }

    calculateLayout() {
        const cx = this.canvas.width / 2;
        const cy = this.canvas.height / 2;
        const sourceRadius = 180;
        const claimRadius = 100;

        // Position sources in outer ring
        this.sourcePositions = this.data.sources.map((source, i) => {
            const angle = (i / this.data.sources.length) * Math.PI * 2 - Math.PI / 2;
            return {
                ...source,
                x: cx + Math.cos(angle) * sourceRadius,
                y: cy + Math.sin(angle) * sourceRadius,
                angle
            };
        });

        // Position claims in inner ring
        this.claimPositions = this.data.claims.map((claim, i) => {
            const angle = (i / this.data.claims.length) * Math.PI * 2 - Math.PI / 2;
            return {
                ...claim,
                x: cx + Math.cos(angle) * claimRadius,
                y: cy + Math.sin(angle) * claimRadius,
                angle
            };
        });
    }

    render(time) {
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;
        const cx = w / 2;
        const cy = h / 2;

        // Clear with radial gradient
        const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, Math.max(w, h) / 2);
        grad.addColorStop(0, '#0a0a15');
        grad.addColorStop(1, '#050508');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, w, h);

        // Draw web rings
        ctx.strokeStyle = 'rgba(136, 146, 176, 0.1)';
        ctx.lineWidth = 1;
        [100, 140, 180].forEach(r => {
            ctx.beginPath();
            ctx.arc(cx, cy, r, 0, Math.PI * 2);
            ctx.stroke();
        });

        // Draw radial lines
        for (let i = 0; i < 12; i++) {
            const angle = (i / 12) * Math.PI * 2;
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.lineTo(cx + Math.cos(angle) * 200, cy + Math.sin(angle) * 200);
            ctx.stroke();
        }

        // Draw provenance edges (animated flow)
        this.data.credibilityFlow.forEach((flow, fi) => {
            const source = this.sourcePositions.find(s => s.id === flow.source.id);
            if (!source) return;

            flow.claims.forEach((claim, ci) => {
                const claimPos = this.claimPositions.find(c => c.id === claim.id);
                if (!claimPos) return;

                // Animated gradient along edge
                const edgeGrad = ctx.createLinearGradient(source.x, source.y, claimPos.x, claimPos.y);
                const pulsePhase = (time * 0.001 + fi * 0.5 + ci * 0.3) % 1;

                edgeGrad.addColorStop(Math.max(0, pulsePhase - 0.2), 'rgba(255, 217, 61, 0.1)');
                edgeGrad.addColorStop(pulsePhase, 'rgba(100, 255, 218, 0.8)');
                edgeGrad.addColorStop(Math.min(1, pulsePhase + 0.2), 'rgba(255, 217, 61, 0.1)');

                ctx.strokeStyle = edgeGrad;
                ctx.lineWidth = 2 * flow.source.credibility;
                ctx.beginPath();
                ctx.moveTo(source.x, source.y);

                // Curved path through center
                const midX = cx + (source.x + claimPos.x - 2 * cx) * 0.3;
                const midY = cy + (source.y + claimPos.y - 2 * cy) * 0.3;
                ctx.quadraticCurveTo(midX, midY, claimPos.x, claimPos.y);
                ctx.stroke();
            });
        });

        // Draw sources (outer nodes)
        this.sourcePositions.forEach(source => {
            const credColor = source.credibility > 0.8 ? '#64ffda' :
                source.credibility > 0.6 ? '#ffd93d' : '#ff6b9d';

            // Source icon based on type
            ctx.fillStyle = credColor;
            ctx.beginPath();

            if (source.type === 'web') {
                // Globe icon
                ctx.arc(source.x, source.y, 15, 0, Math.PI * 2);
                ctx.fill();
                ctx.strokeStyle = '#050508';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.ellipse(source.x, source.y, 15, 8, 0, 0, Math.PI * 2);
                ctx.stroke();
                ctx.beginPath();
                ctx.moveTo(source.x, source.y - 15);
                ctx.lineTo(source.x, source.y + 15);
                ctx.stroke();
            } else if (source.type === 'video') {
                // Play icon
                ctx.moveTo(source.x - 10, source.y - 12);
                ctx.lineTo(source.x + 12, source.y);
                ctx.lineTo(source.x - 10, source.y + 12);
                ctx.closePath();
                ctx.fill();
            } else {
                // Document icon
                ctx.fillRect(source.x - 10, source.y - 12, 20, 24);
                ctx.fillStyle = '#050508';
                for (let i = 0; i < 3; i++) {
                    ctx.fillRect(source.x - 6, source.y - 8 + i * 8, 12, 2);
                }
            }

            // Label
            ctx.fillStyle = 'rgba(204, 214, 246, 0.9)';
            ctx.font = '10px "Space Grotesk", sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(source.title.substring(0, 15), source.x, source.y + 30);

            // Credibility indicator
            ctx.fillStyle = credColor;
            ctx.fillText(`${Math.round(source.credibility * 100)}%`, source.x, source.y + 42);
        });

        // Draw claims (inner nodes)
        this.claimPositions.forEach(claim => {
            const confAlpha = claim.confidence;

            ctx.fillStyle = `rgba(100, 255, 218, ${confAlpha})`;
            ctx.beginPath();
            ctx.arc(claim.x, claim.y, 8 + claim.confidence * 8, 0, Math.PI * 2);
            ctx.fill();

            // Glow
            const glowGrad = ctx.createRadialGradient(claim.x, claim.y, 0, claim.x, claim.y, 20);
            glowGrad.addColorStop(0, 'rgba(100, 255, 218, 0.3)');
            glowGrad.addColorStop(1, 'rgba(100, 255, 218, 0)');
            ctx.fillStyle = glowGrad;
            ctx.beginPath();
            ctx.arc(claim.x, claim.y, 25, 0, Math.PI * 2);
            ctx.fill();
        });

        // Center hub
        ctx.fillStyle = '#bd93f9';
        ctx.beginPath();
        ctx.arc(cx, cy, 20, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = '#050508';
        ctx.font = 'bold 10px "Space Grotesk", sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('TRUTH', cx, cy + 4);
    }

    animate() {
        this.render(Date.now());
        requestAnimationFrame(() => this.animate());
    }

    dispose() {
        this.canvas?.remove();
    }
}

export default SourceWebVisualizer;
