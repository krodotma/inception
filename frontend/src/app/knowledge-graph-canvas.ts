/**
 * KINESIS Knowledge Graph Canvas
 * 
 * Priority 1 from Architect Review: Make the invisible visible.
 * D3 force-directed graph showing claims, entities, and relationships.
 * 
 * Based on existing graph.js patterns + KINESIS motion tokens.
 */

import * as d3 from 'd3';

// =============================================================================
// TYPES
// =============================================================================

interface GraphNode {
    id: string;
    type: 'entity' | 'claim' | 'procedure' | 'skill' | 'gap';
    label: string;
    confidence: number;
    wikidataId?: string;
    sources: string[];
    x?: number;
    y?: number;
    fx?: number | null;
    fy?: number | null;
}

interface GraphEdge {
    source: string;
    target: string;
    relation: string;
    strength: number;
}

interface GraphData {
    nodes: GraphNode[];
    edges: GraphEdge[];
}

// =============================================================================
// M3 MOTION TOKENS (inline from motion-tokens.css)
// =============================================================================

const MOTION = {
    duration: {
        short: 150,
        medium: 300,
        long: 500,
        extraLong: 800,
    },
    easing: {
        emphasized: 'cubic-bezier(0.2, 0, 0, 1)',
        decelerate: 'cubic-bezier(0.05, 0.7, 0.1, 1)',
        accelerate: 'cubic-bezier(0.3, 0, 0.8, 0.15)',
    },
    spring: {
        gentle: { stiffness: 100, damping: 15 },
        default: { stiffness: 170, damping: 26 },
        snappy: { stiffness: 400, damping: 40 },
    },
};

// =============================================================================
// COLOR PALETTE (confidence-based)
// =============================================================================

const COLORS = {
    entity: '#8B5CF6',      // Purple
    claim: '#3B82F6',       // Blue  
    procedure: '#10B981',   // Green
    skill: '#F59E0B',       // Amber
    gap: '#EF4444',         // Red (attention)

    // Confidence gradients
    confident: '#22C55E',   // Green (>0.9)
    moderate: '#EAB308',    // Yellow (0.6-0.9)
    uncertain: '#F97316',   // Orange (0.3-0.6)
    unknown: '#DC2626',     // Red (<0.3)

    edge: 'rgba(148, 163, 184, 0.4)',
    edgeHover: 'rgba(148, 163, 184, 0.8)',
};

// =============================================================================
// KNOWLEDGE GRAPH CANVAS
// =============================================================================

export class KnowledgeGraphCanvas {
    private container: HTMLElement;
    private svg: d3.Selection<SVGSVGElement, unknown, null, undefined>;
    private simulation: d3.Simulation<GraphNode, GraphEdge>;
    private width: number;
    private height: number;

    private nodes: GraphNode[] = [];
    private edges: GraphEdge[] = [];

    private nodeSelection: d3.Selection<SVGGElement, GraphNode, SVGGElement, unknown> | null = null;
    private edgeSelection: d3.Selection<SVGLineElement, GraphEdge, SVGGElement, unknown> | null = null;

    // State
    private selectedNode: GraphNode | null = null;
    private hoveredNode: GraphNode | null = null;
    private zoomLevel = 1;

    // Callbacks
    onNodeClick?: (node: GraphNode) => void;
    onNodeHover?: (node: GraphNode | null) => void;
    onGapClick?: (gap: GraphNode) => void;

    constructor(container: HTMLElement) {
        this.container = container;
        this.width = container.clientWidth;
        this.height = container.clientHeight;

        // Create SVG
        this.svg = d3.select(container)
            .append('svg')
            .attr('width', '100%')
            .attr('height', '100%')
            .attr('viewBox', `0 0 ${this.width} ${this.height}`)
            .attr('class', 'knowledge-graph-canvas')
            .style('background', 'var(--md-sys-color-background)');

        // Add defs for gradients/filters
        this.createDefs();

        // Create layers
        this.svg.append('g').attr('class', 'edges-layer');
        this.svg.append('g').attr('class', 'nodes-layer');
        this.svg.append('g').attr('class', 'labels-layer');

        // Initialize force simulation
        this.simulation = d3.forceSimulation<GraphNode>()
            .force('link', d3.forceLink<GraphNode, GraphEdge>()
                .id(d => d.id)
                .distance(100)
                .strength(d => d.strength))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(40));

        // Add zoom
        const zoom = d3.zoom<SVGSVGElement, unknown>()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                this.svg.selectAll('g').attr('transform', event.transform);
                this.zoomLevel = event.transform.k;
            });

        this.svg.call(zoom);

        // Resize observer
        const resizeObserver = new ResizeObserver(() => this.handleResize());
        resizeObserver.observe(container);
    }

    // ---------------------------------------------------------------------------
    // DEFS (gradients, filters)
    // ---------------------------------------------------------------------------

    private createDefs(): void {
        const defs = this.svg.append('defs');

        // Glow filter for gaps
        const glow = defs.append('filter')
            .attr('id', 'glow-gap')
            .attr('x', '-50%')
            .attr('y', '-50%')
            .attr('width', '200%')
            .attr('height', '200%');

        glow.append('feGaussianBlur')
            .attr('stdDeviation', '3')
            .attr('result', 'blur');

        glow.append('feMerge')
            .selectAll('feMergeNode')
            .data(['blur', 'SourceGraphic'])
            .enter()
            .append('feMergeNode')
            .attr('in', d => d);

        // Gradient for confidence
        const confGradient = defs.append('radialGradient')
            .attr('id', 'confidence-gradient');

        confGradient.append('stop')
            .attr('offset', '0%')
            .attr('stop-color', COLORS.confident);

        confGradient.append('stop')
            .attr('offset', '100%')
            .attr('stop-color', 'transparent');
    }

    // ---------------------------------------------------------------------------
    // DATA LOADING
    // ---------------------------------------------------------------------------

    public setData(data: GraphData): void {
        this.nodes = data.nodes;
        this.edges = data.edges;

        this.render();

        // Start simulation
        this.simulation
            .nodes(this.nodes)
            .on('tick', () => this.tick());

        (this.simulation.force('link') as d3.ForceLink<GraphNode, GraphEdge>)
            .links(this.edges);

        this.simulation.alpha(1).restart();
    }

    public async loadFromAPI(endpoint: string): Promise<void> {
        try {
            const response = await fetch(endpoint);
            const data = await response.json();

            // Transform API data to graph format
            const graphData = this.transformAPIData(data);
            this.setData(graphData);
        } catch (error) {
            console.error('Failed to load graph data:', error);
        }
    }

    private transformAPIData(apiData: any): GraphData {
        const nodes: GraphNode[] = [];
        const edges: GraphEdge[] = [];

        // Transform entities
        if (apiData.entities) {
            for (const entity of apiData.entities) {
                nodes.push({
                    id: entity.id,
                    type: 'entity',
                    label: entity.name || entity.text,
                    confidence: entity.confidence || 0.8,
                    wikidataId: entity.wikidata_id,
                    sources: entity.sources || [],
                });
            }
        }

        // Transform claims
        if (apiData.claims) {
            for (const claim of apiData.claims) {
                nodes.push({
                    id: claim.id,
                    type: 'claim',
                    label: claim.text?.slice(0, 50) + '...' || claim.subject,
                    confidence: claim.confidence?.epistemic || 0.7,
                    sources: claim.sources || [],
                });

                // Create edge from subject entity to claim
                if (claim.subject_id) {
                    edges.push({
                        source: claim.subject_id,
                        target: claim.id,
                        relation: 'asserts',
                        strength: 0.5,
                    });
                }
            }
        }

        // Transform gaps
        if (apiData.gaps) {
            for (const gap of apiData.gaps) {
                nodes.push({
                    id: gap.id,
                    type: 'gap',
                    label: gap.description || 'Unknown gap',
                    confidence: 0,
                    sources: [],
                });
            }
        }

        return { nodes, edges };
    }

    // ---------------------------------------------------------------------------
    // RENDERING
    // ---------------------------------------------------------------------------

    private render(): void {
        // Render edges
        this.edgeSelection = this.svg.select('.edges-layer')
            .selectAll<SVGLineElement, GraphEdge>('line')
            .data(this.edges)
            .join(
                enter => enter.append('line')
                    .attr('stroke', COLORS.edge)
                    .attr('stroke-width', d => Math.max(1, d.strength * 3))
                    .attr('stroke-opacity', 0)
                    .call(sel => sel.transition()
                        .duration(MOTION.duration.medium)
                        .attr('stroke-opacity', 1)),
                update => update,
                exit => exit
                    .transition()
                    .duration(MOTION.duration.short)
                    .attr('stroke-opacity', 0)
                    .remove()
            );

        // Render nodes
        this.nodeSelection = this.svg.select('.nodes-layer')
            .selectAll<SVGGElement, GraphNode>('g.node')
            .data(this.nodes, d => d.id)
            .join(
                enter => {
                    const g = enter.append('g')
                        .attr('class', 'node')
                        .attr('cursor', 'pointer')
                        .attr('opacity', 0)
                        .call(this.setupDrag())
                        .on('click', (event, d) => this.handleNodeClick(d))
                        .on('mouseenter', (event, d) => this.handleNodeHover(d))
                        .on('mouseleave', () => this.handleNodeHover(null));

                    // Circle
                    g.append('circle')
                        .attr('r', d => this.getNodeRadius(d))
                        .attr('fill', d => this.getNodeColor(d))
                        .attr('stroke', 'rgba(255,255,255,0.2)')
                        .attr('stroke-width', 2)
                        .attr('filter', d => d.type === 'gap' ? 'url(#glow-gap)' : null);

                    // Confidence ring
                    g.append('circle')
                        .attr('class', 'confidence-ring')
                        .attr('r', d => this.getNodeRadius(d) + 4)
                        .attr('fill', 'none')
                        .attr('stroke', d => this.getConfidenceColor(d.confidence))
                        .attr('stroke-width', 2)
                        .attr('stroke-dasharray', d => this.getConfidenceDash(d.confidence));

                    // Label
                    g.append('text')
                        .attr('dy', d => this.getNodeRadius(d) + 16)
                        .attr('text-anchor', 'middle')
                        .attr('class', 'node-label')
                        .attr('fill', 'var(--md-sys-color-on-surface)')
                        .attr('font-size', '11px')
                        .text(d => d.label.slice(0, 20));

                    // Fade in
                    g.transition()
                        .duration(MOTION.duration.medium)
                        .ease(d3.easeCubicOut)
                        .attr('opacity', 1);

                    return g;
                },
                update => update,
                exit => exit
                    .transition()
                    .duration(MOTION.duration.short)
                    .attr('opacity', 0)
                    .remove()
            );
    }

    private tick(): void {
        this.edgeSelection
            ?.attr('x1', d => (d.source as GraphNode).x!)
            .attr('y1', d => (d.source as GraphNode).y!)
            .attr('x2', d => (d.target as GraphNode).x!)
            .attr('y2', d => (d.target as GraphNode).y!);

        this.nodeSelection
            ?.attr('transform', d => `translate(${d.x}, ${d.y})`);
    }

    // ---------------------------------------------------------------------------
    // HELPERS
    // ---------------------------------------------------------------------------

    private getNodeRadius(node: GraphNode): number {
        const baseRadius = {
            entity: 20,
            claim: 15,
            procedure: 18,
            skill: 22,
            gap: 12,
        };
        return baseRadius[node.type] || 15;
    }

    private getNodeColor(node: GraphNode): string {
        return COLORS[node.type] || COLORS.entity;
    }

    private getConfidenceColor(confidence: number): string {
        if (confidence > 0.9) return COLORS.confident;
        if (confidence > 0.6) return COLORS.moderate;
        if (confidence > 0.3) return COLORS.uncertain;
        return COLORS.unknown;
    }

    private getConfidenceDash(confidence: number): string {
        if (confidence > 0.9) return '0';  // Solid
        if (confidence > 0.6) return '4 2';  // Dashed
        if (confidence > 0.3) return '2 2';  // Dotted
        return '1 3';  // Sparse dots
    }

    // ---------------------------------------------------------------------------
    // INTERACTIONS
    // ---------------------------------------------------------------------------

    private setupDrag(): d3.DragBehavior<SVGGElement, GraphNode, GraphNode> {
        return d3.drag<SVGGElement, GraphNode>()
            .on('start', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            })
            .on('drag', (event, d) => {
                d.fx = event.x;
                d.fy = event.y;
            })
            .on('end', (event, d) => {
                if (!event.active) this.simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            });
    }

    private handleNodeClick(node: GraphNode): void {
        this.selectedNode = node;

        // Highlight selected
        this.nodeSelection?.select('circle')
            .transition()
            .duration(MOTION.duration.short)
            .attr('stroke-width', d => d.id === node.id ? 4 : 2);

        if (node.type === 'gap' && this.onGapClick) {
            this.onGapClick(node);
        } else if (this.onNodeClick) {
            this.onNodeClick(node);
        }
    }

    private handleNodeHover(node: GraphNode | null): void {
        this.hoveredNode = node;

        // Scale on hover
        this.nodeSelection?.select('circle')
            .transition()
            .duration(MOTION.duration.short)
            .attr('r', d => {
                const base = this.getNodeRadius(d);
                return d.id === node?.id ? base * 1.2 : base;
            });

        // Highlight connected edges
        this.edgeSelection
            ?.transition()
            .duration(MOTION.duration.short)
            .attr('stroke', d => {
                if (!node) return COLORS.edge;
                const sourceId = typeof d.source === 'string' ? d.source : d.source.id;
                const targetId = typeof d.target === 'string' ? d.target : d.target.id;
                return (sourceId === node.id || targetId === node.id)
                    ? COLORS.edgeHover
                    : COLORS.edge;
            });

        if (this.onNodeHover) {
            this.onNodeHover(node);
        }
    }

    // ---------------------------------------------------------------------------
    // PUBLIC API
    // ---------------------------------------------------------------------------

    public focusOnNode(nodeId: string): void {
        const node = this.nodes.find(n => n.id === nodeId);
        if (!node || !node.x || !node.y) return;

        const transform = d3.zoomIdentity
            .translate(this.width / 2, this.height / 2)
            .scale(2)
            .translate(-node.x, -node.y);

        this.svg.transition()
            .duration(MOTION.duration.long)
            .call(d3.zoom<SVGSVGElement, unknown>().transform as any, transform);
    }

    public highlightGaps(): void {
        const gaps = this.nodes.filter(n => n.type === 'gap');

        this.nodeSelection
            ?.filter(d => d.type === 'gap')
            .select('circle')
            .transition()
            .duration(MOTION.duration.medium)
            .attr('r', d => this.getNodeRadius(d) * 1.5)
            .transition()
            .duration(MOTION.duration.medium)
            .attr('r', d => this.getNodeRadius(d));
    }

    public setRheoModeLevel(level: number): void {
        // Adjust visibility based on RheoMode level
        // 0 = Gist (show only entities)
        // 4 = Skills (show everything)

        const visibleTypes: Record<number, Set<string>> = {
            0: new Set(['entity']),
            1: new Set(['entity', 'claim']),
            2: new Set(['entity', 'claim', 'gap']),
            3: new Set(['entity', 'claim', 'gap', 'procedure']),
            4: new Set(['entity', 'claim', 'gap', 'procedure', 'skill']),
        };

        const visible = visibleTypes[level] || visibleTypes[4];

        this.nodeSelection
            ?.transition()
            .duration(MOTION.duration.medium)
            .attr('opacity', d => visible.has(d.type) ? 1 : 0.2);
    }

    private handleResize(): void {
        this.width = this.container.clientWidth;
        this.height = this.container.clientHeight;

        this.svg.attr('viewBox', `0 0 ${this.width} ${this.height}`);

        this.simulation
            .force('center', d3.forceCenter(this.width / 2, this.height / 2));

        this.simulation.alpha(0.3).restart();
    }

    public destroy(): void {
        this.simulation.stop();
        this.svg.remove();
    }
}

// =============================================================================
// EXPORTS
// =============================================================================

export function initKnowledgeGraph(container: HTMLElement): KnowledgeGraphCanvas {
    return new KnowledgeGraphCanvas(container);
}
