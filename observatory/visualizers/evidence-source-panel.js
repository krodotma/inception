// ════════════════════════════════════════════════════════════════════════════
// EVIDENCE: Source Panel Visualizer
//
// COGNITIVE PURPOSE: Evaluate and rank sources by credibility
// TUFTE PRINCIPLE: Horizontal bar chart sorted by value
// ════════════════════════════════════════════════════════════════════════════

import { DataContracts } from '../lib/mock-data.js';

export class SourcePanelVisualizer {
    constructor(container) {
        this.container = container;
        this.data = DataContracts.getProvenanceWeb();
        this.selectedSource = null;
    }

    init() {
        this.injectStyles();
        this.render();
    }

    injectStyles() {
        if (document.getElementById('evidence-source-styles')) return;

        const style = document.createElement('style');
        style.id = 'evidence-source-styles';
        style.textContent = `
            .source-panel {
                font-family: ui-monospace, 'SF Mono', monospace;
                font-size: 12px;
                background: #0d1117;
                color: #c9d1d9;
                padding: 20px;
                height: 100%;
                overflow: auto;
            }
            
            .source-header {
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: #8b949e;
                margin-bottom: 20px;
            }
            
            .source-list {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            
            .source-row {
                display: grid;
                grid-template-columns: 200px 1fr 60px 60px;
                gap: 16px;
                align-items: center;
                padding: 12px;
                border: 1px solid #21262d;
                border-radius: 4px;
                cursor: pointer;
                transition: background 0.15s, border-color 0.15s;
            }
            
            .source-row:hover {
                background: #161b22;
                border-color: #30363d;
            }
            
            .source-row.selected {
                border-color: #58a6ff;
                background: #161b22;
            }
            
            .source-name {
                font-weight: 500;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            
            .source-type {
                display: inline-block;
                padding: 2px 6px;
                font-size: 9px;
                text-transform: uppercase;
                border-radius: 3px;
                margin-left: 8px;
            }
            
            .source-type.web { background: #1f3d5c; color: #79c0ff; }
            .source-type.pdf { background: #3d2b1f; color: #d29922; }
            .source-type.video { background: #2d1f3d; color: #a371f7; }
            
            .credibility-bar-container {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .credibility-bar {
                flex: 1;
                height: 8px;
                background: #21262d;
                border-radius: 4px;
                overflow: hidden;
            }
            
            .credibility-bar-fill {
                height: 100%;
                border-radius: 4px;
                transition: width 0.3s;
            }
            
            .credibility-bar-fill.high { background: #3fb950; }
            .credibility-bar-fill.medium { background: #d29922; }
            .credibility-bar-fill.low { background: #f85149; }
            
            .credibility-value {
                font-variant-numeric: tabular-nums;
                min-width: 35px;
                text-align: right;
            }
            
            .claim-count {
                text-align: center;
                color: #8b949e;
            }
            
            .claim-count strong {
                color: #c9d1d9;
            }
            
            .source-details {
                margin-top: 24px;
                padding: 16px;
                background: #161b22;
                border: 1px solid #30363d;
                border-radius: 4px;
            }
            
            .source-details-header {
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: #8b949e;
                margin-bottom: 12px;
            }
            
            .source-url {
                color: #58a6ff;
                font-size: 11px;
                word-break: break-all;
                margin-bottom: 12px;
            }
            
            .source-claims-list {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }
            
            .source-claim-item {
                padding: 8px 12px;
                background: #0d1117;
                border-radius: 3px;
                font-size: 11px;
                line-height: 1.4;
            }
            
            .source-claim-conf {
                float: right;
                color: #8b949e;
                margin-left: 12px;
            }
        `;
        document.head.appendChild(style);
    }

    getCredibilityLevel(cred) {
        return cred >= 0.8 ? 'high' : cred >= 0.5 ? 'medium' : 'low';
    }

    selectSource(sourceId) {
        this.selectedSource = this.selectedSource === sourceId ? null : sourceId;
        this.render();
    }

    render() {
        const sources = [...this.data.sources].sort((a, b) => b.credibility - a.credibility);

        const sourceRows = sources.map(source => {
            const level = this.getCredibilityLevel(source.credibility);
            const isSelected = this.selectedSource === source.id;

            return `
                <div class="source-row ${isSelected ? 'selected' : ''}" data-id="${source.id}">
                    <div class="source-name">
                        ${source.title}
                        <span class="source-type ${source.type}">${source.type}</span>
                    </div>
                    <div class="credibility-bar-container">
                        <div class="credibility-bar">
                            <div class="credibility-bar-fill ${level}" style="width: ${source.credibility * 100}%"></div>
                        </div>
                        <span class="credibility-value">${source.credibility.toFixed(2)}</span>
                    </div>
                    <div class="claim-count"><strong>${source.claimCount}</strong> claims</div>
                </div>
            `;
        }).join('');

        let detailsPanel = '';
        if (this.selectedSource) {
            const source = sources.find(s => s.id === this.selectedSource);
            const claims = this.data.claims.filter(c => c.sourceIds?.includes(source.id));

            const claimsList = claims.map(claim => `
                <div class="source-claim-item">
                    <span class="source-claim-conf">${claim.confidence.toFixed(2)}</span>
                    ${claim.text}
                </div>
            `).join('') || '<div class="source-claim-item" style="color: #8b949e;">No claims from this source</div>';

            detailsPanel = `
                <div class="source-details">
                    <div class="source-details-header">Source Details</div>
                    <div class="source-url">${source.url}</div>
                    <div class="source-details-header">Claims from this source</div>
                    <div class="source-claims-list">${claimsList}</div>
                </div>
            `;
        }

        this.container.innerHTML = `
            <div class="source-panel">
                <div class="source-header">Source Credibility Ranking</div>
                <div class="source-list">${sourceRows}</div>
                ${detailsPanel}
            </div>
        `;

        // Attach click handlers
        this.container.querySelectorAll('.source-row').forEach(row => {
            row.addEventListener('click', () => this.selectSource(row.dataset.id));
        });
    }

    dispose() {
        this.container.innerHTML = '';
    }
}

export default SourcePanelVisualizer;
