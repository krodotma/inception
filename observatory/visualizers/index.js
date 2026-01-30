// ════════════════════════════════════════════════════════════════════════════
// OBSERVATORY VISUALIZERS — Multi-Paradigm Index
// Cosmic Art (legacy) + EVIDENCE (Tuftean data displays)
// ════════════════════════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════════════════════
// EVIDENCE: Tuftean Data-Dense Visualizations (NEW)
// ═══════════════════════════════════════════════════════════════════════════

export { ClaimTableVisualizer } from './evidence-claim-table.js';
export { SourcePanelVisualizer } from './evidence-source-panel.js';
export { GapMatrixVisualizer } from './evidence-gap-matrix.js';
export { DialecticalComparisonVisualizer } from './evidence-dialectical.js';
export { TimelineVisualizer } from './evidence-timeline.js';

// ═══════════════════════════════════════════════════════════════════════════
// LEGACY: Cosmic Art Visualizations (deprecated, kept for reference)
// ═══════════════════════════════════════════════════════════════════════════

export { GapResolutionInterface } from './gap-resolution.js';
export { DialecticalSynthesisEngine } from './dialectical-synthesis.js';
export { TemporalQueryExplorer } from './temporal-query.js';
export { VoidShaderVisualizer } from './void-shader.js';
export { KnowledgeForceGraph } from './knowledge-force.js';
export { OrganicMorphingVisualizer } from './organic-morphing.js';
export { UncertaintyFieldVisualizer } from './uncertainty-field.js';

// ═══════════════════════════════════════════════════════════════════════════
// EVIDENCE VISUALIZER REGISTRY (Data-Dense, Tuftean)
// ═══════════════════════════════════════════════════════════════════════════

export const EvidenceVisualizers = {
    'claim-table': {
        name: 'Claim Table',
        purpose: 'Browse, sort, and compare claims',
        tech: 'HTML Table + Sparklines',
        load: () => import('./evidence-claim-table.js').then(m => m.ClaimTableVisualizer),
    },
    'source-panel': {
        name: 'Source Panel',
        purpose: 'Rank sources by credibility',
        tech: 'HTML + Bar Chart',
        load: () => import('./evidence-source-panel.js').then(m => m.SourcePanelVisualizer),
    },
    'gap-matrix': {
        name: 'Gap Matrix',
        purpose: 'Prioritize knowledge gaps',
        tech: 'Scatter Plot + List',
        load: () => import('./evidence-gap-matrix.js').then(m => m.GapMatrixVisualizer),
    },
    'dialectical-comparison': {
        name: 'Dialectical Comparison',
        purpose: 'Compare conflicting claims',
        tech: 'Split Panel Table',
        load: () => import('./evidence-dialectical.js').then(m => m.DialecticalComparisonVisualizer),
    },
    'timeline': {
        name: 'Timeline',
        purpose: 'Track temporal evolution',
        tech: 'Horizontal Timeline',
        load: () => import('./evidence-timeline.js').then(m => m.TimelineVisualizer),
    },
};

export const evidenceIds = Object.keys(EvidenceVisualizers);

export function getNextEvidence(currentId) {
    const idx = evidenceIds.indexOf(currentId);
    return evidenceIds[(idx + 1) % evidenceIds.length];
}

// ═══════════════════════════════════════════════════════════════════════════
// LEGACY REGISTRY (Cosmic Art — kept for art mode toggle)
// ═══════════════════════════════════════════════════════════════════════════

export const PurposeVisualizers = {
    'gap-resolution': {
        name: 'Gap Resolution (Art)',
        purpose: 'Feel knowledge voids',
        metaphor: 'Gravitational singularities',
        tech: 'Three.js',
        load: () => import('./gap-resolution.js').then(m => m.GapResolutionInterface),
    },
    'dialectical-synthesis': {
        name: 'Dialectical Synthesis (Art)',
        purpose: 'Navigate contradictions',
        metaphor: 'Magnetic pole opposition',
        tech: 'Canvas 2D',
        load: () => import('./dialectical-synthesis.js').then(m => m.DialecticalSynthesisEngine),
    },
    'temporal-query': {
        name: 'Temporal Query (Art)',
        purpose: 'Query across time',
        metaphor: 'River strata',
        tech: 'Canvas 2D',
        load: () => import('./temporal-query.js').then(m => m.TemporalQueryExplorer),
    },
    'void-shader': {
        name: 'Void Shader (Art)',
        purpose: 'Feel the unknown',
        metaphor: 'Fractal event horizons',
        tech: 'Raw WebGL',
        load: () => import('./void-shader.js').then(m => m.VoidShaderVisualizer),
    },
    'knowledge-force': {
        name: 'Knowledge Force (Art)',
        purpose: 'Explore topology',
        metaphor: 'Emergent clustering',
        tech: 'D3.js SVG',
        load: () => import('./knowledge-force.js').then(m => m.KnowledgeForceGraph),
    },
    'organic-morphing': {
        name: 'Organic Morphing (Art)',
        purpose: 'Feel state transitions',
        metaphor: 'Liquid forms',
        tech: 'Pure CSS',
        load: () => import('./organic-morphing.js').then(m => m.OrganicMorphingVisualizer),
    },
    'uncertainty-field': {
        name: 'Uncertainty Field (Art)',
        purpose: 'Visualize uncertainty',
        metaphor: 'Noise as truth',
        tech: 'WebGL Noise',
        load: () => import('./uncertainty-field.js').then(m => m.UncertaintyFieldVisualizer),
    },
};

export const purposeIds = Object.keys(PurposeVisualizers);

export function getNextPurpose(currentId) {
    const idx = purposeIds.indexOf(currentId);
    return purposeIds[(idx + 1) % purposeIds.length];
}
