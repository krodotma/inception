// ════════════════════════════════════════════════════════════════════════════
// EVIDENCE: Claim Table Visualizer
//
// COGNITIVE PURPOSE: Browse, sort, and compare claims in the knowledge graph
// TUFTE PRINCIPLE: Data-dense table with inline sparklines
// ════════════════════════════════════════════════════════════════════════════

import { DataContracts } from '../lib/mock-data.js';

export class ClaimTableVisualizer {
    constructor(container) {
        this.container = container;
        this.data = DataContracts.getDialecticalTree();
        this.sortColumn = 'confidence';
        this.sortAsc = false;
    }

    init() {
        this.injectStyles();
        this.render();
    }

    injectStyles() {
        if (document.getElementById('evidence-styles')) return;

        const style = document.createElement('style');
        style.id = 'evidence-styles';
        style.textContent = `
            .evidence-container {
                font-family: ui-monospace, 'SF Mono', monospace;
                font-size: 12px;
                background: #0d1117;
                color: #c9d1d9;
                padding: 20px;
                height: 100%;
                overflow: auto;
            }
            
            .evidence-header {
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: #8b949e;
                margin-bottom: 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .evidence-count {
                color: #58a6ff;
            }
            
            .evidence-table {
                width: 100%;
                border-collapse: collapse;
            }
            
            .evidence-table th {
                text-align: left;
                padding: 8px 12px;
                font-weight: 500;
                color: #8b949e;
                text-transform: uppercase;
                font-size: 10px;
                letter-spacing: 0.05em;
                border-bottom: 1px solid #30363d;
                cursor: pointer;
                user-select: none;
                white-space: nowrap;
            }
            
            .evidence-table th:hover { color: #58a6ff; }
            .evidence-table th.sorted { color: #58a6ff; }
            .evidence-table th.sorted::after { content: ' ↓'; }
            .evidence-table th.sorted.asc::after { content: ' ↑'; }
            
            .evidence-table td {
                padding: 10px 12px;
                border-bottom: 1px solid #21262d;
                vertical-align: top;
            }
            
            .evidence-table tbody tr:hover {
                background: #161b22;
            }
            
            .claim-text {
                max-width: 400px;
                line-height: 1.4;
            }
            
            .claim-dialectical {
                display: inline-block;
                padding: 2px 6px;
                background: #3d1f1f;
                color: #f85149;
                border-radius: 3px;
                font-size: 9px;
                margin-left: 8px;
            }
            
            .confidence {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .confidence-value {
                font-variant-numeric: tabular-nums;
                min-width: 40px;
            }
            
            .confidence-bar {
                width: 50px;
                height: 4px;
                background: #21262d;
                border-radius: 2px;
                overflow: hidden;
            }
            
            .confidence-bar-fill {
                height: 100%;
                border-radius: 2px;
            }
            
            .confidence.high .confidence-bar-fill { background: #3fb950; }
            .confidence.medium .confidence-bar-fill { background: #d29922; }
            .confidence.low .confidence-bar-fill { background: #f85149; }
            
            .confidence-interval {
                color: #6e7681;
                font-size: 10px;
            }
            
            .source-count {
                display: inline-flex;
                align-items: center;
                gap: 4px;
            }
            
            .source-icon {
                width: 12px;
                height: 12px;
                opacity: 0.6;
            }
            
            .sparkline {
                font-family: ui-monospace, monospace;
                letter-spacing: -0.05em;
                color: #8b949e;
            }
            
            .sparkline.positive { color: #3fb950; }
            .sparkline.negative { color: #f85149; }
            
            .temporal-tag {
                font-size: 10px;
                color: #6e7681;
            }
            
            .supersedes-tag {
                display: inline-block;
                padding: 2px 6px;
                background: #1f3d1f;
                color: #3fb950;
                border-radius: 3px;
                font-size: 9px;
            }
        `;
        document.head.appendChild(style);
    }

    sparkline(values, max = 1) {
        const chars = '▁▂▃▄▅▆▇█';
        return values.map(v => chars[Math.floor(Math.min(v / max, 1) * 7)]).join('');
    }

    sparklineTrend(values) {
        if (values.length < 2) return 'neutral';
        const delta = values[values.length - 1] - values[0];
        return delta > 0.1 ? 'positive' : delta < -0.1 ? 'negative' : 'neutral';
    }

    getConfidenceLevel(conf) {
        return conf >= 0.8 ? 'high' : conf >= 0.5 ? 'medium' : 'low';
    }

    getSortedClaims() {
        const claims = [...this.data.claims];
        claims.sort((a, b) => {
            let aVal, bVal;
            switch (this.sortColumn) {
                case 'text':
                    aVal = a.text.toLowerCase();
                    bVal = b.text.toLowerCase();
                    break;
                case 'confidence':
                    aVal = a.confidence;
                    bVal = b.confidence;
                    break;
                case 'sources':
                    aVal = a.sourceIds?.length || 0;
                    bVal = b.sourceIds?.length || 0;
                    break;
                default:
                    aVal = a.confidence;
                    bVal = b.confidence;
            }
            if (aVal < bVal) return this.sortAsc ? -1 : 1;
            if (aVal > bVal) return this.sortAsc ? 1 : -1;
            return 0;
        });
        return claims;
    }

    handleSort(column) {
        if (this.sortColumn === column) {
            this.sortAsc = !this.sortAsc;
        } else {
            this.sortColumn = column;
            this.sortAsc = false;
        }
        this.render();
    }

    render() {
        const claims = this.getSortedClaims();

        // Generate mock sparkline history for each claim
        const generateHistory = (conf) => {
            const history = [];
            let val = conf * 0.7 + Math.random() * 0.3;
            for (let i = 0; i < 8; i++) {
                history.push(val);
                val += (Math.random() - 0.5) * 0.1;
                val = Math.max(0.1, Math.min(1, val));
            }
            history[history.length - 1] = conf; // End at current
            return history;
        };

        const rows = claims.map(claim => {
            const level = this.getConfidenceLevel(claim.confidence);
            const sources = claim.sourceIds?.length || 0;
            const history = generateHistory(claim.confidence);
            const spark = this.sparkline(history);
            const trend = this.sparklineTrend(history);

            const interval = claim.interval
                ? `[${claim.interval.lower.toFixed(2)}–${claim.interval.upper.toFixed(2)}]`
                : '';

            const dialecticalTag = claim.dialectical
                ? `<span class="claim-dialectical">${claim.dialectical.type}</span>`
                : '';

            const supersedesTag = claim.supersedes
                ? `<span class="supersedes-tag">supersedes ${claim.supersedes}</span>`
                : '';

            return `
                <tr data-id="${claim.id}">
                    <td>
                        <div class="claim-text">${claim.text}${dialecticalTag}</div>
                        ${supersedesTag}
                    </td>
                    <td>
                        <div class="confidence ${level}">
                            <span class="confidence-value">${claim.confidence.toFixed(2)}</span>
                            <div class="confidence-bar">
                                <div class="confidence-bar-fill" style="width: ${claim.confidence * 100}%"></div>
                            </div>
                        </div>
                        <span class="confidence-interval">${interval}</span>
                    </td>
                    <td>
                        <span class="source-count">
                            <svg class="source-icon" viewBox="0 0 16 16" fill="currentColor">
                                <path d="M2 2.5A2.5 2.5 0 014.5 0h8.75a.75.75 0 01.75.75v12.5a.75.75 0 01-.75.75h-2.5a.75.75 0 110-1.5h1.75v-2h-8a1 1 0 00-.714 1.7.75.75 0 01-1.072 1.05A2.495 2.495 0 012 11.5v-9z"/>
                            </svg>
                            ${sources}
                        </span>
                    </td>
                    <td>
                        <span class="sparkline ${trend}">${spark}</span>
                    </td>
                    <td>
                        <span class="temporal-tag">${claim.temporal?.validFrom || '—'}</span>
                    </td>
                </tr>
            `;
        }).join('');

        const thClass = (col) => {
            if (this.sortColumn === col) {
                return `sorted ${this.sortAsc ? 'asc' : ''}`;
            }
            return '';
        };

        this.container.innerHTML = `
            <div class="evidence-container">
                <div class="evidence-header">
                    <span>Claims in Knowledge Graph</span>
                    <span class="evidence-count">${claims.length} claims</span>
                </div>
                <table class="evidence-table">
                    <thead>
                        <tr>
                            <th class="${thClass('text')}" data-sort="text">Claim</th>
                            <th class="${thClass('confidence')}" data-sort="confidence">Confidence</th>
                            <th class="${thClass('sources')}" data-sort="sources">Sources</th>
                            <th>Trend</th>
                            <th>Valid From</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows}
                    </tbody>
                </table>
            </div>
        `;

        // Attach sort handlers
        this.container.querySelectorAll('th[data-sort]').forEach(th => {
            th.addEventListener('click', () => this.handleSort(th.dataset.sort));
        });
    }

    dispose() {
        this.container.innerHTML = '';
    }
}

export default ClaimTableVisualizer;
