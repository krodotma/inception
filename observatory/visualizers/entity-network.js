// ════════════════════════════════════════════════════════════════════════════
// VISUALIZER 8: ENTITY NETWORK MATRIX
// Heatmap showing relationship strengths between entities
// ════════════════════════════════════════════════════════════════════════════

import { DataContracts } from '../lib/mock-data.js';

export class EntityNetworkVisualizer {
    constructor(container) {
        this.container = container;
        this.data = DataContracts.getEntityMatrix();
        this.canvas = null;
        this.ctx = null;
        this.hoveredCell = null;
    }

    init() {
        this.canvas = document.createElement('canvas');
        this.canvas.width = this.container.clientWidth;
        this.canvas.height = this.container.clientHeight;
        this.canvas.style.cssText = 'position: absolute; top: 0; left: 0;';
        this.container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');

        this.calculateLayout();
        this.bindEvents();
        this.animate();
    }

    calculateLayout() {
        const padding = 120;
        const availableWidth = this.canvas.width - padding * 2;
        const availableHeight = this.canvas.height - padding * 2;

        const n = this.data.entities.length;
        this.cellSize = Math.min(availableWidth / n, availableHeight / n, 80);
        this.startX = (this.canvas.width - n * this.cellSize) / 2;
        this.startY = (this.canvas.height - n * this.cellSize) / 2 + 40;
    }

    bindEvents() {
        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const col = Math.floor((x - this.startX) / this.cellSize);
            const row = Math.floor((y - this.startY) / this.cellSize);

            if (col >= 0 && col < this.data.entities.length &&
                row >= 0 && row < this.data.entities.length) {
                this.hoveredCell = { row, col };
            } else {
                this.hoveredCell = null;
            }
        });
    }

    heatColor(value, time) {
        // Gradient from void to crystalline
        if (value === 0) return 'rgba(20, 20, 30, 0.8)';

        // Pulse based on strength
        const pulse = 1 + Math.sin(time * 0.003 * value) * 0.2;
        const r = Math.floor(100 + value * 155 * pulse);
        const g = Math.floor(255 * value * pulse);
        const b = Math.floor(218 + (1 - value) * 37);

        return `rgba(${r}, ${g}, ${b}, ${0.3 + value * 0.7})`;
    }

    render(time) {
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;
        const entities = this.data.entities;
        const matrix = this.data.matrix;
        const n = entities.length;

        // Background
        ctx.fillStyle = '#050508';
        ctx.fillRect(0, 0, w, h);

        // Title
        ctx.fillStyle = '#bd93f9';
        ctx.font = 'bold 20px "Space Grotesk", sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('Entity Relationship Matrix', w / 2, 40);

        // Draw matrix cells
        for (let row = 0; row < n; row++) {
            for (let col = 0; col < n; col++) {
                const x = this.startX + col * this.cellSize;
                const y = this.startY + row * this.cellSize;
                const value = matrix[row][col];

                const isHovered = this.hoveredCell &&
                    (this.hoveredCell.row === row || this.hoveredCell.col === col);
                const isExact = this.hoveredCell &&
                    this.hoveredCell.row === row && this.hoveredCell.col === col;

                // Cell background
                ctx.fillStyle = this.heatColor(value, time);
                ctx.beginPath();
                ctx.roundRect(x + 2, y + 2, this.cellSize - 4, this.cellSize - 4, 4);
                ctx.fill();

                // Highlight row/col on hover
                if (isHovered && !isExact) {
                    ctx.strokeStyle = 'rgba(189, 147, 249, 0.5)';
                    ctx.lineWidth = 1;
                    ctx.stroke();
                }

                // Highlight exact cell
                if (isExact) {
                    ctx.strokeStyle = '#64ffda';
                    ctx.lineWidth = 2;
                    ctx.stroke();
                }

                // Value text (if significant)
                if (value > 0) {
                    ctx.fillStyle = value > 0.5 ? '#050508' : '#e6f1ff';
                    ctx.font = '11px "Space Grotesk", sans-serif';
                    ctx.textAlign = 'center';
                    ctx.fillText(value.toFixed(1), x + this.cellSize / 2, y + this.cellSize / 2 + 4);
                }

                // Diagonal (self) = entity icon
                if (row === col) {
                    ctx.fillStyle = '#bd93f9';
                    ctx.beginPath();
                    ctx.arc(x + this.cellSize / 2, y + this.cellSize / 2, 8, 0, Math.PI * 2);
                    ctx.fill();
                }
            }
        }

        // Row labels (left)
        ctx.textAlign = 'right';
        ctx.fillStyle = '#e6f1ff';
        ctx.font = '12px "Space Grotesk", sans-serif';
        entities.forEach((entity, i) => {
            const y = this.startY + i * this.cellSize + this.cellSize / 2 + 4;
            const isHighlighted = this.hoveredCell && this.hoveredCell.row === i;
            ctx.fillStyle = isHighlighted ? '#64ffda' : '#e6f1ff';
            ctx.fillText(entity.name, this.startX - 10, y);
        });

        // Column labels (top, rotated)
        entities.forEach((entity, i) => {
            const x = this.startX + i * this.cellSize + this.cellSize / 2;
            const isHighlighted = this.hoveredCell && this.hoveredCell.col === i;

            ctx.save();
            ctx.translate(x, this.startY - 10);
            ctx.rotate(-Math.PI / 4);
            ctx.textAlign = 'left';
            ctx.fillStyle = isHighlighted ? '#64ffda' : '#e6f1ff';
            ctx.fillText(entity.name, 0, 0);
            ctx.restore();
        });

        // Tooltip
        if (this.hoveredCell) {
            const { row, col } = this.hoveredCell;
            const value = matrix[row][col];
            const e1 = entities[row].name;
            const e2 = entities[col].name;

            const tooltipX = this.startX + col * this.cellSize + this.cellSize;
            const tooltipY = this.startY + row * this.cellSize;

            ctx.fillStyle = 'rgba(30, 30, 40, 0.95)';
            ctx.beginPath();
            ctx.roundRect(tooltipX + 10, tooltipY - 20, 180, 50, 8);
            ctx.fill();
            ctx.strokeStyle = '#64ffda';
            ctx.lineWidth = 1;
            ctx.stroke();

            ctx.fillStyle = '#e6f1ff';
            ctx.textAlign = 'left';
            ctx.font = 'bold 11px "Space Grotesk", sans-serif';
            ctx.fillText(`${e1} ↔ ${e2}`, tooltipX + 20, tooltipY - 2);
            ctx.font = '11px "Space Grotesk", sans-serif';
            ctx.fillStyle = value > 0.5 ? '#64ffda' : value > 0 ? '#ffd93d' : '#8892b0';
            ctx.fillText(`Strength: ${value.toFixed(2)}`, tooltipX + 20, tooltipY + 16);
        }

        // Legend
        const legendX = 20;
        const legendY = h - 40;
        ctx.fillStyle = '#8892b0';
        ctx.font = '10px "Space Grotesk", sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText('Connection Strength:', legendX, legendY);

        const gradWidth = 100;
        const grad = ctx.createLinearGradient(legendX + 110, 0, legendX + 110 + gradWidth, 0);
        grad.addColorStop(0, 'rgba(20, 20, 30, 0.8)');
        grad.addColorStop(0.5, 'rgba(100, 255, 218, 0.5)');
        grad.addColorStop(1, 'rgba(100, 255, 218, 1)');
        ctx.fillStyle = grad;
        ctx.fillRect(legendX + 110, legendY - 10, gradWidth, 15);

        ctx.fillStyle = '#8892b0';
        ctx.fillText('0', legendX + 110, legendY + 15);
        ctx.fillText('1', legendX + 110 + gradWidth - 5, legendY + 15);
    }

    animate() {
        this.render(Date.now());
        requestAnimationFrame(() => this.animate());
    }

    dispose() {
        this.canvas?.remove();
    }
}

export default EntityNetworkVisualizer;
