/**
 * Inception Neurosymbolic Interface
 * Phase 1: Backend Integration (Steps 1-50)
 * 
 * PURPOSE-FIRST: Every visual = real backend data
 * No placeholders. Interaction changes the model.
 */

import { h, text, app } from 'hyperapp';
import { NeuroScene } from './lib/components/NeuroScene.js';
import { compileToCSS, generateSampleNode } from './lib/grammar.js';
import * as API from './lib/api.js';

// ============================================================
// STATE (Step 21-28: Map backend data model)
// ============================================================

const initialState = {
    // Connection status
    connected: false,
    loading: true,
    error: null,

    // Backend data (real knowledge, not placeholders)
    stats: {
        entities: 0,
        claims: 0,
        procedures: 0,
        gaps: 0,
    },
    sources: [],      // Ingested sources
    entities: [],     // Named entities from extraction
    claims: [],       // SPO triples with confidence
    gaps: [],         // Knowledge holes to fill
    graph: null,      // Hypergraph topology

    // UI state
    selectedNodeId: null,
    selectedNodeType: null, // 'source' | 'entity' | 'claim' | 'gap'
    sceneReady: false,
    activePanel: 'knowledge', // 'knowledge' | 'ingest' | 'gaps'

    // Ingestion state
    ingesting: false,
    ingestUrl: '',
    ingestProgress: null,

    // Query state
    query: '',
    queryResults: null,
};

// ============================================================
// ACTIONS (State transitions)
// ============================================================

// Connection & Loading
const SetLoading = (state, loading) => ({ ...state, loading });
const SetConnected = (state) => ({ ...state, connected: true, loading: false });
const SetError = (state, error) => ({ ...state, error, loading: false });

// Data population (from API)
const SetStats = (state, stats) => ({ ...state, stats });
const SetSources = (state, sources) => ({ ...state, sources });
const SetEntities = (state, entities) => ({ ...state, entities });
const SetClaims = (state, claims) => ({ ...state, claims });
const SetGaps = (state, gaps) => ({ ...state, gaps });
const SetGraph = (state, graph) => ({ ...state, graph });

// Selection
const SelectNode = (state, { id, type }) => ({
    ...state,
    selectedNodeId: state.selectedNodeId === id ? null : id,
    selectedNodeType: state.selectedNodeId === id ? null : type,
});

// UI navigation
const SetActivePanel = (state, panel) => ({ ...state, activePanel: panel });
const SetSceneReady = (state) => ({ ...state, sceneReady: true });

// Ingestion
const SetIngestUrl = (state, url) => ({ ...state, ingestUrl: url });
const StartIngesting = (state) => ({ ...state, ingesting: true, ingestProgress: { stage: 'starting' } });
const UpdateIngestProgress = (state, progress) => ({ ...state, ingestProgress: progress });
const FinishIngesting = (state) => ({ ...state, ingesting: false, ingestProgress: null, ingestUrl: '' });

// Query
const SetQuery = (state, query) => ({ ...state, query });
const SetQueryResults = (state, results) => ({ ...state, queryResults: results });

// ============================================================
// EFFECTS (Side effects & API calls)
// ============================================================

const fetchInitialDataFx = (dispatch) => {
    dispatch(SetLoading, true);

    API.fetchInitialData()
        .then(({ stats, sources, entities, gaps }) => {
            dispatch(SetStats, stats);
            dispatch(SetSources, sources);
            dispatch(SetEntities, entities);
            dispatch(SetGaps, gaps);
            dispatch(SetConnected);
        })
        .catch(error => {
            console.error('[Inception] Failed to fetch initial data:', error);
            dispatch(SetError, error.message);
        });
};

const fetchGraphFx = (dispatch) => {
    API.fetchGraphWithClaims()
        .then(data => {
            dispatch(SetGraph, data);
            dispatch(SetClaims, data.claims || []);

            // Update 3D scene with real data
            if (window.neuroScene && data.nodes) {
                window.neuroScene.clear();
                data.nodes.forEach(node => {
                    // Map backend node to grammar-compatible format
                    const grammarNode = mapNodeToGrammar(node);
                    window.neuroScene.addNode(grammarNode);
                });
            }
        })
        .catch(error => {
            console.error('[Inception] Failed to fetch graph:', error);
        });
};

const initSceneFx = (dispatch) => {
    requestAnimationFrame(() => {
        const canvas = document.getElementById('neuro-canvas');
        if (canvas) {
            try {
                window.neuroScene = new NeuroScene(canvas);
                dispatch(SetSceneReady);

                // Now fetch real graph data
                fetchGraphFx(dispatch);

                console.log('[Inception] 3D scene initialized with real data');
            } catch (e) {
                console.error('[Inception] Scene init failed:', e);
            }
        }
    });
};

const startIngestionFx = (dispatch, url) => {
    dispatch(StartIngesting);

    API.subscribeToIngestion(
        url,
        (progress) => dispatch(UpdateIngestProgress, progress),
        (result) => {
            dispatch(FinishIngesting);
            // Refresh data after ingestion
            fetchInitialDataFx(dispatch);
            fetchGraphFx(dispatch);
        },
        (error) => {
            console.error('[Inception] Ingestion failed:', error);
            dispatch(SetError, error.message);
            dispatch(FinishIngesting);
        }
    );
};

const queryKnowledgeFx = (dispatch, queryText) => {
    API.queryKnowledge(queryText)
        .then(results => dispatch(SetQueryResults, results))
        .catch(error => {
            console.error('[Inception] Query failed:', error);
        });
};

// ============================================================
// DATA MAPPING (Step 41-50: Backend data → Visual grammar)
// ============================================================

/**
 * Map backend node to grammar-compatible format for 3D rendering
 * Step 41-49: Data → Visual properties
 */
function mapNodeToGrammar(node) {
    const baseNode = {
        id: node.id,
        label: node.name || node.statement || node.description || 'Unknown',
        entityType: mapNodeType(node.type),
    };

    // Step 41: Confidence → visual solidity
    const confidence = node.confidence || 0.5;

    // Step 42-43: Modality/hedging → particle density
    // For now, derive uncertainty from confidence
    const uncertainty = 1 - confidence;

    // Step 45: Source credibility → glow intensity
    const sourceTrust = node.source_credibility || confidence;

    // Step 48: Recency → saturation
    const recency = node.recency || 0.5;

    return {
        ...baseNode,
        uncertainty,
        confidence,
        attention: recency,
        sourceTrust,
    };
}

function mapNodeType(backendType) {
    const typeMap = {
        'entity': 'entity',
        'claim': 'claim',
        'source': 'source',
        'procedure': 'concept',
        'gap': 'gap',
    };
    return typeMap[backendType] || 'entity';
}

// ============================================================
// COMPONENTS
// ============================================================

const Header = () => (
    h('header', { class: 'neuro-header' }, [
        h('div', { class: 'header-brand' }, [
            h('h1', { class: 'header-title' }, [text('Inception')]),
            h('span', { class: 'header-subtitle' }, [text('Neurosymbolic Knowledge')]),
        ]),
        h('div', { class: 'header-badge' }, [
            h('span', { class: 'badge-phase' }, [text('Phase 1')]),
            h('span', { class: 'badge-version' }, [text('PURPOSE')]),
        ]),
    ])
);

const StatsBar = (stats, connected) => (
    h('div', { class: 'stats-bar' }, [
        StatCard('Entities', String(stats.entities), 'count', connected),
        StatCard('Claims', String(stats.claims), 'claim', connected),
        StatCard('Procedures', String(stats.procedures), 'procedure', connected),
        StatCard('Gaps', String(stats.gaps), 'gap', connected),
    ])
);

const StatCard = (label, value, type, connected) => (
    h('div', { class: `stat-card stat-${type} ${connected ? '' : 'loading'}` }, [
        h('span', { class: 'stat-value' }, [text(connected ? value : '...')]),
        h('span', { class: 'stat-label' }, [text(label)]),
    ])
);

const PanelTabs = (activePanel) => (
    h('div', { class: 'panel-tabs' }, [
        h('button', {
            class: `tab ${activePanel === 'knowledge' ? 'active' : ''}`,
            onclick: [SetActivePanel, 'knowledge']
        }, [text('Knowledge')]),
        h('button', {
            class: `tab ${activePanel === 'ingest' ? 'active' : ''}`,
            onclick: [SetActivePanel, 'ingest']
        }, [text('Ingest')]),
        h('button', {
            class: `tab ${activePanel === 'gaps' ? 'active' : ''}`,
            onclick: [SetActivePanel, 'gaps']
        }, [text('Gaps')]),
    ])
);

const KnowledgePanel = (entities, claims, selectedNodeId) => (
    h('div', { class: 'knowledge-panel' }, [
        h('h3', {}, [text('Entities')]),
        h('div', { class: 'node-list' },
            entities.slice(0, 10).map(entity =>
                EntityCard(entity, entity.id === selectedNodeId)
            )
        ),
        h('h3', {}, [text('Claims')]),
        h('div', { class: 'node-list' },
            claims.slice(0, 10).map(claim =>
                ClaimCard(claim, claim.id === selectedNodeId)
            )
        ),
    ])
);

const EntityCard = (entity, isSelected) => (
    h('div', {
        class: `node-card ${isSelected ? 'selected' : ''} type-entity`,
        onclick: [SelectNode, { id: entity.id, type: 'entity' }],
    }, [
        h('div', { class: 'node-header' }, [
            h('span', { class: 'node-type-badge' }, [text(entity.type || 'entity')]),
            h('span', { class: 'node-label' }, [text(entity.name)]),
        ]),
        entity.description ?
            h('div', { class: 'node-description' }, [text(entity.description)]) : null,
        h('div', { class: 'node-meta' }, [
            h('span', {}, [text(`Confidence: ${Math.round((entity.confidence || 0.5) * 100)}%`)]),
        ]),
    ])
);

const ClaimCard = (claim, isSelected) => (
    h('div', {
        class: `node-card ${isSelected ? 'selected' : ''} type-claim`,
        onclick: [SelectNode, { id: claim.id, type: 'claim' }],
    }, [
        h('div', { class: 'node-header' }, [
            h('span', { class: 'node-type-badge' }, [text('claim')]),
        ]),
        h('div', { class: 'claim-statement' }, [text(claim.statement)]),
        h('div', { class: 'node-meta' }, [
            h('span', {}, [text(`Confidence: ${Math.round((claim.confidence || 0.5) * 100)}%`)]),
        ]),
    ])
);

const IngestPanel = (ingestUrl, ingesting, ingestProgress) => (
    h('div', { class: 'ingest-panel' }, [
        h('h3', {}, [text('Ingest Source')]),
        h('div', { class: 'ingest-form' }, [
            h('input', {
                type: 'url',
                class: 'ingest-input',
                placeholder: 'YouTube URL, web page, or PDF...',
                value: ingestUrl,
                disabled: ingesting,
                oninput: (state, event) => SetIngestUrl(state, event.target.value),
            }),
            h('button', {
                class: 'action-btn primary',
                disabled: ingesting || !ingestUrl,
                onclick: (state) => [state, [startIngestionFx, state.ingestUrl]],
            }, [text(ingesting ? 'Ingesting...' : '→ Ingest')]),
        ]),
        ingesting && ingestProgress ? IngestProgress(ingestProgress) : null,
    ])
);

const IngestProgress = (progress) => (
    h('div', { class: 'ingest-progress' }, [
        h('div', { class: 'progress-stage' }, [
            text(`Stage: ${progress.stage || 'processing'}`),
        ]),
        progress.claims_extracted !== undefined ?
            h('div', { class: 'progress-stats' }, [
                text(`Claims: ${progress.claims_extracted} | Entities: ${progress.entities_found || 0}`),
            ]) : null,
        h('div', { class: 'progress-bar' }, [
            h('div', {
                class: 'progress-fill',
                style: { width: `${(progress.percent || 0) * 100}%` }
            }),
        ]),
    ])
);

const GapsPanel = (gaps) => (
    h('div', { class: 'gaps-panel' }, [
        h('h3', {}, [text('Knowledge Gaps')]),
        gaps.length === 0 ?
            h('p', { class: 'empty-state' }, [text('No gaps detected')]) :
            h('div', { class: 'gap-list' },
                gaps.map(gap => GapCard(gap))
            ),
    ])
);

const GapCard = (gap) => (
    h('div', { class: `gap-card severity-${gap.severity || 'medium'}` }, [
        h('div', { class: 'gap-description' }, [text(gap.description)]),
        h('div', { class: 'gap-meta' }, [
            gap.severity ? h('span', { class: 'gap-severity' }, [text(gap.severity)]) : null,
        ]),
        h('button', { class: 'action-btn small' }, [text('Research')]),
    ])
);

const Sidebar = (state) => (
    h('aside', { class: 'sidebar' }, [
        PanelTabs(state.activePanel),
        state.activePanel === 'knowledge' ?
            KnowledgePanel(state.entities, state.claims, state.selectedNodeId) :
            state.activePanel === 'ingest' ?
                IngestPanel(state.ingestUrl, state.ingesting, state.ingestProgress) :
                state.activePanel === 'gaps' ?
                    GapsPanel(state.gaps) :
                    null,
    ])
);

const Canvas3D = () => (
    h('canvas', { id: 'neuro-canvas', class: 'neuro-canvas' })
);

const LoadingOverlay = (loading, error) => (
    h('div', { class: `loading-overlay ${loading ? '' : 'hidden'}` }, [
        error ?
            h('div', { class: 'error-state' }, [
                h('span', { class: 'error-icon' }, [text('⚠')]),
                h('span', {}, [text(error)]),
                h('button', {
                    class: 'action-btn',
                    onclick: (state) => [state, fetchInitialDataFx]
                }, [text('Retry')]),
            ]) :
            h('div', { class: 'loading-state' }, [
                h('div', { class: 'loading-spinner' }),
                h('span', {}, [text('Connecting to Inception...')]),
            ]),
    ])
);

const ConnectionIndicator = (connected) => (
    h('div', { class: `connection-indicator ${connected ? 'connected' : 'disconnected'}` }, [
        h('span', { class: 'indicator-dot' }),
        h('span', {}, [text(connected ? 'Connected' : 'Offline')]),
    ])
);

// ============================================================
// MAIN VIEW
// ============================================================

const view = (state) => (
    h('div', { class: 'neuro-app' }, [
        Header(),
        ConnectionIndicator(state.connected),
        h('div', { class: 'main-layout' }, [
            Sidebar(state),
            h('main', { class: 'main-content' }, [
                StatsBar(state.stats, state.connected),
                h('div', { class: 'canvas-wrapper' }, [
                    Canvas3D(),
                    LoadingOverlay(state.loading, state.error),
                ]),
            ]),
        ]),
    ])
);

// ============================================================
// APP INIT
// ============================================================

app({
    init: [initialState, [fetchInitialDataFx], [initSceneFx]],
    view,
    node: document.getElementById('app'),
});

console.log('[Inception] PURPOSE-FIRST Neurosymbolic Interface');
console.log('[Inception] Every visual = real data. No placeholders.');
