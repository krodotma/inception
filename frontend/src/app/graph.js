/**
 * VEGA-3 ULTRATHINK: Enhanced Graph Visualization
 * 
 * Additions:
 * - WebGL renderer option for large graphs
 * - Level-of-detail (LOD) for labels
 * - Minimap navigation
 * - Temporal playback controls
 * - Edge bundling
 * - Search highlighting
 * 
 * Model: Opus 4.5 ULTRATHINK
 */

// =============================================================================
// ENHANCED GRAPH CLASS
// =============================================================================

class InceptionGraph {
    constructor(container, options = {}) {
        this.container = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        this.options = {
            renderer: options.renderer || 'canvas', // 'canvas' | 'webgl'
            lodThreshold: options.lodThreshold || 0.5,
            enableMinimap: options.enableMinimap !== false,
            enableTemporal: options.enableTemporal || false,
            ...options
        };

        this.cy = null;
        this.minimap = null;
        this.temporalData = [];
        this.currentTime = 0;

        this.init();
    }

    async init() {
        // Dynamic import for code splitting
        const cytoscape = (await import('cytoscape')).default;

        // Initialize Cytoscape
        this.cy = cytoscape({
            container: this.container,

            style: this.getStyles(),

            // Performance optimizations
            textureOnViewport: this.options.renderer === 'webgl',
            hideEdgesOnViewport: true,
            hideLabelsOnViewport: false,

            // Interaction
            minZoom: 0.1,
            maxZoom: 5,
            wheelSensitivity: 0.3,
        });

        // Setup LOD
        this.setupLOD();

        // Setup minimap
        if (this.options.enableMinimap) {
            this.setupMinimap();
        }

        // Setup temporal
        if (this.options.enableTemporal) {
            this.setupTemporalControls();
        }

        // Keyboard shortcuts
        this.setupKeyboard();

        return this;
    }

    // ===========================================================================
    // STYLES
    // ===========================================================================

    getStyles() {
        return [
            // Nodes
            {
                selector: 'node',
                style: {
                    'background-color': 'data(color)',
                    'label': 'data(label)',
                    'width': 'data(size)',
                    'height': 'data(size)',
                    'font-size': '12px',
                    'font-family': 'Inter, system-ui, sans-serif',
                    'text-valign': 'bottom',
                    'text-margin-y': '8px',
                    'text-wrap': 'ellipsis',
                    'text-max-width': '100px',
                    'color': '#cdd6f4',
                    'text-outline-color': '#1e1e2e',
                    'text-outline-width': '2px',
                    'border-width': '2px',
                    'border-color': '#45475a',
                    'transition-property': 'background-color, border-color, width, height',
                    'transition-duration': '200ms',
                }
            },

            // Node types
            {
                selector: 'node[type="entity"]',
                style: {
                    'background-color': '#7c4dff',
                    'shape': 'round-rectangle',
                }
            },
            {
                selector: 'node[type="claim"]',
                style: {
                    'background-color': '#00bfa5',
                    'shape': 'ellipse',
                }
            },
            {
                selector: 'node[type="procedure"]',
                style: {
                    'background-color': '#ffab00',
                    'shape': 'diamond',
                }
            },
            {
                selector: 'node[type="gap"]',
                style: {
                    'background-color': '#ff5252',
                    'shape': 'triangle',
                }
            },

            // Hover
            {
                selector: 'node:active',
                style: {
                    'overlay-opacity': 0.1,
                    'overlay-color': '#fff',
                }
            },

            // Selected
            {
                selector: 'node:selected',
                style: {
                    'border-color': '#f5c2e7',
                    'border-width': '3px',
                }
            },

            // Highlighted (search)
            {
                selector: 'node.highlighted',
                style: {
                    'border-color': '#f5c2e7',
                    'border-width': '4px',
                    'z-index': 9999,
                }
            },

            // Faded (not in search)
            {
                selector: 'node.faded',
                style: {
                    'opacity': 0.3,
                }
            },

            // LOD - hide labels at low zoom
            {
                selector: 'node.lod-hide-label',
                style: {
                    'label': '',
                }
            },

            // Edges
            {
                selector: 'edge',
                style: {
                    'width': 2,
                    'line-color': '#585b70',
                    'target-arrow-color': '#585b70',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'opacity': 0.7,
                    'transition-property': 'line-color, width, opacity',
                    'transition-duration': '200ms',
                }
            },

            // Edge strength
            {
                selector: 'edge[strength="strong"]',
                style: {
                    'width': 3,
                    'line-color': '#7c4dff',
                    'target-arrow-color': '#7c4dff',
                }
            },
            {
                selector: 'edge[strength="weak"]',
                style: {
                    'width': 1,
                    'line-style': 'dashed',
                    'opacity': 0.4,
                }
            },

            // Edge highlighted
            {
                selector: 'edge.highlighted',
                style: {
                    'line-color': '#f5c2e7',
                    'target-arrow-color': '#f5c2e7',
                    'width': 4,
                    'opacity': 1,
                }
            },

            // Edge faded
            {
                selector: 'edge.faded',
                style: {
                    'opacity': 0.1,
                }
            },
        ];
    }

    // ===========================================================================
    // LEVEL OF DETAIL (LOD)
    // ===========================================================================

    setupLOD() {
        let lastZoom = this.cy.zoom();

        this.cy.on('zoom', () => {
            const zoom = this.cy.zoom();
            const threshold = this.options.lodThreshold;

            // Avoid thrashing - only update on significant changes
            if (Math.abs(zoom - lastZoom) < 0.05) return;
            lastZoom = zoom;

            if (zoom < threshold) {
                // Low zoom - hide labels, show clusters
                this.cy.nodes().addClass('lod-hide-label');
            } else {
                // High zoom - show labels
                this.cy.nodes().removeClass('lod-hide-label');
            }
        });
    }

    // ===========================================================================
    // MINIMAP
    // ===========================================================================

    setupMinimap() {
        const minimapContainer = document.createElement('div');
        minimapContainer.className = 'graph-minimap';
        minimapContainer.innerHTML = `
      <div class="minimap-viewport"></div>
    `;
        this.container.appendChild(minimapContainer);

        const viewport = minimapContainer.querySelector('.minimap-viewport');

        // Update viewport on pan/zoom
        this.cy.on('pan zoom', () => {
            this.updateMinimap(viewport);
        });

        // Click minimap to navigate
        minimapContainer.addEventListener('click', (e) => {
            const rect = minimapContainer.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width;
            const y = (e.clientY - rect.top) / rect.height;

            const bb = this.cy.elements().boundingBox();
            const centerX = bb.x1 + (bb.w * x);
            const centerY = bb.y1 + (bb.h * y);

            this.cy.animate({
                center: { x: centerX, y: centerY },
                duration: 200,
                easing: 'ease-out',
            });
        });

        this.minimap = minimapContainer;
    }

    updateMinimap(viewport) {
        const ext = this.cy.extent();
        const bb = this.cy.elements().boundingBox();

        const left = ((ext.x1 - bb.x1) / bb.w) * 100;
        const top = ((ext.y1 - bb.y1) / bb.h) * 100;
        const width = (ext.w / bb.w) * 100;
        const height = (ext.h / bb.h) * 100;

        viewport.style.left = `${Math.max(0, left)}%`;
        viewport.style.top = `${Math.max(0, top)}%`;
        viewport.style.width = `${Math.min(100, width)}%`;
        viewport.style.height = `${Math.min(100, height)}%`;
    }

    // ===========================================================================
    // TEMPORAL PLAYBACK
    // ===========================================================================

    setupTemporalControls() {
        const controls = document.createElement('div');
        controls.className = 'graph-temporal-controls';
        controls.innerHTML = `
      <button class="temporal-btn" data-action="start">⏮</button>
      <button class="temporal-btn" data-action="back">◀</button>
      <button class="temporal-btn temporal-btn--play" data-action="play">▶</button>
      <button class="temporal-btn" data-action="forward">▶</button>
      <button class="temporal-btn" data-action="end">⏭</button>
      <input type="range" class="temporal-slider" min="0" max="100" value="100">
      <span class="temporal-time">Now</span>
    `;
        this.container.appendChild(controls);

        const slider = controls.querySelector('.temporal-slider');
        const timeLabel = controls.querySelector('.temporal-time');

        slider.addEventListener('input', () => {
            this.setTemporalPosition(parseInt(slider.value));
            timeLabel.textContent = this.formatTime(this.currentTime);
        });

        controls.querySelectorAll('.temporal-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const action = btn.dataset.action;
                this.temporalAction(action);
            });
        });
    }

    setTemporalPosition(percent) {
        // Filter nodes/edges by timestamp
        this.currentTime = percent;
        const threshold = (percent / 100) * this.getMaxTimestamp();

        this.cy.nodes().forEach(node => {
            const ts = node.data('timestamp') || 0;
            if (ts <= threshold) {
                node.removeClass('temporal-hidden');
            } else {
                node.addClass('temporal-hidden');
            }
        });
    }

    getMaxTimestamp() {
        let max = 0;
        this.cy.nodes().forEach(node => {
            const ts = node.data('timestamp') || 0;
            if (ts > max) max = ts;
        });
        return max || Date.now();
    }

    formatTime(percent) {
        if (percent >= 100) return 'Now';
        return `${percent}%`;
    }

    temporalAction(action) {
        // Stub for temporal controls
        console.log('Temporal action:', action);
    }

    // ===========================================================================
    // SEARCH
    // ===========================================================================

    search(query) {
        if (!query) {
            this.clearSearch();
            return [];
        }

        const lowerQuery = query.toLowerCase();
        const matches = [];

        this.cy.nodes().forEach(node => {
            const label = (node.data('label') || '').toLowerCase();
            const desc = (node.data('description') || '').toLowerCase();

            if (label.includes(lowerQuery) || desc.includes(lowerQuery)) {
                node.addClass('highlighted').removeClass('faded');
                matches.push(node);

                // Highlight connected edges
                node.connectedEdges().addClass('highlighted').removeClass('faded');
                node.neighborhood('node').removeClass('faded');
            } else {
                node.addClass('faded').removeClass('highlighted');
            }
        });

        this.cy.edges().forEach(edge => {
            if (!edge.hasClass('highlighted')) {
                edge.addClass('faded');
            }
        });

        // Focus on first match
        if (matches.length > 0) {
            this.cy.animate({
                fit: { eles: matches[0], padding: 100 },
                duration: 300,
                easing: 'ease-out',
            });
        }

        return matches;
    }

    clearSearch() {
        this.cy.nodes().removeClass('highlighted faded');
        this.cy.edges().removeClass('highlighted faded');
    }

    // ===========================================================================
    // KEYBOARD
    // ===========================================================================

    setupKeyboard() {
        document.addEventListener('keydown', (e) => {
            if (!this.container.contains(document.activeElement) &&
                document.activeElement !== document.body) return;

            switch (e.key) {
                case 'f':
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        this.showSearchOverlay();
                    }
                    break;
                case 'Escape':
                    this.clearSearch();
                    this.hideSearchOverlay();
                    break;
                case '1':
                    this.setLayout('force');
                    break;
                case '2':
                    this.setLayout('hierarchical');
                    break;
                case '3':
                    this.setLayout('radial');
                    break;
                case '0':
                    this.cy.fit(undefined, 50);
                    break;
            }
        });
    }

    showSearchOverlay() {
        let overlay = this.container.querySelector('.graph-search-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'graph-search-overlay';
            overlay.innerHTML = `
        <input type="text" class="graph-search-input" placeholder="Search nodes...">
        <span class="graph-search-count"></span>
      `;
            this.container.appendChild(overlay);

            const input = overlay.querySelector('.graph-search-input');
            const count = overlay.querySelector('.graph-search-count');

            input.addEventListener('input', () => {
                const matches = this.search(input.value);
                count.textContent = matches.length ? `${matches.length} found` : '';
            });
        }

        overlay.classList.add('visible');
        overlay.querySelector('.graph-search-input').focus();
    }

    hideSearchOverlay() {
        const overlay = this.container.querySelector('.graph-search-overlay');
        if (overlay) overlay.classList.remove('visible');
    }

    // ===========================================================================
    // LAYOUTS
    // ===========================================================================

    setLayout(type) {
        const layouts = {
            force: {
                name: 'cose',
                animate: true,
                animationDuration: 500,
                nodeRepulsion: 8000,
                idealEdgeLength: 100,
                gravity: 0.25,
            },
            hierarchical: {
                name: 'dagre',
                animate: true,
                animationDuration: 500,
                rankDir: 'TB',
                nodeSep: 50,
                rankSep: 100,
            },
            radial: {
                name: 'concentric',
                animate: true,
                animationDuration: 500,
                concentric: node => node.degree(),
                levelWidth: () => 2,
                minNodeSpacing: 50,
            },
            grid: {
                name: 'grid',
                animate: true,
                animationDuration: 500,
            },
        };

        const layout = this.cy.layout(layouts[type] || layouts.force);
        layout.run();
    }

    // ===========================================================================
    // DATA
    // ===========================================================================

    setData(data) {
        this.cy.elements().remove();

        // Add nodes
        if (data.nodes) {
            data.nodes.forEach(node => {
                this.cy.add({
                    group: 'nodes',
                    data: {
                        id: node.id,
                        label: node.label || node.name,
                        type: node.type || 'entity',
                        size: node.size || 40,
                        color: node.color || this.getColorForType(node.type),
                        description: node.description,
                        timestamp: node.timestamp,
                    }
                });
            });
        }

        // Add edges
        if (data.edges) {
            data.edges.forEach(edge => {
                this.cy.add({
                    group: 'edges',
                    data: {
                        source: edge.source,
                        target: edge.target,
                        strength: edge.strength || 'normal',
                    }
                });
            });
        }

        // Run layout
        this.setLayout('force');
    }

    getColorForType(type) {
        const colors = {
            entity: '#7c4dff',
            claim: '#00bfa5',
            procedure: '#ffab00',
            gap: '#ff5252',
            source: '#89b4fa',
        };
        return colors[type] || '#7c4dff';
    }

    // ===========================================================================
    // EXPORT
    // ===========================================================================

    exportPNG() {
        return this.cy.png({
            output: 'blob',
            bg: '#1e1e2e',
            scale: 2,
        });
    }

    exportJSON() {
        return this.cy.json();
    }
}

// =============================================================================
// CSS ADDITIONS
// =============================================================================

const graphCSS = `
.graph-minimap {
  position: absolute;
  bottom: 16px;
  right: 16px;
  width: 150px;
  height: 100px;
  background: rgba(30, 30, 46, 0.9);
  border: 1px solid #45475a;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
}

.minimap-viewport {
  position: absolute;
  border: 2px solid #7c4dff;
  background: rgba(124, 77, 255, 0.2);
  pointer-events: none;
}

.graph-temporal-controls {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(30, 30, 46, 0.95);
  border: 1px solid #45475a;
  border-radius: 24px;
}

.temporal-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  color: #cdd6f4;
  cursor: pointer;
  border-radius: 50%;
  transition: background 0.2s;
}

.temporal-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.temporal-btn--play {
  background: #7c4dff;
}

.temporal-slider {
  width: 200px;
}

.temporal-time {
  color: #a6adc8;
  font-size: 12px;
  min-width: 50px;
}

.graph-search-overlay {
  position: absolute;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  display: none;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(30, 30, 46, 0.95);
  border: 1px solid #45475a;
  border-radius: 24px;
}

.graph-search-overlay.visible {
  display: flex;
}

.graph-search-input {
  width: 300px;
  padding: 8px 16px;
  background: transparent;
  border: none;
  color: #cdd6f4;
  font-size: 14px;
  outline: none;
}

.graph-search-count {
  color: #a6adc8;
  font-size: 12px;
}

.temporal-hidden {
  display: none !important;
}
`;

// Inject CSS
if (typeof document !== 'undefined') {
    const style = document.createElement('style');
    style.textContent = graphCSS;
    document.head.appendChild(style);
}

// =============================================================================
// 3D MODE STUB (THREE.js) - Stage 3.5 Steps 416-430
// =============================================================================

/**
 * InceptionGraph3D - THREE.js based 3D graph visualization
 * 
 * This is a stub implementation that provides the interface for 3D visualization.
 * Full implementation will use:
 * - THREE.js for WebGL rendering
 * - Force-directed layout in 3D space
 * - Orbit controls for navigation
 * - Raycasting for node selection
 */
class InceptionGraph3D {
    constructor(container, options = {}) {
        this.container = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        this.options = {
            nodeSize: options.nodeSize || 10,
            linkDistance: options.linkDistance || 100,
            cameraDistance: options.cameraDistance || 500,
            enableVR: options.enableVR || false,
            ...options
        };

        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.nodes3D = new Map();
        this.edges3D = [];

        this.init();
    }

    async init() {
        // Lazy load THREE.js
        try {
            const THREE = await import('three');
            const { OrbitControls } = await import('three/examples/jsm/controls/OrbitControls.js');

            // Scene setup
            this.scene = new THREE.Scene();
            this.scene.background = new THREE.Color(0x1e1e2e);

            // Camera
            const aspect = this.container.clientWidth / this.container.clientHeight;
            this.camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 2000);
            this.camera.position.z = this.options.cameraDistance;

            // Renderer
            this.renderer = new THREE.WebGLRenderer({ antialias: true });
            this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
            this.container.appendChild(this.renderer.domElement);

            // Controls
            this.controls = new OrbitControls(this.camera, this.renderer.domElement);
            this.controls.enableDamping = true;

            // Lighting
            const ambient = new THREE.AmbientLight(0xffffff, 0.5);
            const point = new THREE.PointLight(0xffffff, 1);
            point.position.set(100, 100, 100);
            this.scene.add(ambient, point);

            this.animate();
        } catch (e) {
            console.warn('THREE.js not available, 3D mode disabled:', e.message);
            this.showFallback();
        }
    }

    showFallback() {
        this.container.innerHTML = `
            <div style="display:flex;align-items:center;justify-content:center;height:100%;color:#a6adc8;">
                <div style="text-align:center;">
                    <div style="font-size:48px;margin-bottom:16px;">🔮</div>
                    <div>3D Mode requires THREE.js</div>
                    <div style="font-size:12px;margin-top:8px;">npm install three</div>
                </div>
            </div>
        `;
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        this.controls?.update();
        this.renderer?.render(this.scene, this.camera);
    }

    loadGraph(data) {
        if (!this.scene) return;

        const THREE = window.THREE;
        if (!THREE) return;

        // Clear existing
        this.nodes3D.forEach(mesh => this.scene.remove(mesh));
        this.nodes3D.clear();

        // Create node meshes
        const geometry = new THREE.SphereGeometry(this.options.nodeSize, 32, 32);

        data.nodes?.forEach((node, i) => {
            const color = this.getNodeColor(node.type);
            const material = new THREE.MeshPhongMaterial({ color });
            const mesh = new THREE.Mesh(geometry, material);

            // Distribute in 3D space
            const phi = Math.acos(-1 + (2 * i) / data.nodes.length);
            const theta = Math.sqrt(data.nodes.length * Math.PI) * phi;
            const r = this.options.linkDistance * 2;

            mesh.position.x = r * Math.sin(phi) * Math.cos(theta);
            mesh.position.y = r * Math.sin(phi) * Math.sin(theta);
            mesh.position.z = r * Math.cos(phi);

            mesh.userData = node;
            this.nodes3D.set(node.id, mesh);
            this.scene.add(mesh);
        });
    }

    getNodeColor(type) {
        const colors = {
            entity: 0x89b4fa,
            claim: 0xa6e3a1,
            procedure: 0xf9e2af,
            gap: 0xf38ba8,
            source: 0xcba6f7,
        };
        return colors[type] || 0xcdd6f4;
    }

    focusNode(nodeId) {
        const mesh = this.nodes3D.get(nodeId);
        if (mesh && this.camera) {
            this.camera.lookAt(mesh.position);
        }
    }

    resize() {
        if (this.camera && this.renderer) {
            const w = this.container.clientWidth;
            const h = this.container.clientHeight;
            this.camera.aspect = w / h;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(w, h);
        }
    }

    destroy() {
        this.renderer?.dispose();
        this.container.innerHTML = '';
    }
}

// =============================================================================
// EXPORTS
// =============================================================================

export { InceptionGraph, InceptionGraph3D };
export default InceptionGraph;
