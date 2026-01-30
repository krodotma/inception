// ════════════════════════════════════════════════════════════════════════════
// EVIDENCE: Dialectical Comparison Visualizer
//
// COGNITIVE PURPOSE: Compare thesis/antithesis claims side-by-side
// TUFTE PRINCIPLE: Direct comparison, no decoration, explicit contrast
// ════════════════════════════════════════════════════════════════════════════

import { DataContracts } from '../lib/mock-data.js';

export class DialecticalComparisonVisualizer {
    constructor(container) {
        this.container = container;
        this.data = DataContracts.getDialecticalTree();
        this.selectedPair = 0;
    }

    init() {
        this.injectStyles();
        this.render();
    }

    injectStyles() {
        if (document.getElementById('evidence-dialectical-styles')) return;

        const style = document.createElement('style');
        style.id = 'evidence-dialectical-styles';
        style.textContent = `
            .dialectical-container {
                font-family: ui-monospace, 'SF Mono', monospace;
                font-size: 12px;
                background: #0d1117;
                color: #c9d1d9;
                padding: 20px;
                height: 100%;
                overflow: auto;
            }
            
            .dialectical-header {
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: #8b949e;
                margin-bottom: 20px;
            }
            
            .dialectical-pair-selector {
                display: flex;
                gap: 8px;
                margin-bottom: 20px;
            }
            
            .pair-button {
                padding: 8px 16px;
                background: #21262d;
                border: 1px solid #30363d;
                border-radius: 4px;
                color: #8b949e;
                font-family: inherit;
                font-size: 11px;
                cursor: pointer;
                transition: all 0.15s;
            }
            
            .pair-button:hover {
                background: #30363d;
                color: #c9d1d9;
            }
            
            .pair-button.selected {
                background: #161b22;
                border-color: #58a6ff;
                color: #58a6ff;
            }
            
            .dialectical-comparison {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 0;
                border: 1px solid #30363d;
                border-radius: 4px;
                overflow: hidden;
            }
            
            .dialectical-side {
                padding: 24px;
            }
            
            .dialectical-side.thesis {
                border-right: 1px solid #30363d;
                background: linear-gradient(135deg, #0a1f0a 0%, #0d1117 100%);
            }
            
            .dialectical-side.antithesis {
                background: linear-gradient(135deg, #1f0a0a 0%, #0d1117 100%);
            }
            
            .dialectical-label {
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 0.2em;
                margin-bottom: 16px;
            }
            
            .dialectical-side.thesis .dialectical-label { color: #3fb950; }
            .dialectical-side.antithesis .dialectical-label { color: #f85149; }
            
            .dialectical-claim {
                font-size: 15px;
                line-height: 1.6;
                margin-bottom: 20px;
                font-weight: 400;
            }
            
            .dialectical-meta {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            
            .dialectical-meta-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px 12px;
                background: rgba(0,0,0,0.3);
                border-radius: 4px;
            }
            
            .meta-label {
                font-size: 9px;
                text-transform: uppercase;
                color: #6e7681;
            }
            
            .meta-value {
                font-variant-numeric: tabular-nums;
            }
            
            .confidence-indicator {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .confidence-indicator .bar {
                width: 60px;
                height: 4px;
                background: #21262d;
                border-radius: 2px;
                overflow: hidden;
            }
            
            .confidence-indicator .bar-fill {
                height: 100%;
                border-radius: 2px;
            }
            
            .thesis .confidence-indicator .bar-fill { background: #3fb950; }
            .antithesis .confidence-indicator .bar-fill { background: #f85149; }
            
            .dialectical-resolution {
                grid-column: 1 / -1;
                padding: 20px 24px;
                background: #161b22;
                border-top: 1px solid #30363d;
            }
            
            .resolution-header {
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: #8b949e;
                margin-bottom: 12px;
            }
            
            .resolution-verdict {
                display: flex;
                align-items: center;
                gap: 16px;
            }
            
            .verdict-bar {
                flex: 1;
                height: 8px;
                background: #21262d;
                border-radius: 4px;
                overflow: hidden;
                display: flex;
            }
            
            .verdict-thesis {
                height: 100%;
                background: #3fb950;
                transition: width 0.3s;
            }
            
            .verdict-antithesis {
                height: 100%;
                background: #f85149;
                transition: width 0.3s;
            }
            
            .verdict-text {
                min-width: 150px;
                text-align: right;
                font-size: 11px;
            }
            
            .verdict-text.favors-thesis { color: #3fb950; }
            .verdict-text.favors-antithesis { color: #f85149; }
            .verdict-text.contested { color: #d29922; }
            
            .no-conflicts {
                padding: 40px;
                text-align: center;
                color: #6e7681;
            }
        `;
        document.head.appendChild(style);
    }

    getDialecticalPairs() {
        // Find claims that have dialectical relationships
        const tensions = this.data.tensions || [];
        const pairs = [];

        tensions.forEach(claim => {
            if (claim.dialectical?.target) {
                const target = this.data.claims.find(c => c.id === claim.dialectical.target);
                if (target) {
                    pairs.push({
                        thesis: target,
                        antithesis: claim,
                        type: claim.dialectical.type
                    });
                }
            }
        });

        return pairs;
    }

    selectPair(index) {
        this.selectedPair = index;
        this.render();
    }

    render() {
        const pairs = this.getDialecticalPairs();

        if (pairs.length === 0) {
            this.container.innerHTML = `
                <div class="dialectical-container">
                    <div class="dialectical-header">Dialectical Tensions</div>
                    <div class="no-conflicts">No dialectical tensions found in current knowledge graph</div>
                </div>
            `;
            return;
        }

        const pairButtons = pairs.map((pair, i) => `
            <button class="pair-button ${this.selectedPair === i ? 'selected' : ''}" data-index="${i}">
                Tension ${i + 1}: ${pair.type}
            </button>
        `).join('');

        const currentPair = pairs[this.selectedPair];
        const thesis = currentPair.thesis;
        const antithesis = currentPair.antithesis;

        // Calculate resolution
        const thesisWeight = thesis.confidence;
        const antithesisWeight = antithesis.confidence;
        const total = thesisWeight + antithesisWeight;
        const thesisPercent = (thesisWeight / total * 100).toFixed(0);
        const antithesisPercent = (antithesisWeight / total * 100).toFixed(0);

        const delta = thesis.confidence - antithesis.confidence;
        let verdictClass, verdictText;
        if (delta > 0.2) {
            verdictClass = 'favors-thesis';
            verdictText = `Thesis favored (+${delta.toFixed(2)})`;
        } else if (delta < -0.2) {
            verdictClass = 'favors-antithesis';
            verdictText = `Antithesis favored (${delta.toFixed(2)})`;
        } else {
            verdictClass = 'contested';
            verdictText = `Contested (Δ ${Math.abs(delta).toFixed(2)})`;
        }

        // Get source info
        const getSourceInfo = (claim) => {
            const count = claim.sourceIds?.length || 0;
            return `${count} source${count !== 1 ? 's' : ''}`;
        };

        this.container.innerHTML = `
            <div class="dialectical-container">
                <div class="dialectical-header">Dialectical Tensions in Knowledge Graph</div>
                <div class="dialectical-pair-selector">${pairButtons}</div>
                
                <div class="dialectical-comparison">
                    <div class="dialectical-side thesis">
                        <div class="dialectical-label">Thesis</div>
                        <div class="dialectical-claim">${thesis.text}</div>
                        <div class="dialectical-meta">
                            <div class="dialectical-meta-row">
                                <span class="meta-label">Confidence</span>
                                <div class="confidence-indicator">
                                    <span class="meta-value">${thesis.confidence.toFixed(2)}</span>
                                    <div class="bar">
                                        <div class="bar-fill" style="width: ${thesis.confidence * 100}%"></div>
                                    </div>
                                </div>
                            </div>
                            <div class="dialectical-meta-row">
                                <span class="meta-label">Sources</span>
                                <span class="meta-value">${getSourceInfo(thesis)}</span>
                            </div>
                            <div class="dialectical-meta-row">
                                <span class="meta-label">Valid From</span>
                                <span class="meta-value">${thesis.temporal?.validFrom || '—'}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="dialectical-side antithesis">
                        <div class="dialectical-label">Antithesis</div>
                        <div class="dialectical-claim">${antithesis.text}</div>
                        <div class="dialectical-meta">
                            <div class="dialectical-meta-row">
                                <span class="meta-label">Confidence</span>
                                <div class="confidence-indicator">
                                    <span class="meta-value">${antithesis.confidence.toFixed(2)}</span>
                                    <div class="bar">
                                        <div class="bar-fill" style="width: ${antithesis.confidence * 100}%"></div>
                                    </div>
                                </div>
                            </div>
                            <div class="dialectical-meta-row">
                                <span class="meta-label">Sources</span>
                                <span class="meta-value">${getSourceInfo(antithesis)}</span>
                            </div>
                            <div class="dialectical-meta-row">
                                <span class="meta-label">Valid From</span>
                                <span class="meta-value">${antithesis.temporal?.validFrom || '—'}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="dialectical-resolution">
                        <div class="resolution-header">Resolution Analysis</div>
                        <div class="resolution-verdict">
                            <span style="color:#3fb950;font-size:11px">${thesisPercent}%</span>
                            <div class="verdict-bar">
                                <div class="verdict-thesis" style="width: ${thesisPercent}%"></div>
                                <div class="verdict-antithesis" style="width: ${antithesisPercent}%"></div>
                            </div>
                            <span style="color:#f85149;font-size:11px">${antithesisPercent}%</span>
                            <span class="verdict-text ${verdictClass}">${verdictText}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Attach pair selector handlers
        this.container.querySelectorAll('.pair-button').forEach(btn => {
            btn.addEventListener('click', () => this.selectPair(parseInt(btn.dataset.index)));
        });
    }

    dispose() {
        this.container.innerHTML = '';
    }
}

export default DialecticalComparisonVisualizer;
