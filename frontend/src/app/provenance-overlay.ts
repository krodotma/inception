/**
 * Source Provenance Overlay
 * 
 * Priority 6 from Architect Review: Show exactly where knowledge came from.
 * Tooltip/overlay showing source, timestamp, confidence on hover.
 */

export interface SourceReference {
    id: string;
    type: 'video' | 'webpage' | 'pdf' | 'rfc' | 'book';
    title: string;
    url?: string;
    timestamp?: string;  // e.g., "3:42 - 3:45" for video
    pageRef?: string;    // e.g., "§1.4" for RFC
    accessedAt: Date;
    authority: number;   // 0-1
    freshness: number;   // 0-1
}

export interface ClaimProvenance {
    claimId: string;
    claimText: string;
    sources: SourceReference[];
    confidence: number;
    fusionMethod?: 'recency' | 'authority' | 'consensus' | 'confidence';
}

const ICONS: Record<string, string> = {
    video: '🎬',
    webpage: '🌐',
    pdf: '📄',
    rfc: '📜',
    book: '📚',
};

export class ProvenanceOverlay {
    private overlay: HTMLElement | null = null;
    private currentClaim: ClaimProvenance | null = null;

    onSourceClick?: (source: SourceReference) => void;

    constructor() {
        this.createOverlay();
    }

    private createOverlay(): void {
        this.overlay = document.createElement('div');
        this.overlay.className = 'provenance-overlay';
        this.overlay.style.cssText = `
      position: fixed;
      z-index: 10000;
      pointer-events: none;
      opacity: 0;
      transition: opacity 150ms ease-out;
      max-width: 320px;
    `;
        document.body.appendChild(this.overlay);
        this.addStyles();
    }

    public show(claim: ClaimProvenance, x: number, y: number): void {
        if (!this.overlay) return;
        this.currentClaim = claim;

        const sourceList = claim.sources.map(s => `
      <li class="prov-source" data-source-id="${s.id}">
        <span class="prov-icon">${ICONS[s.type] || '📎'}</span>
        <div class="prov-source-info">
          <span class="prov-title">${s.title}</span>
          ${s.timestamp ? `<span class="prov-time">@ ${s.timestamp}</span>` : ''}
          ${s.pageRef ? `<span class="prov-ref">${s.pageRef}</span>` : ''}
        </div>
        <div class="prov-bars">
          <div class="prov-bar" title="Authority ${Math.round(s.authority * 100)}%">
            <div class="prov-fill" style="width:${s.authority * 100}%;background:#8B5CF6"></div>
          </div>
          <div class="prov-bar" title="Freshness ${Math.round(s.freshness * 100)}%">
            <div class="prov-fill" style="width:${s.freshness * 100}%;background:#10B981"></div>
          </div>
        </div>
      </li>
    `).join('');

        this.overlay.innerHTML = `
      <div class="prov-content">
        <div class="prov-claim">"${claim.claimText}"</div>
        <div class="prov-divider"></div>
        <ul class="prov-sources">${sourceList}</ul>
        <div class="prov-footer">
          <span class="prov-conf">⭐ Confidence: ${Math.round(claim.confidence * 100)}%</span>
          ${claim.fusionMethod ? `<span class="prov-fusion">🔗 ${claim.fusionMethod}</span>` : ''}
        </div>
      </div>
    `;

        // Position
        const rect = this.overlay.getBoundingClientRect();
        const left = Math.min(x + 10, window.innerWidth - rect.width - 20);
        const top = y + 20 > window.innerHeight - rect.height ? y - rect.height - 10 : y + 20;

        this.overlay.style.left = `${left}px`;
        this.overlay.style.top = `${top}px`;
        this.overlay.style.opacity = '1';
        this.overlay.style.pointerEvents = 'auto';

        // Source click handlers
        this.overlay.querySelectorAll('.prov-source').forEach(el => {
            el.addEventListener('click', () => {
                const id = el.getAttribute('data-source-id');
                const source = claim.sources.find(s => s.id === id);
                if (source && this.onSourceClick) this.onSourceClick(source);
            });
        });
    }

    public hide(): void {
        if (!this.overlay) return;
        this.overlay.style.opacity = '0';
        this.overlay.style.pointerEvents = 'none';
        this.currentClaim = null;
    }

    public isVisible(): boolean {
        return this.overlay?.style.opacity === '1';
    }

    private addStyles(): void {
        if (document.getElementById('provenance-overlay-styles')) return;
        const style = document.createElement('style');
        style.id = 'provenance-overlay-styles';
        style.textContent = `
      .prov-content {
        background: var(--md-sys-color-surface, #1e1e2e);
        border: 1px solid var(--md-sys-color-outline-variant, #333);
        border-radius: 12px;
        padding: 12px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        backdrop-filter: blur(8px);
      }
      .prov-claim {
        font-style: italic;
        color: var(--md-sys-color-on-surface-variant, #94a3b8);
        font-size: 13px;
        line-height: 1.4;
        margin-bottom: 8px;
      }
      .prov-divider {
        height: 1px;
        background: var(--md-sys-color-outline-variant, #333);
        margin: 8px 0;
      }
      .prov-sources {
        list-style: none;
        margin: 0;
        padding: 0;
      }
      .prov-source {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 6px 0;
        cursor: pointer;
        border-radius: 6px;
        transition: background 100ms;
      }
      .prov-source:hover {
        background: rgba(255,255,255,0.05);
      }
      .prov-icon { font-size: 16px; }
      .prov-source-info { flex: 1; min-width: 0; }
      .prov-title {
        display: block;
        font-size: 12px;
        font-weight: 500;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .prov-time, .prov-ref {
        font-size: 10px;
        color: var(--md-sys-color-primary, #8B5CF6);
      }
      .prov-bars {
        display: flex;
        flex-direction: column;
        gap: 2px;
        width: 40px;
      }
      .prov-bar {
        height: 3px;
        background: rgba(255,255,255,0.1);
        border-radius: 2px;
        overflow: hidden;
      }
      .prov-fill { height: 100%; border-radius: 2px; }
      .prov-footer {
        display: flex;
        justify-content: space-between;
        margin-top: 8px;
        font-size: 11px;
        color: var(--md-sys-color-on-surface-variant, #94a3b8);
      }
    `;
        document.head.appendChild(style);
    }

    public destroy(): void {
        this.overlay?.remove();
        this.overlay = null;
    }
}

export function initProvenanceOverlay(): ProvenanceOverlay {
    return new ProvenanceOverlay();
}
