// ════════════════════════════════════════════════════════════════════════════
// DIALECTICAL SYNTHESIS ENGINE — Purpose-Aligned Cognitive Tool
//
// COGNITIVE PURPOSE: Navigate contradictions to synthesize truth
// VISUAL METAPHOR: Thesis/Antithesis as opposing magnetic poles,
//                  Synthesis emerges from the tension field between them
// ANTI-CORPORATE: No panels, no symmetry — raw dialectical tension
// ════════════════════════════════════════════════════════════════════════════

import { DataContracts } from '../lib/mock-data.js';

// ═══════════════════════════════════════════════════════════════════════════
// PURPOSE: This is a REASONING TOOL, not a chart.
//
// When you see opposing claims:
//   - You should FEEL the tension between them (visual stress)
//   - You should SEE the confidence weight of each position
//   - You should TRACE the sources backing each side
//   - You should DISCOVER where synthesis might emerge
//
// The visual language is:
//   - Opposition: Claims push against each other, creating stress lines
//   - Weight: Confidence manifests as visual mass/gravity
//   - Sources: Root tendrils anchoring each position
//   - Synthesis: The emergent calm in the storm — resolution space
// ═══════════════════════════════════════════════════════════════════════════

export class DialecticalSynthesisEngine {
    constructor(container) {
        this.container = container;
        this.data = DataContracts.getDialecticalTree();
        this.canvas = null;
        this.ctx = null;
        this.dialecticalPairs = [];
        this.selectedPair = null;
        this.time = 0;
    }

    init() {
        this.canvas = document.createElement('canvas');
        this.canvas.width = this.container.clientWidth;
        this.canvas.height = this.container.clientHeight;
        this.canvas.style.cssText = 'position:absolute;top:0;left:0;cursor:crosshair;';
        this.container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');

        this.extractDialecticalPairs();
        this.setupInteraction();
        this.animate();
    }

    extractDialecticalPairs() {
        // Find claims that contradict each other
        const tensions = this.data.tensions || [];
        const claims = this.data.claims || [];

        tensions.forEach(claim => {
            if (claim.dialectical?.type === 'contradicts') {
                const opposingClaim = claims.find(c => c.id === claim.dialectical.target);
                if (opposingClaim) {
                    this.dialecticalPairs.push({
                        thesis: opposingClaim,  // Original claim
                        antithesis: claim,      // Contradicting claim
                        tensionStrength: Math.abs(opposingClaim.confidence - claim.confidence),
                        // Synthesis potential: higher when confidences are similar (genuine debate)
                        synthesisPotential: 1 - Math.abs(opposingClaim.confidence - claim.confidence),
                        position: {
                            x: this.canvas.width / 2,
                            y: this.canvas.height / 2
                        }
                    });
                }
            }
        });

        // If no explicit dialectical pairs, create from any contradicting edges
        if (this.dialecticalPairs.length === 0) {
            const contradictEdges = this.data.dialecticalEdges?.filter(e => e.type === 'contradicts') || [];
            contradictEdges.forEach(edge => {
                const thesis = claims.find(c => c.id === edge.source);
                const antithesis = claims.find(c => c.id === edge.target);
                if (thesis && antithesis) {
                    this.dialecticalPairs.push({
                        thesis,
                        antithesis,
                        tensionStrength: 0.5,
                        synthesisPotential: 0.5,
                        position: { x: this.canvas.width / 2, y: 150 + this.dialecticalPairs.length * 200 }
                    });
                }
            });
        }
    }

    setupInteraction() {
        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            this.mouseX = e.clientX - rect.left;
            this.mouseY = e.clientY - rect.top;
        });

        this.canvas.addEventListener('click', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            // Check if clicked on a dialectical pair
            this.dialecticalPairs.forEach(pair => {
                const dist = Math.sqrt(
                    Math.pow(x - pair.position.x, 2) +
                    Math.pow(y - pair.position.y, 2)
                );
                if (dist < 150) {
                    this.selectedPair = pair;
                    console.log('[Dialectic] Selected pair:');
                    console.log('  Thesis:', pair.thesis.text);
                    console.log('  Antithesis:', pair.antithesis.text);
                    console.log('  Synthesis potential:', pair.synthesisPotential);
                }
            });
        });
    }

    render() {
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;
        this.time = Date.now() * 0.001;

        // Background: Not black, not white — the gray of uncertainty
        const bgGrad = ctx.createRadialGradient(w / 2, h / 2, 0, w / 2, h / 2, Math.max(w, h) * 0.7);
        bgGrad.addColorStop(0, '#0a0810');
        bgGrad.addColorStop(1, '#000004');
        ctx.fillStyle = bgGrad;
        ctx.fillRect(0, 0, w, h);

        // Tension field background — interference pattern
        this.renderTensionField();

        // Render each dialectical pair
        this.dialecticalPairs.forEach((pair, i) => {
            this.renderDialecticalPair(pair, i);
        });

        // Instructions (not a corporate tooltip)
        ctx.fillStyle = 'rgba(100, 100, 120, 0.5)';
        ctx.font = '11px monospace';
        ctx.fillText('click pair to examine · synthesis emerges from tension', 20, h - 20);
    }

    renderTensionField() {
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;

        // Interference pattern from all dialectical pairs
        const resolution = 20;

        for (let x = 0; x < w; x += resolution) {
            for (let y = 0; y < h; y += resolution) {
                let totalTension = 0;

                this.dialecticalPairs.forEach(pair => {
                    const dx = x - pair.position.x;
                    const dy = y - pair.position.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);

                    // Tension waves emanate from each pair
                    const wave = Math.sin(dist * 0.05 - this.time * 2) * pair.tensionStrength;
                    totalTension += wave / (1 + dist * 0.01);
                });

                if (Math.abs(totalTension) > 0.1) {
                    const alpha = Math.abs(totalTension) * 0.3;
                    ctx.fillStyle = totalTension > 0
                        ? `rgba(180, 60, 80, ${alpha})`   // Thesis-leaning
                        : `rgba(60, 80, 180, ${alpha})`;  // Antithesis-leaning
                    ctx.fillRect(x, y, resolution, resolution);
                }
            }
        }
    }

    renderDialecticalPair(pair, index) {
        const ctx = this.ctx;
        const cx = pair.position.x;
        const cy = pair.position.y;
        const spread = 120 + pair.tensionStrength * 50;

        const thesisX = cx - spread;
        const antithesisX = cx + spread;

        // Thesis side (left)
        this.renderClaim(pair.thesis, thesisX, cy, 'thesis');

        // Antithesis side (right)
        this.renderClaim(pair.antithesis, antithesisX, cy, 'antithesis');

        // Tension lines between them — stress fractures
        const tensionLines = 5 + Math.floor(pair.tensionStrength * 10);
        ctx.lineWidth = 1;

        for (let i = 0; i < tensionLines; i++) {
            const t = i / tensionLines;
            const offsetY = (t - 0.5) * 80;
            const jitter = Math.sin(this.time * 3 + i) * pair.tensionStrength * 10;

            // Gradient from thesis color to antithesis color
            const grad = ctx.createLinearGradient(thesisX + 40, cy, antithesisX - 40, cy);
            grad.addColorStop(0, `rgba(180, 60, 80, ${0.3 + pair.tensionStrength * 0.3})`);
            grad.addColorStop(0.5, `rgba(200, 180, 100, ${0.5})`); // Yellow tension zone
            grad.addColorStop(1, `rgba(60, 80, 180, ${0.3 + pair.tensionStrength * 0.3})`);

            ctx.strokeStyle = grad;
            ctx.beginPath();
            ctx.moveTo(thesisX + 40, cy + offsetY);

            // Jagged tension path
            const midX = cx;
            ctx.lineTo(midX - 20 + jitter, cy + offsetY + jitter * 0.5);
            ctx.lineTo(midX + jitter * 0.7, cy + offsetY - jitter * 0.3);
            ctx.lineTo(midX + 20 - jitter * 0.5, cy + offsetY + jitter * 0.4);
            ctx.lineTo(antithesisX - 40, cy + offsetY);
            ctx.stroke();
        }

        // Synthesis zone — the calm in the center (if potential is high)
        if (pair.synthesisPotential > 0.3) {
            const synthRadius = 20 + pair.synthesisPotential * 30;
            const pulse = Math.sin(this.time * 2) * 0.3 + 0.7;

            const synthGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, synthRadius);
            synthGrad.addColorStop(0, `rgba(100, 255, 180, ${0.4 * pulse * pair.synthesisPotential})`);
            synthGrad.addColorStop(0.5, `rgba(180, 255, 200, ${0.2 * pulse * pair.synthesisPotential})`);
            synthGrad.addColorStop(1, 'rgba(100, 255, 180, 0)');

            ctx.fillStyle = synthGrad;
            ctx.beginPath();
            ctx.arc(cx, cy, synthRadius, 0, Math.PI * 2);
            ctx.fill();

            // Synthesis label
            ctx.fillStyle = `rgba(100, 255, 180, ${0.6 + pulse * 0.4})`;
            ctx.font = 'italic 12px serif';
            ctx.textAlign = 'center';
            ctx.fillText('synthesis?', cx, cy + 4);
        }

        // Selection highlight
        if (pair === this.selectedPair) {
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);
            ctx.beginPath();
            ctx.ellipse(cx, cy, spread + 60, 80, 0, 0, Math.PI * 2);
            ctx.stroke();
            ctx.setLineDash([]);
        }
    }

    renderClaim(claim, x, y, type) {
        const ctx = this.ctx;
        const confidence = claim.confidence || 0.5;
        const radius = 30 + confidence * 20;

        // Colors based on type
        const colors = type === 'thesis'
            ? { primary: '#b43c50', secondary: '#8a2a3a', text: '#ffcccc' }
            : { primary: '#3c50b4', secondary: '#2a3a8a', text: '#ccccff' };

        // Claim mass — visualized as density
        const layers = 3 + Math.floor(confidence * 5);
        for (let i = layers; i >= 0; i--) {
            const layerRadius = radius * (1 - i * 0.1);
            const alpha = 0.1 + (i / layers) * 0.3;

            ctx.fillStyle = i === 0 ? colors.primary : `rgba(${type === 'thesis' ? '180,60,80' : '60,80,180'}, ${alpha})`;
            ctx.beginPath();
            ctx.arc(x, y, layerRadius, 0, Math.PI * 2);
            ctx.fill();
        }

        // Confidence ring
        ctx.strokeStyle = colors.secondary;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(x, y, radius + 5, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * confidence);
        ctx.stroke();

        // Claim text (abbreviated)
        ctx.fillStyle = colors.text;
        ctx.font = '10px monospace';
        ctx.textAlign = 'center';
        const text = claim.text || claim.statement || 'Claim';
        const words = text.split(' ').slice(0, 4).join(' ');
        ctx.fillText(words, x, y - radius - 15);
        ctx.fillText(words.length < text.length ? '...' : '', x, y - radius - 5);

        // Confidence label
        ctx.fillStyle = 'rgba(255,255,255,0.7)';
        ctx.font = 'bold 11px monospace';
        ctx.fillText(`${Math.round(confidence * 100)}%`, x, y + 4);

        // Source tendrils (roots anchoring the claim)
        if (claim.sourceIds?.length) {
            claim.sourceIds.forEach((sourceId, i) => {
                const angle = Math.PI + (i - claim.sourceIds.length / 2) * 0.3;
                const tendrilLength = 30 + Math.random() * 20;

                ctx.strokeStyle = `rgba(${type === 'thesis' ? '180,100,100' : '100,100,180'}, 0.4)`;
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(x, y + radius);
                ctx.lineTo(
                    x + Math.cos(angle) * tendrilLength,
                    y + radius + Math.sin(angle) * tendrilLength
                );
                ctx.stroke();
            });
        }
    }

    animate() {
        this.render();
        requestAnimationFrame(() => this.animate());
    }

    dispose() {
        this.canvas?.remove();
    }
}

export default DialecticalSynthesisEngine;
