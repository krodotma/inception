/**
 * D3 Force Graph - Agent Auth Provider Visualization
 * 
 * Creates a force-directed graph showing:
 * - Provider nodes with status-based coloring
 * - Connection links to central Inception node
 * - Interactive drag and zoom
 * - Real-time status updates
 */

import * as d3 from 'd3';

// Provider configuration
const PROVIDERS = [
    { id: 'inception', name: 'Inception', color: '#fff', type: 'center', connected: true },
    { id: 'claude', name: 'Claude', model: 'Opus 4.5', color: '#8B5CF6', type: 'provider', connected: true },
    { id: 'gemini', name: 'Gemini', model: '2.5 Flash', color: '#4285F4', type: 'provider', connected: true },
    { id: 'codex', name: 'Codex', model: 'gpt-5.2-codex', color: '#10B981', type: 'provider', connected: true },
    { id: 'kimi', name: 'Kimi', model: 'API Key', color: '#F59E0B', type: 'provider', connected: false }
];

// Links from center to each provider
const LINKS = [
    { source: 'inception', target: 'claude' },
    { source: 'inception', target: 'gemini' },
    { source: 'inception', target: 'codex' },
    { source: 'inception', target: 'kimi' }
];

class AgentAuthD3Graph {
    constructor(container, options = {}) {
        this.container = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        this.options = {
            width: 500,
            height: 350,
            nodeRadius: 24,
            linkDistance: 120,
            chargeStrength: -400,
            ...options
        };

        this.svg = null;
        this.simulation = null;
        this.nodes = JSON.parse(JSON.stringify(PROVIDERS));
        this.links = JSON.parse(JSON.stringify(LINKS));

        this.init();
    }

    init() {
        const { width, height, nodeRadius, linkDistance, chargeStrength } = this.options;

        // Create SVG
        this.svg = d3.select(this.container)
            .append('svg')
            .attr('width', width)
            .attr('height', height)
            .attr('viewBox', [0, 0, width, height])
            .style('background', 'transparent');

        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.5, 3])
            .on('zoom', (event) => {
                this.g.attr('transform', event.transform);
            });

        this.svg.call(zoom);

        // Main group for zoom/pan
        this.g = this.svg.append('g');

        // Create gradient definitions for glow effect
        this.createGradients();

        // Force simulation
        this.simulation = d3.forceSimulation(this.nodes)
            .force('link', d3.forceLink(this.links)
                .id(d => d.id)
                .distance(linkDistance))
            .force('charge', d3.forceManyBody().strength(chargeStrength))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(nodeRadius + 10));

        // Create links
        this.linkElements = this.g.append('g')
            .attr('class', 'links')
            .selectAll('line')
            .data(this.links)
            .join('line')
            .attr('stroke', d => {
                const target = this.nodes.find(n => n.id === d.target.id || n.id === d.target);
                return target ? target.color : '#666';
            })
            .attr('stroke-opacity', 0.4)
            .attr('stroke-width', 2)
            .attr('stroke-dasharray', d => {
                const target = this.nodes.find(n => n.id === d.target.id || n.id === d.target);
                return target && target.connected ? 'none' : '5,5';
            });

        // Create nodes
        this.nodeElements = this.g.append('g')
            .attr('class', 'nodes')
            .selectAll('g')
            .data(this.nodes)
            .join('g')
            .attr('class', 'node')
            .call(this.drag());

        // Node circles
        this.nodeElements.append('circle')
            .attr('r', d => d.type === 'center' ? nodeRadius * 1.2 : nodeRadius)
            .attr('fill', d => `url(#gradient-${d.id})`)
            .attr('stroke', d => d.color)
            .attr('stroke-width', 2)
            .attr('stroke-opacity', d => d.connected ? 1 : 0.3);

        // Node labels
        this.nodeElements.append('text')
            .text(d => d.name)
            .attr('text-anchor', 'middle')
            .attr('dy', nodeRadius + 16)
            .attr('fill', '#fff')
            .attr('font-size', '11px')
            .attr('font-weight', '500');

        // Status indicator (small dot)
        this.nodeElements.filter(d => d.type === 'provider')
            .append('circle')
            .attr('class', 'status-dot')
            .attr('r', 6)
            .attr('cx', nodeRadius - 4)
            .attr('cy', -nodeRadius + 4)
            .attr('fill', d => d.connected ? '#22C55E' : '#EF4444');

        // Tooltip
        this.nodeElements.append('title')
            .text(d => `${d.name}${d.model ? ': ' + d.model : ''}`);

        // Tick function
        this.simulation.on('tick', () => {
            this.linkElements
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            this.nodeElements
                .attr('transform', d => `translate(${d.x}, ${d.y})`);
        });
    }

    createGradients() {
        const defs = this.svg.append('defs');

        this.nodes.forEach(node => {
            const gradient = defs.append('radialGradient')
                .attr('id', `gradient-${node.id}`)
                .attr('cx', '30%')
                .attr('cy', '30%');

            gradient.append('stop')
                .attr('offset', '0%')
                .attr('stop-color', node.color)
                .attr('stop-opacity', 0.8);

            gradient.append('stop')
                .attr('offset', '100%')
                .attr('stop-color', node.color)
                .attr('stop-opacity', node.connected ? 0.4 : 0.1);
        });
    }

    drag() {
        return d3.drag()
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

    /**
     * Update provider status
     * @param {string} provider - Provider ID
     * @param {boolean} connected - Connection status
     */
    updateStatus(provider, connected) {
        const node = this.nodes.find(n => n.id === provider);
        if (!node) return;

        node.connected = connected;

        // Update status dot
        this.nodeElements.filter(d => d.id === provider)
            .select('.status-dot')
            .transition()
            .duration(300)
            .attr('fill', connected ? '#22C55E' : '#EF4444');

        // Update node opacity
        this.nodeElements.filter(d => d.id === provider)
            .select('circle:first-of-type')
            .transition()
            .duration(300)
            .attr('stroke-opacity', connected ? 1 : 0.3);

        // Update link dash
        this.linkElements.filter(d =>
            d.target.id === provider || d.target === provider
        )
            .transition()
            .duration(300)
            .attr('stroke-dasharray', connected ? 'none' : '5,5')
            .attr('stroke-opacity', connected ? 0.6 : 0.2);
    }

    /**
     * Cluster nodes by status
     */
    clusterByStatus() {
        const { width, height } = this.options;

        // Connected cluster on left, disconnected on right
        this.simulation
            .force('x', d3.forceX(d => {
                if (d.type === 'center') return width / 2;
                return d.connected ? width * 0.35 : width * 0.65;
            }).strength(0.3))
            .force('y', d3.forceY(height / 2).strength(0.1))
            .alpha(0.5)
            .restart();
    }

    /**
     * Reset to default layout
     */
    resetLayout() {
        this.simulation
            .force('x', null)
            .force('y', null)
            .force('center', d3.forceCenter(this.options.width / 2, this.options.height / 2))
            .alpha(0.5)
            .restart();
    }

    /**
     * Cleanup
     */
    destroy() {
        this.simulation.stop();
        this.svg.remove();
    }
}

export { AgentAuthD3Graph };
export default AgentAuthD3Graph;
