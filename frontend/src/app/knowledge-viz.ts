/**
 * Inception Knowledge Visualization - Unified Module
 * 
 * Exports all Priority 1-5 components from Architect Review.
 * Import this to get the complete knowledge visualization suite.
 */

// =============================================================================
// COMPONENT EXPORTS
// =============================================================================

// Priority 1: Knowledge Graph Canvas
export { KnowledgeGraphCanvas, initKnowledgeGraph } from './knowledge-graph-canvas';
export type { GraphNode, GraphEdge, GraphData } from './knowledge-graph-canvas';

// Priority 2: RheoMode Switcher
export { RheoModeSwitcher, SemanticZoomCamera, initRheoModeSwitcher, initSemanticZoom, RHEO_LEVELS } from './rheomode-switcher';
export type { RheoModeLevel } from './rheomode-switcher';

// Priority 3: Temporal Timeline
export { TemporalTimeline, initTemporalTimeline } from './temporal-timeline';
export type { TimelineEvent, TimelineConfig } from './temporal-timeline';

// Priority 4: Gap Explorer
export { GapExplorerPanel, initGapExplorer } from './gap-explorer';
export type { KnowledgeGap, ResearchSource } from './gap-explorer';

// Priority 5: Confidence Visualization
export { ConfidenceRing, ConfidenceMeter, ClaimCard, createConfidenceRing, createConfidenceMeter, createClaimCard } from './confidence-viz';
export type { ConfidenceScore, ClaimWithConfidence } from './confidence-viz';

// =============================================================================
// INTEGRATED DASHBOARD
// =============================================================================

export interface DashboardConfig {
    apiBaseUrl?: string;
    initialRheoLevel?: number;
    showTimeline?: boolean;
    showGapExplorer?: boolean;
}

export class InceptionDashboard {
    private container: HTMLElement;
    private config: DashboardConfig;

    private graphCanvas: KnowledgeGraphCanvas | null = null;
    private rheoSwitcher: RheoModeSwitcher | null = null;
    private timeline: TemporalTimeline | null = null;
    private gapExplorer: GapExplorerPanel | null = null;

    constructor(container: HTMLElement, config: DashboardConfig = {}) {
        this.container = container;
        this.config = {
            apiBaseUrl: '/api',
            initialRheoLevel: 2,
            showTimeline: true,
            showGapExplorer: true,
            ...config,
        };

        this.render();
        this.initializeComponents();
        this.loadData();
    }

    private render(): void {
        this.container.innerHTML = `
      <div class="inception-dashboard">
        <div class="dashboard-header">
          <h1>Knowledge Graph</h1>
          <div class="rheo-container" id="rheo-container"></div>
        </div>
        
        <div class="dashboard-body">
          <div class="graph-container" id="graph-container"></div>
          
          <aside class="dashboard-sidebar">
            ${this.config.showGapExplorer ? '<div id="gap-container"></div>' : ''}
            <div id="claim-detail-container"></div>
          </aside>
        </div>
        
        ${this.config.showTimeline ? '<div class="timeline-container" id="timeline-container"></div>' : ''}
      </div>
    `;

        this.addDashboardStyles();
    }

    private async initializeComponents(): Promise<void> {
        // Knowledge Graph
        const graphEl = document.getElementById('graph-container');
        if (graphEl) {
            const { initKnowledgeGraph } = await import('./knowledge-graph-canvas');
            this.graphCanvas = initKnowledgeGraph(graphEl);

            this.graphCanvas.onNodeClick = (node) => this.handleNodeClick(node);
            this.graphCanvas.onGapClick = (gap) => this.handleGapClick(gap);
        }

        // RheoMode
        const rheoEl = document.getElementById('rheo-container');
        if (rheoEl) {
            const { initRheoModeSwitcher } = await import('./rheomode-switcher');
            this.rheoSwitcher = initRheoModeSwitcher(rheoEl, (level) => {
                this.graphCanvas?.setRheoModeLevel(level);
            });
            this.rheoSwitcher.setLevel(this.config.initialRheoLevel || 2);
        }

        // Timeline
        if (this.config.showTimeline) {
            const timelineEl = document.getElementById('timeline-container');
            if (timelineEl) {
                const { initTemporalTimeline } = await import('./temporal-timeline');
                this.timeline = initTemporalTimeline(timelineEl);

                this.timeline.onTimeChange = (date) => this.handleTimeChange(date);
            }
        }

        // Gap Explorer
        if (this.config.showGapExplorer) {
            const gapEl = document.getElementById('gap-container');
            if (gapEl) {
                const { initGapExplorer } = await import('./gap-explorer');
                this.gapExplorer = initGapExplorer(gapEl);

                this.gapExplorer.onGapSelect = (gap) => this.graphCanvas?.focusOnNode(gap.id);
                this.gapExplorer.onStartResearch = (gap) => this.startResearch(gap.id);
            }
        }
    }

    private async loadData(): Promise<void> {
        const baseUrl = this.config.apiBaseUrl;

        try {
            // Load graph data
            const graphRes = await fetch(`${baseUrl}/graph`);
            if (graphRes.ok) {
                const graphData = await graphRes.json();
                this.graphCanvas?.loadFromAPI(`${baseUrl}/graph`);
            }

            // Load gaps
            if (this.gapExplorer) {
                this.gapExplorer.loadFromAPI(`${baseUrl}/gaps`);
            }

            // Load timeline events
            if (this.timeline) {
                this.timeline.loadFromAPI(`${baseUrl}/entities/temporal`);
            }
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    }

    private handleNodeClick(node: any): void {
        console.log('Node clicked:', node);
        // Show claim detail in sidebar
    }

    private handleGapClick(gap: any): void {
        this.gapExplorer?.expand();
    }

    private handleTimeChange(date: Date): void {
        // Filter graph to show only entities valid at this time
        console.log('Time changed:', date);
    }

    private async startResearch(gapId: string): Promise<void> {
        try {
            await fetch(`${this.config.apiBaseUrl}/gaps/${gapId}/research`, { method: 'POST' });
            this.gapExplorer?.updateGapStatus(gapId, 'researching', 0);
        } catch (error) {
            console.error('Failed to start research:', error);
        }
    }

    public refresh(): void {
        this.loadData();
    }

    public destroy(): void {
        this.graphCanvas?.destroy();
        this.timeline?.destroy();
    }

    private addDashboardStyles(): void {
        if (document.getElementById('inception-dashboard-styles')) return;

        const style = document.createElement('style');
        style.id = 'inception-dashboard-styles';
        style.textContent = `
      .inception-dashboard {
        display: flex;
        flex-direction: column;
        height: 100vh;
        background: var(--md-sys-color-background, #0f0f1a);
        color: var(--md-sys-color-on-background, #fff);
      }
      .dashboard-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 24px;
        border-bottom: 1px solid var(--md-sys-color-outline-variant, #333);
      }
      .dashboard-header h1 { margin: 0; font-size: 24px; }
      .dashboard-body {
        flex: 1;
        display: flex;
        overflow: hidden;
      }
      .graph-container {
        flex: 1;
        min-height: 400px;
      }
      .dashboard-sidebar {
        width: 320px;
        border-left: 1px solid var(--md-sys-color-outline-variant, #333);
        padding: 16px;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 16px;
      }
      .timeline-container {
        height: 160px;
        border-top: 1px solid var(--md-sys-color-outline-variant, #333);
        padding: 8px 24px;
      }
      @media (max-width: 768px) {
        .dashboard-sidebar { display: none; }
      }
    `;
        document.head.appendChild(style);
    }
}

export function initInceptionDashboard(container: HTMLElement, config?: DashboardConfig): InceptionDashboard {
    return new InceptionDashboard(container, config);
}
