// ════════════════════════════════════════════════════════════════════════════
// VISUALIZER 5: DIALECTICAL TREE
// Branching claims with support/contradiction relationships
// ════════════════════════════════════════════════════════════════════════════

import { DataContracts } from '../lib/mock-data.js';

export class DialecticalTreeVisualizer {
    constructor(container) {
        this.container = container;
        this.data = DataContracts.getDialecticalTree();
        this.canvas = null;
        this.ctx = null;
        this.nodes = [];
        this.hoveredNode = null;
    }

    init() {
        this.canvas = document.createElement('canvas');
        this.canvas.width = this.container.clientWidth;
        this.canvas.height = this.container.clientHeight;
        this.canvas.style.cssText = 'position: absolute; top: 0; left: 0;';
        this.container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');

        this.calculateTreeLayout();
        this.bindEvents();
        this.animate();
    }

    calculateTreeLayout() {
        const w = this.canvas.width;
        const h = this.canvas.height;
        const rootX = w / 2;
        const rootY = 80;

        // Build tree structure from dialectical edges
        const claims = this.data.claims;
        const edges = this.data.dialecticalEdges;

        // Find root claims (not targeted by anything)
        const targetedIds = new Set(edges.filter(e => e.type === 'supports').map(e => e.target));
        const roots = claims.filter(c => !targetedIds.has(c.id));

        // Layout tree
        const levelHeight = 120;
        const nodeWidth = 180;

        this.nodes = [];

        // Position roots at top
        roots.forEach((claim, i) => {
            const x = rootX + (i - (roots.length - 1) / 2) * (nodeWidth + 40);
            this.addNodeToTree(claim, x, rootY, 0);
        });

        // Add supporting claims below
        claims.filter(c => !roots.includes(c)).forEach((claim, i) => {
            const edge = edges.find(e => e.target === claim.id && e.type === 'supports');
            const parent = this.nodes.find(n => n.claim.id === edge?.source);

            if (parent) {
                const childCount = this.nodes.filter(n => n.parentId === parent.claim.id).length;
                const x = parent.x + (childCount - 0.5) * 100;
                this.addNodeToTree(claim, x, parent.y + levelHeight, parent.depth + 1, parent.claim.id);
            } else {
                // Orphan claim - position to side
                this.addNodeToTree(claim, 100 + i * 200, h - 150, 2);
            }
        });
    }

    addNodeToTree(claim, x, y, depth, parentId = null) {
        // Check if dialectical (has contradiction)
        const tension = this.data.tensions.find(t => t.id === claim.id);

        this.nodes.push({
            claim,
            x, y, depth,
            parentId,
            width: 160,
            height: 60,
            isDialectical: !!tension,
            dialecticalTarget: tension?.dialectical?.target
        });
    }

    bindEvents() {
        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            this.hoveredNode = this.nodes.find(n =>
                x >= n.x - n.width / 2 && x <= n.x + n.width / 2 &&
                y >= n.y - n.height / 2 && y <= n.y + n.height / 2
            );
        });
    }

    render(time) {
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;

        // Background
        ctx.fillStyle = '#050508';
        ctx.fillRect(0, 0, w, h);

        // Draw dialectical tension lines first (behind everything)
        ctx.lineWidth = 3;
        this.nodes.filter(n => n.isDialectical).forEach(node => {
            const target = this.nodes.find(n => n.claim.id === node.dialecticalTarget);
            if (target) {
                // Animated zigzag tension line
                ctx.strokeStyle = '#ff6b9d';
                ctx.setLineDash([5, 5]);
                ctx.beginPath();
                ctx.moveTo(node.x, node.y);

                // Lightning bolt effect
                const midX = (node.x + target.x) / 2;
                const midY = (node.y + target.y) / 2;
                const offset = Math.sin(time * 0.003) * 20;

                ctx.lineTo(midX + offset, midY - 10);
                ctx.lineTo(midX - offset, midY + 10);
                ctx.lineTo(target.x, target.y);
                ctx.stroke();
                ctx.setLineDash([]);

                // "CONTRADICTION" label
                ctx.fillStyle = 'rgba(255, 107, 157, 0.8)';
                ctx.font = 'bold 10px "Space Grotesk", sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText('⚡ CONTRADICTION', midX, midY);
            }
        });

        // Draw support edges
        ctx.strokeStyle = 'rgba(100, 255, 218, 0.4)';
        ctx.lineWidth = 2;
        this.nodes.forEach(node => {
            if (node.parentId) {
                const parent = this.nodes.find(n => n.claim.id === node.parentId);
                if (parent) {
                    ctx.beginPath();
                    ctx.moveTo(parent.x, parent.y + parent.height / 2);
                    ctx.lineTo(node.x, node.y - node.height / 2);
                    ctx.stroke();

                    // Arrow head
                    const angle = Math.atan2(
                        node.y - node.height / 2 - parent.y - parent.height / 2,
                        node.x - parent.x
                    );
                    const arrowSize = 8;
                    ctx.fillStyle = '#64ffda';
                    ctx.beginPath();
                    ctx.moveTo(node.x, node.y - node.height / 2);
                    ctx.lineTo(
                        node.x - arrowSize * Math.cos(angle - 0.3),
                        node.y - node.height / 2 - arrowSize * Math.sin(angle - 0.3)
                    );
                    ctx.lineTo(
                        node.x - arrowSize * Math.cos(angle + 0.3),
                        node.y - node.height / 2 - arrowSize * Math.sin(angle + 0.3)
                    );
                    ctx.closePath();
                    ctx.fill();
                }
            }
        });

        // Draw claim nodes
        this.nodes.forEach(node => {
            const isHovered = node === this.hoveredNode;
            const x = node.x - node.width / 2;
            const y = node.y - node.height / 2;

            // Node background
            const conf = node.claim.confidence || 0.5;
            ctx.fillStyle = node.isDialectical
                ? `rgba(255, 107, 157, ${0.3 + conf * 0.4})`
                : `rgba(100, 255, 218, ${0.2 + conf * 0.3})`;

            ctx.beginPath();
            ctx.roundRect(x, y, node.width, node.height, 12);
            ctx.fill();

            // Border
            ctx.strokeStyle = node.isDialectical ? '#ff6b9d' : '#64ffda';
            ctx.lineWidth = isHovered ? 3 : 1;
            ctx.stroke();

            // Confidence bar
            const barWidth = node.width - 20;
            ctx.fillStyle = 'rgba(0,0,0,0.3)';
            ctx.fillRect(x + 10, y + node.height - 12, barWidth, 6);
            ctx.fillStyle = conf > 0.8 ? '#64ffda' : conf > 0.5 ? '#ffd93d' : '#ff6b9d';
            ctx.fillRect(x + 10, y + node.height - 12, barWidth * conf, 6);

            // Claim text
            ctx.fillStyle = '#e6f1ff';
            ctx.font = '11px "Space Grotesk", sans-serif';
            ctx.textAlign = 'center';
            const text = node.claim.text || node.claim.statement || 'Claim';
            ctx.fillText(text.substring(0, 30) + (text.length > 30 ? '...' : ''), node.x, node.y);
        });

        // Legend
        ctx.fillStyle = 'rgba(136, 146, 176, 0.7)';
        ctx.font = '12px "Space Grotesk", sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText('→ Supports   ⚡ Contradicts', 20, h - 20);
    }

    animate() {
        this.render(Date.now());
        requestAnimationFrame(() => this.animate());
    }

    dispose() {
        this.canvas?.remove();
    }
}

export default DialecticalTreeVisualizer;
