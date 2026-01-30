// ════════════════════════════════════════════════════════════════════════════
// EVIDENCE: Timeline Visualizer
//
// COGNITIVE PURPOSE: Track when knowledge was added, updated, or superseded
// TUFTE PRINCIPLE: Horizontal timeline with stacked intervals, no decoration
// ════════════════════════════════════════════════════════════════════════════

import { DataContracts } from '../lib/mock-data.js';

export class TimelineVisualizer {
    constructor(container) {
        this.container = container;
        this.data = DataContracts.getTemporalData();
        this.selectedEvent = null;
        this.zoom = 1;
        this.panOffset = 0;
    }

    init() {
        this.injectStyles();
        this.render();
    }

    injectStyles() {
        if (document.getElementById('evidence-timeline-styles')) return;

        const style = document.createElement('style');
        style.id = 'evidence-timeline-styles';
        style.textContent = `
            .timeline-container {
                font-family: ui-monospace, 'SF Mono', monospace;
                font-size: 12px;
                background: #0d1117;
                color: #c9d1d9;
                padding: 20px;
                height: 100%;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }
            
            .timeline-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 16px;
            }
            
            .timeline-title {
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: #8b949e;
            }
            
            .timeline-controls {
                display: flex;
                gap: 8px;
            }
            
            .timeline-btn {
                padding: 4px 12px;
                background: #21262d;
                border: 1px solid #30363d;
                border-radius: 4px;
                color: #8b949e;
                font-family: inherit;
                font-size: 11px;
                cursor: pointer;
            }
            
            .timeline-btn:hover {
                background: #30363d;
                color: #c9d1d9;
            }
            
            .timeline-main {
                flex: 1;
                display: flex;
                flex-direction: column;
                overflow: hidden;
                border: 1px solid #21262d;
                border-radius: 4px;
                background: #161b22;
            }
            
            .timeline-axis {
                display: flex;
                padding: 12px 20px;
                border-bottom: 1px solid #21262d;
                background: #0d1117;
            }
            
            .timeline-year {
                flex: 1;
                text-align: center;
                font-size: 10px;
                color: #6e7681;
            }
            
            .timeline-year.current {
                color: #58a6ff;
            }
            
            .timeline-body {
                flex: 1;
                overflow-y: auto;
                padding: 12px 0;
            }
            
            .timeline-row {
                display: flex;
                align-items: center;
                padding: 8px 20px;
                min-height: 40px;
            }
            
            .timeline-row:hover {
                background: rgba(88, 166, 255, 0.05);
            }
            
            .timeline-label {
                width: 160px;
                flex-shrink: 0;
                font-size: 11px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                padding-right: 12px;
            }
            
            .timeline-track {
                flex: 1;
                height: 20px;
                position: relative;
            }
            
            .timeline-interval {
                position: absolute;
                height: 12px;
                top: 4px;
                border-radius: 2px;
                cursor: pointer;
                transition: opacity 0.15s;
            }
            
            .timeline-interval:hover {
                opacity: 0.8;
            }
            
            .timeline-interval.entity { background: #3fb950; }
            .timeline-interval.claim { background: #a371f7; }
            .timeline-interval.supersession { background: #d29922; }
            
            .timeline-event {
                position: absolute;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                top: 6px;
                transform: translateX(-50%);
                cursor: pointer;
                border: 2px solid #0d1117;
            }
            
            .timeline-event.creation { background: #3fb950; }
            .timeline-event.claim { background: #a371f7; }
            .timeline-event.supersession { background: #d29922; }
            
            .timeline-event:hover {
                transform: translateX(-50%) scale(1.3);
                z-index: 10;
            }
            
            .timeline-event.selected {
                transform: translateX(-50%) scale(1.5);
                box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.5);
            }
            
            .timeline-details {
                padding: 16px 20px;
                background: #0d1117;
                border-top: 1px solid #21262d;
            }
            
            .timeline-details-header {
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: #8b949e;
                margin-bottom: 8px;
            }
            
            .timeline-details-content {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 16px;
            }
            
            .detail-item {
                padding: 12px;
                background: #161b22;
                border-radius: 4px;
            }
            
            .detail-label {
                font-size: 9px;
                text-transform: uppercase;
                color: #6e7681;
                margin-bottom: 4px;
            }
            
            .detail-value {
                font-size: 13px;
            }
            
            .legend {
                display: flex;
                gap: 16px;
                padding: 12px 20px;
                border-top: 1px solid #21262d;
            }
            
            .legend-item {
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 10px;
                color: #6e7681;
            }
            
            .legend-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
            }
            
            .legend-dot.creation { background: #3fb950; }
            .legend-dot.claim { background: #a371f7; }
            .legend-dot.supersession { background: #d29922; }
        `;
        document.head.appendChild(style);
    }

    parseYear(dateStr) {
        if (!dateStr) return null;
        return parseInt(dateStr.split('-')[0]);
    }

    getTimeRange() {
        const years = this.data.events
            .map(e => this.parseYear(e.timestamp))
            .filter(y => y !== null);

        const entities = this.data.entities || [];
        entities.forEach(e => {
            if (e.intervals) {
                e.intervals.forEach(i => {
                    const from = this.parseYear(i.from);
                    const until = this.parseYear(i.until);
                    if (from) years.push(from);
                    if (until) years.push(until);
                });
            }
        });

        const min = Math.min(...years) || 2010;
        const max = Math.max(...years, new Date().getFullYear());
        return { min, max };
    }

    selectEvent(eventIndex) {
        this.selectedEvent = this.selectedEvent === eventIndex ? null : eventIndex;
        this.render();
    }

    render() {
        const events = this.data.events;
        const entities = this.data.entities || [];
        const range = this.getTimeRange();
        const years = [];

        for (let y = range.min; y <= range.max; y++) {
            years.push(y);
        }

        const currentYear = new Date().getFullYear();

        // Calculate position as percentage
        const yearToPercent = (year) => {
            return ((year - range.min) / (range.max - range.min)) * 100;
        };

        // Year axis
        const yearAxis = years.map(y =>
            `<span class="timeline-year ${y === currentYear ? 'current' : ''}">${y}</span>`
        ).join('');

        // Entity intervals
        const entityRows = entities.slice(0, 8).map(entity => {
            const intervals = entity.intervals || [];
            const intervalBars = intervals.map(interval => {
                const from = this.parseYear(interval.from) || range.min;
                const until = this.parseYear(interval.until) || range.max;
                const left = yearToPercent(from);
                const width = yearToPercent(until) - left;
                return `<div class="timeline-interval entity" style="left: ${left}%; width: ${width}%" title="${entity.name}"></div>`;
            }).join('');

            return `
                <div class="timeline-row">
                    <div class="timeline-label" title="${entity.name}">${entity.name}</div>
                    <div class="timeline-track">${intervalBars}</div>
                </div>
            `;
        }).join('');

        // Events as dots
        const eventDots = events.map((event, i) => {
            const year = this.parseYear(event.timestamp);
            if (!year) return '';
            const left = yearToPercent(year);
            const isSelected = this.selectedEvent === i;
            return `
                <div class="timeline-event ${event.type} ${isSelected ? 'selected' : ''}" 
                     style="left: ${left}%"
                     data-event="${i}"
                     title="${event.event}">
                </div>
            `;
        }).join('');

        // Event track
        const eventTrackRow = `
            <div class="timeline-row">
                <div class="timeline-label">Events</div>
                <div class="timeline-track">${eventDots}</div>
            </div>
        `;

        // Selected event details
        let detailsPanel = '';
        if (this.selectedEvent !== null) {
            const event = events[this.selectedEvent];
            detailsPanel = `
                <div class="timeline-details">
                    <div class="timeline-details-header">Event Details</div>
                    <div class="timeline-details-content">
                        <div class="detail-item">
                            <div class="detail-label">Event</div>
                            <div class="detail-value">${event.event}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Date</div>
                            <div class="detail-value">${event.timestamp}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Type</div>
                            <div class="detail-value">${event.type}</div>
                        </div>
                    </div>
                </div>
            `;
        }

        this.container.innerHTML = `
            <div class="timeline-container">
                <div class="timeline-header">
                    <span class="timeline-title">Knowledge Timeline (${range.min}–${range.max})</span>
                    <div class="timeline-controls">
                        <button class="timeline-btn">Zoom In</button>
                        <button class="timeline-btn">Zoom Out</button>
                    </div>
                </div>
                
                <div class="timeline-main">
                    <div class="timeline-axis">${yearAxis}</div>
                    <div class="timeline-body">
                        ${entityRows}
                        ${eventTrackRow}
                    </div>
                    <div class="legend">
                        <div class="legend-item">
                            <span class="legend-dot creation"></span>
                            Entity Creation
                        </div>
                        <div class="legend-item">
                            <span class="legend-dot claim"></span>
                            Claim Added
                        </div>
                        <div class="legend-item">
                            <span class="legend-dot supersession"></span>
                            Supersession
                        </div>
                    </div>
                </div>
                
                ${detailsPanel}
            </div>
        `;

        // Attach event handlers
        this.container.querySelectorAll('.timeline-event').forEach(el => {
            el.addEventListener('click', () => this.selectEvent(parseInt(el.dataset.event)));
        });
    }

    dispose() {
        this.container.innerHTML = '';
    }
}

export default TimelineVisualizer;
