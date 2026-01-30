/**
 * Gap Explorer Panel
 * 
 * Priority 4 from Architect Review: Make gap exploration visible.
 * Shows detected knowledge gaps and autonomous research progress.
 */

// =============================================================================
// TYPES
// =============================================================================

export interface KnowledgeGap {
    id: string;
    type: 'definition' | 'context' | 'evidence' | 'conflict' | 'temporal';
    description: string;
    severity: number;  // 0-1
    relatedClaims: string[];
    status: 'detected' | 'researching' | 'resolved' | 'needs_human';
    researchProgress?: number;  // 0-1
    sources?: ResearchSource[];
}

export interface ResearchSource {
    url: string;
    title: string;
    authority: number;
    freshness: number;
    status: 'pending' | 'fetching' | 'processing' | 'done' | 'failed';
}

// =============================================================================
// MOTION TOKENS
// =============================================================================

const MOTION = {
    duration: {
        short: 150,
        medium: 300,
        long: 500,
    },
    easing: {
        emphasized: 'cubic-bezier(0.2, 0, 0, 1)',
        decelerate: 'cubic-bezier(0.05, 0.7, 0.1, 1)',
    },
};

// =============================================================================
// GAP EXPLORER PANEL
// =============================================================================

export class GapExplorerPanel {
    private container: HTMLElement;
    private gaps: KnowledgeGap[] = [];
    private selectedGap: KnowledgeGap | null = null;
    private isExpanded: boolean = false;

    // Callbacks
    onGapSelect?: (gap: KnowledgeGap) => void;
    onApproveResearch?: (gap: KnowledgeGap) => void;
    onRejectResearch?: (gap: KnowledgeGap) => void;
    onStartResearch?: (gap: KnowledgeGap) => void;

    constructor(container: HTMLElement) {
        this.container = container;
        this.render();
        this.addStyles();
    }

    // ---------------------------------------------------------------------------
    // DATA
    // ---------------------------------------------------------------------------

    public setGaps(gaps: KnowledgeGap[]): void {
        this.gaps = gaps.sort((a, b) => b.severity - a.severity);
        this.render();
    }

    public async loadFromAPI(endpoint: string): Promise<void> {
        try {
            const response = await fetch(endpoint);
            const data = await response.json();

            const gaps: KnowledgeGap[] = data.gaps?.map((g: any) => ({
                id: g.id,
                type: g.type || 'definition',
                description: g.description || g.text,
                severity: g.severity || 0.5,
                relatedClaims: g.related_claims || [],
                status: g.status || 'detected',
                researchProgress: g.progress || 0,
                sources: g.sources || [],
            })) || [];

            this.setGaps(gaps);
        } catch (error) {
            console.error('Failed to load gaps:', error);
        }
    }

    public updateGapStatus(gapId: string, status: KnowledgeGap['status'], progress?: number): void {
        const gap = this.gaps.find(g => g.id === gapId);
        if (gap) {
            gap.status = status;
            if (progress !== undefined) {
                gap.researchProgress = progress;
            }
            this.render();
        }
    }

    // ---------------------------------------------------------------------------
    // RENDERING
    // ---------------------------------------------------------------------------

    private render(): void {
        const activeGaps = this.gaps.filter(g => g.status !== 'resolved');
        const researchingGaps = this.gaps.filter(g => g.status === 'researching');

        this.container.innerHTML = `
      <div class="gap-explorer ${this.isExpanded ? 'expanded' : ''}">
        <div class="gap-explorer-header" role="button" tabindex="0" aria-expanded="${this.isExpanded}">
          <div class="gap-explorer-title">
            <span class="material-symbols-outlined gap-icon pulse">help_outline</span>
            <span class="gap-count">${activeGaps.length}</span>
            <span>Knowledge Gaps</span>
          </div>
          ${researchingGaps.length > 0 ? `
            <div class="gap-researching-badge">
              <span class="material-symbols-outlined spin">sync</span>
              ${researchingGaps.length} researching
            </div>
          ` : ''}
          <span class="material-symbols-outlined expand-icon">${this.isExpanded ? 'expand_less' : 'expand_more'}</span>
        </div>
        
        <div class="gap-explorer-body">
          ${this.isExpanded ? this.renderGapList() : ''}
        </div>
        
        ${this.selectedGap ? this.renderGapDetail() : ''}
      </div>
    `;

        this.attachListeners();
    }

    private renderGapList(): string {
        if (this.gaps.length === 0) {
            return `
        <div class="gap-empty">
          <span class="material-symbols-outlined">check_circle</span>
          <span>No knowledge gaps detected</span>
        </div>
      `;
        }

        return `
      <ul class="gap-list" role="listbox">
        ${this.gaps.map(gap => this.renderGapItem(gap)).join('')}
      </ul>
    `;
    }

    private renderGapItem(gap: KnowledgeGap): string {
        const isSelected = this.selectedGap?.id === gap.id;
        const typeIcons: Record<string, string> = {
            definition: 'menu_book',
            context: 'layers',
            evidence: 'fact_check',
            conflict: 'warning',
            temporal: 'schedule',
        };

        const statusColors: Record<string, string> = {
            detected: 'var(--md-sys-color-error)',
            researching: 'var(--md-sys-color-primary)',
            resolved: 'var(--md-sys-color-tertiary)',
            needs_human: 'var(--md-sys-color-warning, #F59E0B)',
        };

        return `
      <li 
        class="gap-item ${isSelected ? 'selected' : ''}"
        data-gap-id="${gap.id}"
        role="option"
        aria-selected="${isSelected}"
        tabindex="0"
      >
        <div class="gap-item-icon" style="color: ${statusColors[gap.status]}">
          <span class="material-symbols-outlined">${typeIcons[gap.type] || 'help'}</span>
        </div>
        <div class="gap-item-content">
          <div class="gap-item-desc">${gap.description.slice(0, 50)}${gap.description.length > 50 ? '...' : ''}</div>
          <div class="gap-item-meta">
            <span class="gap-type">${gap.type}</span>
            ${gap.status === 'researching' ? `
              <div class="gap-progress">
                <div class="gap-progress-bar" style="width: ${(gap.researchProgress || 0) * 100}%"></div>
              </div>
            ` : `
              <span class="gap-status">${gap.status}</span>
            `}
          </div>
        </div>
        <div class="gap-severity" title="Severity: ${Math.round(gap.severity * 100)}%">
          <svg viewBox="0 0 36 36" class="severity-ring">
            <path
              d="M18 2.5 a 15.5 15.5 0 1 1 0 31 a 15.5 15.5 0 1 1 0 -31"
              fill="none"
              stroke="var(--md-sys-color-surface-variant)"
              stroke-width="3"
            />
            <path
              d="M18 2.5 a 15.5 15.5 0 1 1 0 31 a 15.5 15.5 0 1 1 0 -31"
              fill="none"
              stroke="${this.getSeverityColor(gap.severity)}"
              stroke-width="3"
              stroke-dasharray="${gap.severity * 100}, 100"
              stroke-linecap="round"
            />
          </svg>
        </div>
      </li>
    `;
    }

    private renderGapDetail(): string {
        const gap = this.selectedGap!;

        return `
      <div class="gap-detail-overlay" role="dialog" aria-modal="true">
        <div class="gap-detail">
          <div class="gap-detail-header">
            <h3>${gap.type.charAt(0).toUpperCase() + gap.type.slice(1)} Gap</h3>
            <button class="gap-detail-close" aria-label="Close">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          
          <div class="gap-detail-body">
            <p class="gap-detail-desc">${gap.description}</p>
            
            ${gap.relatedClaims.length > 0 ? `
              <div class="gap-related">
                <h4>Related Claims</h4>
                <ul>
                  ${gap.relatedClaims.map(c => `<li>${c}</li>`).join('')}
                </ul>
              </div>
            ` : ''}
            
            ${gap.status === 'researching' && gap.sources ? `
              <div class="gap-research-trail">
                <h4>Research Trail</h4>
                <ul class="source-list">
                  ${gap.sources.map(s => `
                    <li class="source-item ${s.status}">
                      <span class="material-symbols-outlined source-icon">
                        ${s.status === 'done' ? 'check_circle' : s.status === 'failed' ? 'error' : 'pending'}
                      </span>
                      <span class="source-title">${s.title}</span>
                      <span class="source-url">${new URL(s.url).hostname}</span>
                    </li>
                  `).join('')}
                </ul>
              </div>
            ` : ''}
          </div>
          
          <div class="gap-detail-actions">
            ${gap.status === 'detected' ? `
              <button class="gap-btn gap-btn-primary" data-action="start-research">
                <span class="material-symbols-outlined">search</span>
                Start Research
              </button>
            ` : ''}
            
            ${gap.status === 'researching' || gap.status === 'needs_human' ? `
              <button class="gap-btn gap-btn-success" data-action="approve">
                <span class="material-symbols-outlined">check</span>
                Approve
              </button>
              <button class="gap-btn gap-btn-danger" data-action="reject">
                <span class="material-symbols-outlined">close</span>
                Reject
              </button>
            ` : ''}
          </div>
        </div>
      </div>
    `;
    }

    // ---------------------------------------------------------------------------
    // HELPERS
    // ---------------------------------------------------------------------------

    private getSeverityColor(severity: number): string {
        if (severity > 0.7) return 'var(--md-sys-color-error)';
        if (severity > 0.4) return 'var(--md-sys-color-warning, #F59E0B)';
        return 'var(--md-sys-color-tertiary)';
    }

    // ---------------------------------------------------------------------------
    // INTERACTIONS
    // ---------------------------------------------------------------------------

    private attachListeners(): void {
        // Toggle expand
        this.container.querySelector('.gap-explorer-header')?.addEventListener('click', () => {
            this.isExpanded = !this.isExpanded;
            this.render();
        });

        // Gap selection
        this.container.querySelectorAll('.gap-item').forEach(item => {
            item.addEventListener('click', () => {
                const gapId = item.getAttribute('data-gap-id');
                this.selectGap(gapId);
            });

            item.addEventListener('keydown', (e: Event) => {
                if ((e as KeyboardEvent).key === 'Enter') {
                    const gapId = item.getAttribute('data-gap-id');
                    this.selectGap(gapId);
                }
            });
        });

        // Close detail
        this.container.querySelector('.gap-detail-close')?.addEventListener('click', () => {
            this.selectedGap = null;
            this.render();
        });

        // Actions
        this.container.querySelector('[data-action="start-research"]')?.addEventListener('click', () => {
            if (this.selectedGap && this.onStartResearch) {
                this.onStartResearch(this.selectedGap);
            }
        });

        this.container.querySelector('[data-action="approve"]')?.addEventListener('click', () => {
            if (this.selectedGap && this.onApproveResearch) {
                this.onApproveResearch(this.selectedGap);
            }
        });

        this.container.querySelector('[data-action="reject"]')?.addEventListener('click', () => {
            if (this.selectedGap && this.onRejectResearch) {
                this.onRejectResearch(this.selectedGap);
            }
        });
    }

    private selectGap(gapId: string | null): void {
        this.selectedGap = this.gaps.find(g => g.id === gapId) || null;
        this.render();

        if (this.selectedGap && this.onGapSelect) {
            this.onGapSelect(this.selectedGap);
        }
    }

    public expand(): void {
        this.isExpanded = true;
        this.render();
    }

    public collapse(): void {
        this.isExpanded = false;
        this.render();
    }

    // ---------------------------------------------------------------------------
    // STYLES
    // ---------------------------------------------------------------------------

    private addStyles(): void {
        if (document.getElementById('gap-explorer-styles')) return;

        const style = document.createElement('style');
        style.id = 'gap-explorer-styles';
        style.textContent = `
      .gap-explorer {
        background: var(--md-sys-color-surface-container);
        border-radius: var(--md-sys-shape-corner-large, 16px);
        overflow: hidden;
      }
      
      .gap-explorer-header {
        display: flex;
        align-items: center;
        gap: var(--md-sys-spacing-sm, 8px);
        padding: var(--md-sys-spacing-md, 16px);
        cursor: pointer;
        transition: background ${MOTION.duration.short}ms ${MOTION.easing.emphasized};
      }
      
      .gap-explorer-header:hover {
        background: var(--md-sys-color-surface-variant);
      }
      
      .gap-explorer-title {
        display: flex;
        align-items: center;
        gap: var(--md-sys-spacing-xs, 4px);
        flex: 1;
        font-weight: 500;
      }
      
      .gap-icon {
        color: var(--md-sys-color-error);
      }
      
      .gap-icon.pulse {
        animation: pulse 2s infinite;
      }
      
      @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
      }
      
      .gap-count {
        background: var(--md-sys-color-error-container);
        color: var(--md-sys-color-on-error-container);
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
      }
      
      .gap-researching-badge {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;
        color: var(--md-sys-color-primary);
      }
      
      .spin {
        animation: spin 1s linear infinite;
      }
      
      @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }
      
      .gap-explorer-body {
        max-height: 0;
        overflow: hidden;
        transition: max-height ${MOTION.duration.medium}ms ${MOTION.easing.decelerate};
      }
      
      .gap-explorer.expanded .gap-explorer-body {
        max-height: 400px;
        overflow-y: auto;
      }
      
      .gap-list {
        list-style: none;
        margin: 0;
        padding: 0;
      }
      
      .gap-item {
        display: flex;
        align-items: center;
        gap: var(--md-sys-spacing-sm, 8px);
        padding: var(--md-sys-spacing-sm, 8px) var(--md-sys-spacing-md, 16px);
        cursor: pointer;
        transition: background ${MOTION.duration.short}ms ${MOTION.easing.emphasized};
      }
      
      .gap-item:hover, .gap-item.selected {
        background: var(--md-sys-color-surface-variant);
      }
      
      .gap-item:focus-visible {
        outline: 2px solid var(--md-sys-color-primary);
        outline-offset: -2px;
      }
      
      .gap-item-content {
        flex: 1;
        min-width: 0;
      }
      
      .gap-item-desc {
        font-size: 14px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      
      .gap-item-meta {
        display: flex;
        align-items: center;
        gap: var(--md-sys-spacing-xs, 4px);
        font-size: 11px;
        color: var(--md-sys-color-on-surface-variant);
        margin-top: 2px;
      }
      
      .gap-type {
        background: var(--md-sys-color-surface);
        padding: 1px 6px;
        border-radius: 4px;
      }
      
      .gap-progress {
        width: 60px;
        height: 4px;
        background: var(--md-sys-color-surface);
        border-radius: 2px;
        overflow: hidden;
      }
      
      .gap-progress-bar {
        height: 100%;
        background: var(--md-sys-color-primary);
        transition: width ${MOTION.duration.medium}ms ${MOTION.easing.decelerate};
      }
      
      .severity-ring {
        width: 28px;
        height: 28px;
        transform: rotate(-90deg);
      }
      
      /* Detail overlay */
      .gap-detail-overlay {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.6);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        animation: fadeIn ${MOTION.duration.short}ms ${MOTION.easing.decelerate};
      }
      
      @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
      }
      
      .gap-detail {
        background: var(--md-sys-color-surface);
        border-radius: var(--md-sys-shape-corner-extra-large, 28px);
        width: 90%;
        max-width: 480px;
        max-height: 80vh;
        overflow: hidden;
        animation: slideUp ${MOTION.duration.medium}ms ${MOTION.easing.decelerate};
      }
      
      @keyframes slideUp {
        from { transform: translateY(20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
      }
      
      .gap-detail-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: var(--md-sys-spacing-md, 16px);
        border-bottom: 1px solid var(--md-sys-color-outline-variant);
      }
      
      .gap-detail-header h3 {
        margin: 0;
        font-size: 18px;
      }
      
      .gap-detail-close {
        background: transparent;
        border: none;
        cursor: pointer;
        padding: 4px;
        border-radius: 50%;
        color: var(--md-sys-color-on-surface);
      }
      
      .gap-detail-close:hover {
        background: var(--md-sys-color-surface-variant);
      }
      
      .gap-detail-body {
        padding: var(--md-sys-spacing-md, 16px);
        max-height: 50vh;
        overflow-y: auto;
      }
      
      .gap-detail-desc {
        margin: 0 0 var(--md-sys-spacing-md, 16px);
        line-height: 1.6;
      }
      
      .gap-related h4, .gap-research-trail h4 {
        font-size: 14px;
        margin: 0 0 var(--md-sys-spacing-sm, 8px);
        color: var(--md-sys-color-on-surface-variant);
      }
      
      .source-list {
        list-style: none;
        margin: 0;
        padding: 0;
      }
      
      .source-item {
        display: flex;
        align-items: center;
        gap: var(--md-sys-spacing-xs, 4px);
        padding: var(--md-sys-spacing-xs, 4px) 0;
        font-size: 13px;
      }
      
      .source-item.done .source-icon { color: var(--md-sys-color-tertiary); }
      .source-item.failed .source-icon { color: var(--md-sys-color-error); }
      .source-item.pending .source-icon, .source-item.fetching .source-icon, .source-item.processing .source-icon {
        color: var(--md-sys-color-primary);
        animation: pulse 1s infinite;
      }
      
      .source-url {
        color: var(--md-sys-color-on-surface-variant);
        font-size: 11px;
      }
      
      .gap-detail-actions {
        display: flex;
        gap: var(--md-sys-spacing-sm, 8px);
        padding: var(--md-sys-spacing-md, 16px);
        border-top: 1px solid var(--md-sys-color-outline-variant);
        justify-content: flex-end;
      }
      
      .gap-btn {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 8px 16px;
        border: none;
        border-radius: 20px;
        cursor: pointer;
        font-weight: 500;
        transition: all ${MOTION.duration.short}ms ${MOTION.easing.emphasized};
      }
      
      .gap-btn-primary {
        background: var(--md-sys-color-primary);
        color: var(--md-sys-color-on-primary);
      }
      
      .gap-btn-success {
        background: var(--md-sys-color-tertiary);
        color: var(--md-sys-color-on-tertiary);
      }
      
      .gap-btn-danger {
        background: var(--md-sys-color-error);
        color: var(--md-sys-color-on-error);
      }
      
      .gap-btn:hover {
        filter: brightness(1.1);
      }
      
      .gap-empty {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: var(--md-sys-spacing-sm, 8px);
        padding: var(--md-sys-spacing-lg, 24px);
        color: var(--md-sys-color-on-surface-variant);
      }
      
      .gap-empty .material-symbols-outlined {
        color: var(--md-sys-color-tertiary);
      }
      
      @media (prefers-reduced-motion: reduce) {
        .gap-icon.pulse, .spin, .source-item .source-icon {
          animation: none;
        }
        .gap-explorer-body, .gap-progress-bar, .gap-btn {
          transition-duration: 0.01ms !important;
        }
      }
    `;
        document.head.appendChild(style);
    }
}

// =============================================================================
// EXPORTS
// =============================================================================

export function initGapExplorer(container: HTMLElement): GapExplorerPanel {
    return new GapExplorerPanel(container);
}
