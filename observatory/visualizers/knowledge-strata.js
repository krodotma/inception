// ════════════════════════════════════════════════════════════════════════════
// VISUALIZER 9: KNOWLEDGE STRATA
// Layered depth slices showing Sources → Claims → Entities → Gaps
// ════════════════════════════════════════════════════════════════════════════

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { DataContracts } from '../lib/mock-data.js';

export class KnowledgeStrataVisualizer {
    constructor(container) {
        this.container = container;
        this.data = DataContracts.getKnowledgeStrata();
        this.layerMeshes = [];
        this.nodeMeshes = [];
        this.crossEdges = [];
    }

    init() {
        // Scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x030306);

        // Camera
        this.camera = new THREE.PerspectiveCamera(
            60, this.container.clientWidth / this.container.clientHeight, 0.1, 500
        );
        this.camera.position.set(60, 80, 100);

        // Renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.container.appendChild(this.renderer.domElement);

        // Controls
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;

        this.createLayers();
        this.createNodes();
        this.createCrossLayerEdges();
        this.addLighting();

        this.animate();
    }

    createLayers() {
        const layerColors = [
            0xffd93d, // Sources - gold
            0x64ffda, // Claims - cyan
            0xbd93f9, // Entities - violet
            0xff6b9d, // Gaps - rose
        ];

        const layerHeight = 25;
        const planeSize = 80;

        this.data.layers.forEach((layer, i) => {
            const y = layer.depth * layerHeight;

            // Glass-like plane
            const geom = new THREE.PlaneGeometry(planeSize, planeSize);
            const mat = new THREE.MeshPhysicalMaterial({
                color: layerColors[i],
                transparent: true,
                opacity: 0.1,
                metalness: 0.1,
                roughness: 0.3,
                side: THREE.DoubleSide
            });

            const plane = new THREE.Mesh(geom, mat);
            plane.rotation.x = -Math.PI / 2;
            plane.position.y = y;
            this.scene.add(plane);

            // Grid lines
            const gridHelper = new THREE.GridHelper(planeSize, 10, layerColors[i], layerColors[i]);
            gridHelper.position.y = y + 0.1;
            gridHelper.material.opacity = 0.2;
            gridHelper.material.transparent = true;
            this.scene.add(gridHelper);

            // Layer label (would use TextGeometry or Sprite in production)
            // For now, store for later reference
            this.layerMeshes.push({ plane, layer, y, color: layerColors[i] });
        });
    }

    createNodes() {
        const nodeGeometries = {
            Sources: new THREE.TetrahedronGeometry(2),
            Claims: new THREE.SphereGeometry(1.5, 16, 16),
            Entities: new THREE.IcosahedronGeometry(2),
            Gaps: new THREE.TorusGeometry(1.5, 0.5, 8, 16),
        };

        const layerColors = [0xffd93d, 0x64ffda, 0xbd93f9, 0xff6b9d];

        this.data.layers.forEach((layer, li) => {
            const y = layer.depth * 25 + 2;
            const nodes = layer.nodes;
            const color = layerColors[li];
            const geomType = nodeGeometries[layer.name] || nodeGeometries.Claims;

            // Distribute nodes on the layer
            const gridSize = Math.ceil(Math.sqrt(nodes.length));
            const spacing = 60 / (gridSize + 1);

            nodes.forEach((node, ni) => {
                const row = Math.floor(ni / gridSize);
                const col = ni % gridSize;

                const x = -30 + (col + 1) * spacing + (Math.random() - 0.5) * 5;
                const z = -30 + (row + 1) * spacing + (Math.random() - 0.5) * 5;

                const mat = new THREE.MeshPhysicalMaterial({
                    color: color,
                    emissive: color,
                    emissiveIntensity: 0.3,
                    metalness: 0.4,
                    roughness: 0.3,
                    transparent: true,
                    opacity: (node.confidence || node.credibility || 0.8)
                });

                const mesh = new THREE.Mesh(geomType.clone(), mat);
                mesh.position.set(x, y, z);
                mesh.userData = { node, layer: layer.name };

                this.scene.add(mesh);
                this.nodeMeshes.push(mesh);
            });
        });
    }

    createCrossLayerEdges() {
        // Draw edges between layers (simplified - actual would use edge data)
        const edgeColors = {
            provenance: 0xffd93d,
            supports: 0x64ffda,
            questions: 0xff6b9d,
        };

        this.data.crossLayerEdges.forEach(edge => {
            const sourceNode = this.nodeMeshes.find(m => m.userData.node?.id === edge.source);
            const targetNode = this.nodeMeshes.find(m => m.userData.node?.id === edge.target);

            if (sourceNode && targetNode) {
                const points = [sourceNode.position, targetNode.position];
                const geom = new THREE.BufferGeometry().setFromPoints(points);
                const mat = new THREE.LineBasicMaterial({
                    color: edgeColors[edge.type] || 0x8892b0,
                    transparent: true,
                    opacity: edge.strength * 0.5
                });

                const line = new THREE.Line(geom, mat);
                this.scene.add(line);
                this.crossEdges.push({ line, source: sourceNode, target: targetNode });
            }
        });
    }

    addLighting() {
        const ambient = new THREE.AmbientLight(0xffffff, 0.4);
        this.scene.add(ambient);

        // Light per layer
        [0, 25, 50, 75].forEach((y, i) => {
            const light = new THREE.PointLight(0xffffff, 0.3, 100);
            light.position.set(0, y + 10, 0);
            this.scene.add(light);
        });
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        const time = Date.now() * 0.001;

        // Gentle floating motion
        this.nodeMeshes.forEach((mesh, i) => {
            mesh.position.y = mesh.userData.originalY || mesh.position.y;
            if (!mesh.userData.originalY) mesh.userData.originalY = mesh.position.y;
            mesh.position.y = mesh.userData.originalY + Math.sin(time + i * 0.2) * 0.5;
            mesh.rotation.y = time * 0.3;
        });

        // Update edge positions
        this.crossEdges.forEach(edge => {
            const positions = edge.line.geometry.attributes.position;
            positions.setXYZ(0, edge.source.position.x, edge.source.position.y, edge.source.position.z);
            positions.setXYZ(1, edge.target.position.x, edge.target.position.y, edge.target.position.z);
            positions.needsUpdate = true;
        });

        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }

    dispose() {
        this.renderer?.dispose();
    }
}

export default KnowledgeStrataVisualizer;
