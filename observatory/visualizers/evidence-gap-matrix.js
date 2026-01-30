// ════════════════════════════════════════════════════════════════════════════
// EVIDENCE: Gap Matrix Visualizer
//
// COGNITIVE PURPOSE: Identify which knowledge gaps to resolve first
// TUFTE PRINCIPLE: 2D scatter for bivariate comparison + list for details
// ════════════════════════════════════════════════════════════════════════════

import { DataContracts } from '../lib/mock-data.js';

export class GapMatrixVisualizer {
    constructor(container) {
        this.container = container;
        this.data = DataContracts.getGapConstellation();
        this.selectedGap = null;
    }

    init() {
        this.injectStyles();
        this.render();
    }

    injectStyles() {
        if (document.getElementById('evidence-gap-styles')) return;

        const style = document.createElement('style');
        style.id = 'evidence-gap-styles';
        style.textContent = `
            .gap-matrix {
                font-family: ui-monospace, 'SF Mono', monospace;
                font-size: 12px;
                background: #0d1117;
                color: #c9d1d9;
                padding: 20px;
                height: 100%;
                display: grid;
                grid-template-columns: 300px 1fr;
                gap: 24px;
                overflow: hidden;
            }
            
            .gap-list {
                overflow: auto;
            }
            
            .gap-list-header {
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: #8b949e;
                margin-bottom: 12px;
            }
            
            .gap-item {
                padding: 12px;
                border: 1px solid #21262d;
                border-radius: 4px;
                margin-bottom: 8px;
                cursor: pointer;
                transition: all 0.15s;
            }
            
            .gap-item:hover {
                background: #161b22;
                border-color: #30363d;
            }
            
            .gap-item.selected {
                border-color: #a371f7;
                background: #161b22;
            }
            
            .gap-item-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }
            
            .gap-type {
                font-size: 9px;
                text-transform: uppercase;
                padding: 2px 6px;
                border-radius: 3px;
            }
            
            .gap-type.missing { background: #3d2b1f; color: #d29922; }
            .gap-type.conflicting { background: #3d1f1f; color: #f85149; }
            
            .gap-priority {
                font-size: 9px;
                text-transform: uppercase;
                color: #8b949e;
            }
            
            .gap-priority.high { color: #f85149; }
            .gap-priority.medium { color: #d29922; }
            .gap-priority.low { color: #3fb950; }
            
            .gap-description {
                font-size: 11px;
                line-height: 1.4;
                color: #8b949e;
            }
            
            .gap-severity-bar {
                margin-top: 8px;
                height: 3px;
                background: #21262d;
                border-radius: 2px;
                overflow: hidden;
            }
            
            .gap-severity-fill {
                height: 100%;
                background: #a371f7;
                border-radius: 2px;
            }
            
            .scatter-container {
                display: flex;
                flex-direction: column;
            }
            
            .scatter-header {
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: #8b949e;
                margin-bottom: 12px;
            }
            
            .scatter-plot {
                flex: 1;
                position: relative;
                background: #161b22;
                border: 1px solid #21262d;
                border-radius: 4px;
                min-height: 300px;
            }
            
            .scatter-axis-x {
                position: absolute;
                bottom: 8px;
                left: 50%;
                transform: translateX(-50%);
                font-size: 9px;
                color: #6e7681;
            }
            
            .scatter-axis-y {
                position: absolute;
                left: 8px;
                top: 50%;
                transform: translateY(-50%) rotate(-90deg);
                font-size: 9px;
                color: #6e7681;
                white-space: nowrap;
            }
            
            .scatter-point {
                position: absolute;
                width: 16px;
                height: 16px;
                border-radius: 50%;
                background: #a371f7;
                border: 2px solid #0d1117;
                transform: translate(-50%, -50%);
                cursor: pointer;
                transition: all 0.15s;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 8px;
                color: #0d1117;
                font-weight: bold;
            }
            
            .scatter-point:hover {
                transform: translate(-50%, -50%) scale(1.3);
                z-index: 10;
            }
            
            .scatter-point.selected {
                background: #fff;
                color: #a371f7;
            }
            
            .scatter-point.high { background: #f85149; }
            .scatter-point.medium { background: #d29922; }
            .scatter-point.low { background: #3fb950; }
            
            .gap-details {
                margin-top: 16px;
                padding: 12px;
                background: #0d1117;
                border: 1px solid #30363d;
                border-radius: 4px;
            }
            
            .gap-details-header {
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: #8b949e;
                margin-bottom: 8px;
            }
            
            .gap-related {
                display: flex;
                flex-wrap: wrap;
                gap: 6px;
            }
            
            .gap-related-tag {
                padding: 4px 8px;
                background: #21262d;
                border-radius: 3px;
                font-size: 10px;
            }
            
            .quadrant-label {
                position: absolute;
                font-size: 9px;
                color: #30363d;
                pointer-events: none;
            }
            
            .quadrant-label.top-right { top: 20px; right: 20px; }
            .quadrant-label.top-left { top: 20px; left: 40px; }
            .quadrant-label.bottom-right { bottom: 30px; right: 20px; }
            .quadrant-label.bottom-left { bottom: 30px; left: 40px; }
        `;
        document.head.appendChild(style);
    }

    selectGap(gapId) {
        this.selectedGap = this.selectedGap === gapId ? null : gapId;
        this.render();
    }

    render() {
        const gaps = this.data.gaps;

        // Gap list
        const gapItems = gaps.map(gap => {
            const isSelected = this.selectedGap === gap.id;
            return `
                <div class="gap-item ${isSelected ? 'selected' : ''}" data-id="${gap.id}">
                    <div class="gap-item-header">
                        <span class="gap-type ${gap.gapType}">${gap.gapType}</span>
                        <span class="gap-priority ${gap.priority}">${gap.priority}</span>
                    </div>
                    <div class="gap-description">${gap.description}</div>
                    <div class="gap-severity-bar">
                        <div class="gap-severity-fill" style="width: ${gap.severity * 100}%"></div>
                    </div>
                </div>
            `;
        }).join('');

        // Scatter points (severity on X, resolvability approximated by inverse of severity)
        const scatterPoints = gaps.map((gap, i) => {
            const x = gap.severity * 80 + 10; // 10-90% of width
            const resolvability = gap.gapType === 'missing' ? 0.7 : 0.4; // Missing is more resolvable
            const y = 90 - resolvability * 80; // Invert Y axis
            const isSelected = this.selectedGap === gap.id;

            return `
                <div class="scatter-point ${gap.priority} ${isSelected ? 'selected' : ''}" 
                     data-id="${gap.id}"
                     style="left: ${x}%; top: ${y}%;">
                    ${i + 1}
                </div>
            `;
        }).join('');

        // Selected gap details
        let detailsPanel = '';
        if (this.selectedGap) {
            const gap = gaps.find(g => g.id === this.selectedGap);
            const relatedEntities = (gap.relatedEntities || []).map(id =>
                `<span class="gap-related-tag">${id}</span>`
            ).join('');
            const relatedClaims = (gap.relatedClaims || []).map(id =>
                `<span class="gap-related-tag">${id}</span>`
            ).join('');

            detailsPanel = `
                <div class="gap-details">
                    <div class="gap-details-header">Related Entities</div>
                    <div class="gap-related">${relatedEntities || '<span style="color:#6e7681">None</span>'}</div>
                    <div class="gap-details-header" style="margin-top:12px">Related Claims</div>
                    <div class="gap-related">${relatedClaims || '<span style="color:#6e7681">None</span>'}</div>
                    <div class="gap-details-header" style="margin-top:12px">Potential Sources</div>
                    <div class="gap-related">${(gap.potentialSources || []).map(s => `<span class="gap-related-tag">${s}</span>`).join('') || '<span style="color:#6e7681">None</span>'}</div>
                </div>
            `;
        }

        this.container.innerHTML = `
            <div class="gap-matrix">
                <div class="gap-list">
                    <div class="gap-list-header">Knowledge Gaps (${gaps.length})</div>
                    ${gapItems}
                </div>
                <div class="scatter-container">
                    <div class="scatter-header">Priority Matrix: Severity × Resolvability</div>
                    <div class="scatter-plot">
                        <span class="quadrant-label top-right">High Priority</span>
                        <span class="quadrant-label top-left">Hard to Resolve</span>
                        <span class="quadrant-label bottom-right">Quick Wins</span>
                        <span class="quadrant-label bottom-left">Low Priority</span>
                        <span class="scatter-axis-x">Severity →</span>
                        <span class="scatter-axis-y">Resolvability ↑</span>
                        ${scatterPoints}
                    </div>
                    ${detailsPanel}
                </div>
            </div>
        `;

        // Attach click handlers
        this.container.querySelectorAll('[data-id]').forEach(el => {
            el.addEventListener('click', () => this.selectGap(el.dataset.id));
        });
    }

    dispose() {
        this.container.innerHTML = '';
    }
}

export default GapMatrixVisualizer;
