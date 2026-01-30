/**
 * Confidence Visualization - Rings, Meters, and ClaimCards
 * Priority 5: Show epistemic/aleatoric uncertainty visually
 */

export interface ConfidenceScore {
    aleatoric: number;
    epistemic: number;
    combined?: number;
}

export interface ClaimWithConfidence {
    id: string;
    text: string;
    confidence: ConfidenceScore;
    sources: string[];
    hasConflict?: boolean;
}

const MOTION = { duration: { short: 150, medium: 300 }, easing: { emphasized: 'cubic-bezier(0.2,0,0,1)', decelerate: 'cubic-bezier(0.05,0.7,0.1,1)' } };

export class ConfidenceRing {
    constructor(container: HTMLElement, confidence: ConfidenceScore, options: { size?: number } = {}) {
        const size = options.size || 40, combined = confidence.combined ?? (confidence.aleatoric + confidence.epistemic) / 2;
        const getColor = (v: number) => v > 0.9 ? '#22C55E' : v > 0.7 ? '#3B82F6' : v > 0.5 ? '#EAB308' : v > 0.3 ? '#F97316' : '#EF4444';
        container.innerHTML = `<div style="width:${size}px;height:${size}px;position:relative"><svg viewBox="0 0 40 40"><circle cx="20" cy="20" r="18" fill="none" stroke="#333" stroke-width="3"/><circle cx="20" cy="20" r="18" fill="none" stroke="${getColor(confidence.epistemic)}" stroke-width="3" stroke-dasharray="${confidence.epistemic * 113} 113" stroke-linecap="round" style="transform:rotate(-90deg);transform-origin:center"/><circle cx="20" cy="20" r="13" fill="none" stroke="${getColor(confidence.aleatoric)}" stroke-width="2" stroke-dasharray="${confidence.aleatoric * 82} 82" stroke-linecap="round" style="transform:rotate(-90deg);transform-origin:center"/><text x="20" y="20" text-anchor="middle" dominant-baseline="central" font-size="10" font-weight="600" fill="#fff">${Math.round(combined * 100)}</text></svg></div>`;
    }
}

export class ConfidenceMeter {
    constructor(container: HTMLElement, confidence: ConfidenceScore, label?: string) {
        const combined = confidence.combined ?? (confidence.aleatoric + confidence.epistemic) / 2;
        container.innerHTML = `<div style="display:flex;align-items:center;gap:8px">${label ? `<span style="font-size:12px;color:#94a3b8;min-width:60px">${label}</span>` : ''}<div style="flex:1;height:6px;background:#333;border-radius:3px;overflow:hidden"><div style="height:100%;width:${combined * 100}%;background:linear-gradient(90deg,#3B82F6,#22C55E);border-radius:3px"></div></div><span style="font-size:12px;font-weight:600">${Math.round(combined * 100)}%</span></div>`;
    }
}

export class ClaimCard {
    expanded = false;
    constructor(private container: HTMLElement, private claim: ClaimWithConfidence, private onClick?: (c: ClaimWithConfidence) => void) { this.render(); }

    private render(): void {
        const conf = this.claim.confidence, combined = conf.combined ?? (conf.aleatoric + conf.epistemic) / 2;
        const border = combined > 0.9 ? '#22C55E' : combined > 0.7 ? '#3B82F6' : combined > 0.5 ? '#EAB308' : combined > 0.3 ? '#F97316' : '#EF4444';
        this.container.innerHTML = `<div class="claim-card" style="background:#1e1e2e;border-radius:12px;padding:16px;border-left:4px solid ${border};cursor:pointer"><div style="display:flex;align-items:start;gap:8px"><div id="ring-${this.claim.id}"></div><div style="flex:1;line-height:1.5">${this.claim.text}</div>${this.claim.hasConflict ? '<span style="color:#EF4444">⚠</span>' : ''}</div>${this.expanded ? `<div style="margin-top:16px;padding-top:16px;border-top:1px solid #333"><div style="font-size:12px;color:#94a3b8">Epistemic: ${Math.round(conf.epistemic * 100)}% | Aleatoric: ${Math.round(conf.aleatoric * 100)}%</div><div style="margin-top:8px;font-size:12px">Sources: ${this.claim.sources.join(', ')}</div></div>` : ''}<button onclick="this.parentElement.classList.toggle('exp')" style="position:absolute;bottom:8px;right:8px;background:none;border:none;color:#94a3b8;cursor:pointer">${this.expanded ? '▲' : '▼'}</button></div>`;
        const ringEl = this.container.querySelector(`#ring-${this.claim.id}`);
        if (ringEl) new ConfidenceRing(ringEl as HTMLElement, conf, { size: 32 });
        this.container.querySelector('.claim-card')?.addEventListener('click', () => { this.expanded = !this.expanded; this.render(); if (this.onClick) this.onClick(this.claim); });
    }
}

export function createConfidenceRing(c: HTMLElement, conf: ConfidenceScore, o?: { size?: number }) { return new ConfidenceRing(c, conf, o); }
export function createConfidenceMeter(c: HTMLElement, conf: ConfidenceScore, l?: string) { return new ConfidenceMeter(c, conf, l); }
export function createClaimCard(c: HTMLElement, claim: ClaimWithConfidence, onClick?: (c: ClaimWithConfidence) => void) { return new ClaimCard(c, claim, onClick); }
