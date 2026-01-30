// ════════════════════════════════════════════════════════════════════════════
// TEMPORAL QUERY EXPLORER — Purpose-Aligned Cognitive Tool
//
// COGNITIVE PURPOSE: Query knowledge across temporal dimensions
// VISUAL METAPHOR: Time as a river, knowledge as sediment layers,
//                  Allen's 13 interval relations as navigation operators
// ANTI-CORPORATE: No timelines with neat markers — organic temporal flow
// ════════════════════════════════════════════════════════════════════════════

import { DataContracts } from '../lib/mock-data.js';

// ═══════════════════════════════════════════════════════════════════════════
// PURPOSE: This is a TEMPORAL REASONING TOOL.
//
// When you explore time:
//   - You should SEE how knowledge changes and supersedes
//   - You should QUERY using Allen's interval relations (before, during, overlaps...)
//   - You should TRACE the versioning lineage of claims
//   - You should UNDERSTAND temporal uncertainty (fuzzy boundaries)
//
// Allen's 13 Interval Relations:
//   before, after, meets, met-by, overlaps, overlapped-by,
//   starts, started-by, finishes, finished-by, during, contains, equals
//
// The visual language is:
//   - Flow: Time moves like water, not like a ruler
//   - Strata: Knowledge accumulates in layers
//   - Erosion: Old knowledge fades, superseded knowledge dissolves
//   - Navigation: Query operators as filters on the temporal stream
// ═══════════════════════════════════════════════════════════════════════════

export class TemporalQueryExplorer {
    constructor(container) {
        this.container = container;
        this.data = DataContracts.getTemporalData();
        this.canvas = null;
        this.ctx = null;
        this.timeRange = { start: new Date('2010-01-01'), end: new Date('2026-01-01') };
        this.viewStart = new Date('2010-01-01');
        this.viewEnd = new Date('2026-01-01');
        this.selectedRelation = null;
        this.focusTime = null;
        this.hoveredEntity = null;
        this.time = 0;
    }

    init() {
        this.canvas = document.createElement('canvas');
        this.canvas.width = this.container.clientWidth;
        this.canvas.height = this.container.clientHeight;
        this.canvas.style.cssText = 'position:absolute;top:0;left:0;cursor:ew-resize;';
        this.container.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');

        this.setupInteraction();
        this.animate();
    }

    // Allen's 13 interval relations
    allenRelations = [
        { name: 'before', symbol: '<', desc: 'X ends before Y starts' },
        { name: 'after', symbol: '>', desc: 'X starts after Y ends' },
        { name: 'meets', symbol: 'm', desc: 'X ends exactly when Y starts' },
        { name: 'met-by', symbol: 'mi', desc: 'X starts exactly when Y ends' },
        { name: 'overlaps', symbol: 'o', desc: 'X starts before Y, ends during Y' },
        { name: 'overlapped-by', symbol: 'oi', desc: 'Y starts before X, ends during X' },
        { name: 'starts', symbol: 's', desc: 'X starts with Y, ends before Y' },
        { name: 'started-by', symbol: 'si', desc: 'Y starts with X, ends before X' },
        { name: 'finishes', symbol: 'f', desc: 'X ends with Y, starts after Y' },
        { name: 'finished-by', symbol: 'fi', desc: 'Y ends with X, starts after X' },
        { name: 'during', symbol: 'd', desc: 'X contained entirely within Y' },
        { name: 'contains', symbol: 'di', desc: 'Y contained entirely within X' },
        { name: 'equals', symbol: '=', desc: 'X and Y have same start and end' },
    ];

    setupInteraction() {
        let isDragging = false;
        let dragStartX = 0;

        this.canvas.addEventListener('mousedown', (e) => {
            isDragging = true;
            dragStartX = e.clientX;
        });

        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            // Update focus time based on mouse position
            const timeRange = this.viewEnd - this.viewStart;
            this.focusTime = new Date(this.viewStart.getTime() + (x / this.canvas.width) * timeRange);

            // Check for entity hover
            this.hoveredEntity = null;
            this.data.entities.forEach((entity, i) => {
                const entityY = 150 + i * 50;
                if (Math.abs(y - entityY) < 20) {
                    this.hoveredEntity = entity;
                }
            });

            // Pan if dragging
            if (isDragging) {
                const dx = e.clientX - dragStartX;
                const panAmount = (dx / this.canvas.width) * timeRange * 0.5;
                // Would implement panning here
                dragStartX = e.clientX;
            }
        });

        this.canvas.addEventListener('mouseup', () => {
            isDragging = false;
        });

        this.canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            // Zoom in/out on time
            const zoomFactor = e.deltaY > 0 ? 1.1 : 0.9;
            const mid = (this.viewStart.getTime() + this.viewEnd.getTime()) / 2;
            const halfRange = (this.viewEnd - this.viewStart) / 2 * zoomFactor;
            this.viewStart = new Date(mid - halfRange);
            this.viewEnd = new Date(mid + halfRange);
        });

        // Keyboard for relation selection
        document.addEventListener('keydown', (e) => {
            if (e.key >= '1' && e.key <= '9') {
                const idx = parseInt(e.key) - 1;
                if (idx < this.allenRelations.length) {
                    this.selectedRelation = this.allenRelations[idx];
                    console.log('[Temporal] Selected relation:', this.selectedRelation.name);
                }
            } else if (e.key === '0') {
                this.selectedRelation = null;
            }
        });
    }

    timeToX(date) {
        const d = new Date(date);
        const range = this.viewEnd - this.viewStart;
        return ((d - this.viewStart) / range) * this.canvas.width;
    }

    render() {
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;
        this.time = Date.now() * 0.001;

        // Background: Deep time void
        ctx.fillStyle = '#020205';
        ctx.fillRect(0, 0, w, h);

        // Temporal flow field (organic, not gridded)
        this.renderTemporalFlow();

        // Entity intervals as strata
        this.renderEntityStrata();

        // Events as sediment markers
        this.renderEvents();

        // Supersession chains (knowledge evolution)
        this.renderSupersessionChains();

        // Focus time indicator
        if (this.focusTime) {
            this.renderFocusTime();
        }

        // Allen relation selector
        this.renderRelationSelector();

        // Query results (if relation selected)
        if (this.selectedRelation && this.hoveredEntity) {
            this.renderQueryResults();
        }
    }

    renderTemporalFlow() {
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;

        // Flowing "river" of time — not straight lines
        ctx.strokeStyle = 'rgba(60, 80, 120, 0.15)';
        ctx.lineWidth = 1;

        for (let y = 100; y < h - 100; y += 30) {
            ctx.beginPath();
            ctx.moveTo(0, y);

            for (let x = 0; x < w; x += 5) {
                const wave = Math.sin(x * 0.01 + this.time + y * 0.1) * 5;
                ctx.lineTo(x, y + wave);
            }
            ctx.stroke();
        }

        // "Now" marker that pulses
        const nowX = this.timeToX(new Date());
        if (nowX > 0 && nowX < w) {
            const pulse = Math.sin(this.time * 3) * 0.3 + 0.7;
            ctx.strokeStyle = `rgba(255, 200, 100, ${pulse})`;
            ctx.lineWidth = 2;
            ctx.setLineDash([5, 5]);
            ctx.beginPath();
            ctx.moveTo(nowX, 50);
            ctx.lineTo(nowX, h - 50);
            ctx.stroke();
            ctx.setLineDash([]);

            ctx.fillStyle = `rgba(255, 200, 100, ${pulse})`;
            ctx.font = '10px monospace';
            ctx.textAlign = 'center';
            ctx.fillText('NOW', nowX, 40);
        }
    }

    renderEntityStrata() {
        const ctx = this.ctx;
        const w = this.canvas.width;

        this.data.entities.forEach((entity, i) => {
            const y = 150 + i * 50;
            const intervals = entity.intervals || [];

            intervals.forEach(interval => {
                const startX = this.timeToX(interval.from);
                const endX = interval.until ? this.timeToX(interval.until) : w;

                if (endX < 0 || startX > w) return; // Off screen

                const confidence = entity.confidence || 0.7;
                const isHovered = entity === this.hoveredEntity;

                // Stratum layer — organic edges, not rectangles
                const grad = ctx.createLinearGradient(startX, y - 15, endX, y - 15);

                if (isHovered) {
                    grad.addColorStop(0, 'rgba(100, 255, 200, 0)');
                    grad.addColorStop(0.1, `rgba(100, 255, 200, ${confidence * 0.6})`);
                    grad.addColorStop(0.9, `rgba(100, 255, 200, ${confidence * 0.6})`);
                    grad.addColorStop(1, 'rgba(100, 255, 200, 0)');
                } else {
                    grad.addColorStop(0, 'rgba(80, 100, 140, 0)');
                    grad.addColorStop(0.1, `rgba(80, 100, 140, ${confidence * 0.4})`);
                    grad.addColorStop(0.9, `rgba(80, 100, 140, ${confidence * 0.4})`);
                    grad.addColorStop(1, 'rgba(80, 100, 140, 0)');
                }

                ctx.fillStyle = grad;
                ctx.beginPath();

                // Organic top edge
                ctx.moveTo(startX, y);
                for (let x = startX; x <= endX; x += 10) {
                    const wave = Math.sin(x * 0.05 + entity.name.length) * 3;
                    ctx.lineTo(x, y - 15 + wave);
                }

                // Organic bottom edge (reverse)
                for (let x = endX; x >= startX; x -= 10) {
                    const wave = Math.sin(x * 0.05 + entity.name.length + 1) * 3;
                    ctx.lineTo(x, y + 15 + wave);
                }

                ctx.closePath();
                ctx.fill();

                // Uncertainty visualization (fuzzy edges)
                if (entity.uncertainty) {
                    const unc = entity.uncertainty.epistemic || 0.1;
                    ctx.strokeStyle = `rgba(255, 100, 150, ${unc})`;
                    ctx.lineWidth = 2 + unc * 5;
                    ctx.setLineDash([2, 3]);
                    ctx.stroke();
                    ctx.setLineDash([]);
                }

                // Entity name
                ctx.fillStyle = isHovered ? '#64ffda' : 'rgba(200, 210, 230, 0.8)';
                ctx.font = isHovered ? 'bold 12px monospace' : '11px monospace';
                ctx.textAlign = 'left';
                ctx.fillText(entity.name, Math.max(startX + 5, 5), y + 4);
            });
        });
    }

    renderEvents() {
        const ctx = this.ctx;

        this.data.events.forEach(event => {
            const x = this.timeToX(event.timestamp);
            if (x < 0 || x > this.canvas.width) return;

            const y = 130; // Above strata

            // Event marker — not a dot, a sediment drop
            const eventColors = {
                creation: '#64ffda',
                supersession: '#ffd93d',
                claim: '#bd93f9',
            };

            ctx.fillStyle = eventColors[event.type] || '#8892b0';
            ctx.beginPath();
            ctx.moveTo(x, y - 10);
            ctx.lineTo(x - 5, y + 5);
            ctx.lineTo(x + 5, y + 5);
            ctx.closePath();
            ctx.fill();

            // Ripple effect for recent events
            const age = (new Date() - new Date(event.timestamp)) / (1000 * 60 * 60 * 24 * 365);
            if (age < 3) {
                ctx.strokeStyle = `rgba(100, 255, 218, ${0.5 - age * 0.15})`;
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.arc(x, y, 10 + age * 5, 0, Math.PI * 2);
                ctx.stroke();
            }
        });
    }

    renderSupersessionChains() {
        const ctx = this.ctx;

        // Claims that supersede other claims
        const supersedingClaims = this.data.claims?.filter(c => c.supersedes) || [];

        supersedingClaims.forEach(claim => {
            const claimX = this.timeToX(claim.temporal?.validFrom || '2024-01-01');
            const y = this.canvas.height - 80;

            // Draw supersession arrow
            ctx.strokeStyle = 'rgba(255, 217, 61, 0.6)';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(claimX - 30, y);
            ctx.lineTo(claimX, y);
            ctx.lineTo(claimX - 8, y - 5);
            ctx.moveTo(claimX, y);
            ctx.lineTo(claimX - 8, y + 5);
            ctx.stroke();

            ctx.fillStyle = 'rgba(255, 217, 61, 0.7)';
            ctx.font = '9px monospace';
            ctx.textAlign = 'center';
            ctx.fillText('supersedes', claimX - 15, y - 10);
        });
    }

    renderFocusTime() {
        const ctx = this.ctx;
        const x = this.timeToX(this.focusTime);
        const h = this.canvas.height;

        // Focus line — subtle cursor
        ctx.strokeStyle = 'rgba(200, 200, 220, 0.3)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(x, 80);
        ctx.lineTo(x, h - 60);
        ctx.stroke();

        // Focus time label
        ctx.fillStyle = 'rgba(200, 200, 220, 0.8)';
        ctx.font = '10px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(this.focusTime.toISOString().slice(0, 10), x, 75);
    }

    renderRelationSelector() {
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;

        // Allen's relations as query operators
        ctx.fillStyle = 'rgba(40, 40, 60, 0.9)';
        ctx.fillRect(0, h - 50, w, 50);

        ctx.font = '9px monospace';
        ctx.textAlign = 'center';

        this.allenRelations.slice(0, 9).forEach((rel, i) => {
            const x = 50 + i * 80;
            const isSelected = rel === this.selectedRelation;

            ctx.fillStyle = isSelected ? '#64ffda' : 'rgba(150, 160, 180, 0.8)';
            ctx.fillText(`[${i + 1}] ${rel.symbol}`, x, h - 30);
            ctx.fillStyle = isSelected ? '#64ffda' : 'rgba(100, 110, 130, 0.6)';
            ctx.fillText(rel.name, x, h - 15);
        });

        ctx.fillStyle = 'rgba(100, 110, 130, 0.5)';
        ctx.textAlign = 'left';
        ctx.fillText('[0] clear   [wheel] zoom   [drag] pan', w - 200, h - 20);
    }

    renderQueryResults() {
        const ctx = this.ctx;
        const entity = this.hoveredEntity;
        const relation = this.selectedRelation;

        // Find entities that match the relation with the hovered entity
        const entityInterval = entity.intervals?.[0];
        if (!entityInterval) return;

        const results = this.data.entities.filter(other => {
            if (other.id === entity.id) return false;
            const otherInterval = other.intervals?.[0];
            if (!otherInterval) return false;

            // Simplified Allen relation check (would be full implementation in production)
            const eStart = new Date(entityInterval.from);
            const eEnd = entityInterval.until ? new Date(entityInterval.until) : new Date();
            const oStart = new Date(otherInterval.from);
            const oEnd = otherInterval.until ? new Date(otherInterval.until) : new Date();

            switch (relation.name) {
                case 'before': return eEnd < oStart;
                case 'after': return eStart > oEnd;
                case 'overlaps': return eStart < oStart && eEnd > oStart && eEnd < oEnd;
                case 'during': return eStart > oStart && eEnd < oEnd;
                case 'contains': return eStart < oStart && eEnd > oEnd;
                default: return false;
            }
        });

        // Highlight matching entities
        results.forEach((result, i) => {
            const y = 150 + this.data.entities.indexOf(result) * 50;
            ctx.strokeStyle = 'rgba(100, 255, 218, 0.8)';
            ctx.lineWidth = 2;
            ctx.setLineDash([3, 3]);
            ctx.beginPath();
            ctx.moveTo(0, y);
            ctx.lineTo(this.canvas.width, y);
            ctx.stroke();
            ctx.setLineDash([]);
        });

        // Query label
        ctx.fillStyle = 'rgba(100, 255, 218, 0.9)';
        ctx.font = '11px monospace';
        ctx.textAlign = 'left';
        ctx.fillText(
            `"${entity.name}" ${relation.name} ? → ${results.length} matches`,
            10, 30
        );
    }

    animate() {
        this.render();
        requestAnimationFrame(() => this.animate());
    }

    dispose() {
        this.canvas?.remove();
    }
}

export default TemporalQueryExplorer;
