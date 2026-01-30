// ════════════════════════════════════════════════════════════════════════════
// KNOWLEDGE FORCE GRAPH — D3.js Force-Directed Layout
//
// COGNITIVE PURPOSE: Explore the topology of knowledge connections
// TECH: D3.js force simulation with SVG, rich interactions
// ANTI-CORPORATE: Organic clustering, no grid, emergent structure
// ════════════════════════════════════════════════════════════════════════════

import { DataContracts } from '../lib/mock-data.js';

export class KnowledgeForceGraph {
    constructor(container) {
        this.container = container;
        this.data = this.prepareData();
        this.svg = null;
        this.simulation = null;
        this.width = container.clientWidth;
        this.height = container.clientHeight;
    }

    prepareData() {
        const raw = DataContracts.getSemanticNebula();
        // SemanticNebula returns 'nodes' not 'entities'
        return {
            nodes: (raw.nodes || []).map(n => ({
                id: n.id,
                name: n.id, // nodes from mock data use id, not name
                type: n.group?.includes('auth') ? 'Entity' :
                    n.group?.includes('storage') ? 'Source' :
                        n.id?.startsWith('c') ? 'Claim' : 'Entity',
                confidence: n.size ? n.size / 20 : 0.7,
                fx: null, fy: null,
            })),
            links: (raw.links || []).map(l => ({
                source: l.source,
                target: l.target,
                type: l.type || 'references',
                strength: l.strength || 0.5,
            })),
        };
    }

    async init() {
        // Dynamic D3 import
        const d3 = await import('https://esm.sh/d3@7');
        this.d3 = d3;

        // SVG container
        this.svg = d3.select(this.container)
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height)
            .style('background', '#000');

        // Definitions for gradients and filters
        const defs = this.svg.append('defs');

        // Glow filter
        const glow = defs.append('filter')
            .attr('id', 'glow')
            .attr('x', '-50%')
            .attr('y', '-50%')
            .attr('width', '200%')
            .attr('height', '200%');
        glow.append('feGaussianBlur')
            .attr('stdDeviation', '3')
            .attr('result', 'coloredBlur');
        const glowMerge = glow.append('feMerge');
        glowMerge.append('feMergeNode').attr('in', 'coloredBlur');
        glowMerge.append('feMergeNode').attr('in', 'SourceGraphic');

        // Link gradient
        const linkGrad = defs.append('linearGradient')
            .attr('id', 'linkGradient')
            .attr('gradientUnits', 'userSpaceOnUse');
        linkGrad.append('stop').attr('offset', '0%').attr('stop-color', '#1a1a2e');
        linkGrad.append('stop').attr('offset', '50%').attr('stop-color', '#3a3a5e');
        linkGrad.append('stop').attr('offset', '100%').attr('stop-color', '#1a1a2e');

        // Force simulation
        this.simulation = d3.forceSimulation(this.data.nodes)
            .force('link', d3.forceLink(this.data.links)
                .id(d => d.id)
                .distance(d => 100 - d.strength * 50)
                .strength(d => d.strength * 0.5))
            .force('charge', d3.forceManyBody()
                .strength(d => -200 - d.confidence * 100))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(30))
            .force('x', d3.forceX(this.width / 2).strength(0.02))
            .force('y', d3.forceY(this.height / 2).strength(0.02));

        // Links
        this.linkElements = this.svg.selectAll('.link')
            .data(this.data.links)
            .enter()
            .append('line')
            .attr('class', 'link')
            .attr('stroke', d => this.getLinkColor(d.type))
            .attr('stroke-width', d => 1 + d.strength * 3)
            .attr('stroke-opacity', d => 0.2 + d.strength * 0.3);

        // Node groups
        this.nodeGroups = this.svg.selectAll('.node')
            .data(this.data.nodes)
            .enter()
            .append('g')
            .attr('class', 'node')
            .call(d3.drag()
                .on('start', (e, d) => this.dragStart(e, d))
                .on('drag', (e, d) => this.dragging(e, d))
                .on('end', (e, d) => this.dragEnd(e, d)));

        // Node circles
        this.nodeGroups.append('circle')
            .attr('r', d => 8 + d.confidence * 12)
            .attr('fill', d => this.getNodeColor(d.type))
            .attr('stroke', d => this.getNodeStroke(d.type))
            .attr('stroke-width', 2)
            .attr('filter', 'url(#glow)')
            .style('cursor', 'grab');

        // Confidence ring
        this.nodeGroups.append('circle')
            .attr('r', d => 12 + d.confidence * 15)
            .attr('fill', 'none')
            .attr('stroke', d => this.getNodeColor(d.type))
            .attr('stroke-width', 1)
            .attr('stroke-opacity', 0.3)
            .attr('stroke-dasharray', d => {
                const circumference = 2 * Math.PI * (12 + d.confidence * 15);
                return `${circumference * d.confidence} ${circumference}`;
            });

        // Labels
        this.nodeGroups.append('text')
            .text(d => d.name.length > 15 ? d.name.slice(0, 12) + '…' : d.name)
            .attr('x', 0)
            .attr('y', d => 25 + d.confidence * 10)
            .attr('text-anchor', 'middle')
            .attr('fill', '#666')
            .attr('font-size', '9px')
            .attr('font-family', 'monospace');

        // Hover interactions
        this.nodeGroups
            .on('mouseenter', (e, d) => this.hoverNode(d, true))
            .on('mouseleave', (e, d) => this.hoverNode(d, false));

        // Tick update
        this.simulation.on('tick', () => this.tick());

        // Legend
        this.renderLegend();
    }

    getNodeColor(type) {
        const colors = {
            Entity: '#64ffda',
            Claim: '#bd93f9',
            Source: '#ffd93d',
            Gap: '#ff6b9d',
        };
        return colors[type] || '#8892b0';
    }

    getNodeStroke(type) {
        const strokes = {
            Entity: '#4ecdc4',
            Claim: '#9d73d9',
            Source: '#ddb92d',
            Gap: '#df4b7d',
        };
        return strokes[type] || '#6872a0';
    }

    getLinkColor(type) {
        const colors = {
            supports: '#44aa88',
            contradicts: '#aa4466',
            contains: '#6688aa',
            references: '#888888',
        };
        return colors[type] || '#444466';
    }

    tick() {
        this.linkElements
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        this.nodeGroups
            .attr('transform', d => `translate(${d.x}, ${d.y})`);
    }

    dragStart(event, d) {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    dragging(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    dragEnd(event, d) {
        if (!event.active) this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }

    hoverNode(node, isHover) {
        const opacity = isHover ? 1 : 0.2;
        const connectedIds = new Set([node.id]);

        this.data.links.forEach(l => {
            const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
            const targetId = typeof l.target === 'object' ? l.target.id : l.target;
            if (sourceId === node.id) connectedIds.add(targetId);
            if (targetId === node.id) connectedIds.add(sourceId);
        });

        if (isHover) {
            this.nodeGroups.style('opacity', d => connectedIds.has(d.id) ? 1 : 0.2);
            this.linkElements.style('opacity', d => {
                const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
                const targetId = typeof d.target === 'object' ? d.target.id : d.target;
                return (sourceId === node.id || targetId === node.id) ? 0.8 : 0.05;
            });
        } else {
            this.nodeGroups.style('opacity', 1);
            this.linkElements.style('opacity', d => 0.2 + d.strength * 0.3);
        }
    }

    renderLegend() {
        const legend = this.svg.append('g')
            .attr('transform', `translate(20, ${this.height - 80})`);

        const types = ['Entity', 'Claim', 'Source', 'Gap'];
        types.forEach((type, i) => {
            legend.append('circle')
                .attr('cx', i * 70)
                .attr('cy', 0)
                .attr('r', 5)
                .attr('fill', this.getNodeColor(type));

            legend.append('text')
                .attr('x', i * 70)
                .attr('y', 15)
                .attr('text-anchor', 'middle')
                .attr('fill', '#555')
                .attr('font-size', '8px')
                .attr('font-family', 'monospace')
                .text(type);
        });
    }

    dispose() {
        this.simulation?.stop();
        this.svg?.remove();
    }
}

export default KnowledgeForceGraph;
