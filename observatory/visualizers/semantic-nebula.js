// ════════════════════════════════════════════════════════════════════════════
// VISUALIZER 6: SEMANTIC NEBULA  
// Force-directed graph with semantic embedding-based positioning
// ════════════════════════════════════════════════════════════════════════════

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { DataContracts } from '../lib/mock-data.js';

export class SemanticNebulaVisualizer {
    constructor(container) {
        this.container = container;
        this.data = DataContracts.getSemanticNebula();
        this.nodeMeshes = new Map();
        this.linkLines = [];
        this.clusterClouds = [];
    }

    init() {
        // Scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x030308);
        this.scene.fog = new THREE.FogExp2(0x030308, 0.008);

        // Camera
        this.camera = new THREE.PerspectiveCamera(
            75, this.container.clientWidth / this.container.clientHeight, 0.1, 500
        );
        this.camera.position.set(0, 30, 80);

        // Renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.container.appendChild(this.renderer.domElement);

        // Controls
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.autoRotate = true;
        this.controls.autoRotateSpeed = 0.5;

        // Post-processing
        this.composer = new EffectComposer(this.renderer);
        this.composer.addPass(new RenderPass(this.scene, this.camera));
        this.composer.addPass(new UnrealBloomPass(
            new THREE.Vector2(this.container.clientWidth, this.container.clientHeight),
            1.0, 0.6, 0.7
        ));

        this.createClusters();
        this.createNodes();
        this.createLinks();
        this.createParticleField();

        this.animate();
    }

    embeddingToPosition(embedding, scale = 40) {
        // Map 5D embedding to 3D position using first 3 dimensions
        // with 4th and 5th affecting Y offset
        return new THREE.Vector3(
            (embedding[0] - 0.5) * scale * 2,
            (embedding[3] - 0.5) * scale + (embedding[4] - 0.5) * scale * 0.5,
            (embedding[1] - 0.5) * scale * 2
        );
    }

    createClusters() {
        const clusterColors = {
            'cluster_auth': 0x64ffda,
            'cluster_storage': 0xffd93d,
            'cluster_kg': 0xbd93f9,
        };

        this.data.clusters.forEach(cluster => {
            const pos = this.embeddingToPosition(cluster.centroid, 50);

            // Nebula cloud effect using particle system
            const particleCount = 500;
            const positions = new Float32Array(particleCount * 3);
            const colors = new Float32Array(particleCount * 3);
            const sizes = new Float32Array(particleCount);

            const color = new THREE.Color(clusterColors[cluster.id] || 0x8892b0);

            for (let i = 0; i < particleCount; i++) {
                // Gaussian distribution around centroid
                const r = Math.random() * 15;
                const theta = Math.random() * Math.PI * 2;
                const phi = Math.random() * Math.PI;

                positions[i * 3] = pos.x + r * Math.sin(phi) * Math.cos(theta);
                positions[i * 3 + 1] = pos.y + r * Math.sin(phi) * Math.sin(theta) * 0.5;
                positions[i * 3 + 2] = pos.z + r * Math.cos(phi);

                colors[i * 3] = color.r;
                colors[i * 3 + 1] = color.g;
                colors[i * 3 + 2] = color.b;

                sizes[i] = 0.5 + Math.random() * 1.5;
            }

            const geom = new THREE.BufferGeometry();
            geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            geom.setAttribute('color', new THREE.BufferAttribute(colors, 3));
            geom.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

            const mat = new THREE.PointsMaterial({
                size: 1,
                vertexColors: true,
                transparent: true,
                opacity: 0.3,
                blending: THREE.AdditiveBlending
            });

            const cloud = new THREE.Points(geom, mat);
            cloud.userData = { cluster, basePositions: positions.slice() };
            this.scene.add(cloud);
            this.clusterClouds.push(cloud);

            // Cluster label
            // (In a real implementation, would use CSS2DRenderer or sprite)
        });
    }

    createNodes() {
        const groupColors = {
            'cluster_auth': 0x64ffda,
            'cluster_storage': 0xffd93d,
            'cluster_kg': 0xbd93f9,
            'unclustered': 0x8892b0
        };

        this.data.nodes.forEach(node => {
            const pos = this.embeddingToPosition(node.embedding);
            const size = Math.sqrt(node.size) * 0.3;

            const geom = new THREE.SphereGeometry(size, 16, 16);
            const mat = new THREE.MeshPhysicalMaterial({
                color: groupColors[node.group] || 0x8892b0,
                emissive: groupColors[node.group] || 0x8892b0,
                emissiveIntensity: 0.5,
                metalness: 0.3,
                roughness: 0.5,
                transparent: true,
                opacity: 0.9
            });

            const mesh = new THREE.Mesh(geom, mat);
            mesh.position.copy(pos);
            mesh.userData = { node, originalPosition: pos.clone() };

            this.scene.add(mesh);
            this.nodeMeshes.set(node.id, mesh);
        });

        // Lighting
        const ambient = new THREE.AmbientLight(0xffffff, 0.3);
        this.scene.add(ambient);

        const light = new THREE.PointLight(0xffffff, 1, 200);
        light.position.set(0, 50, 0);
        this.scene.add(light);
    }

    createLinks() {
        const linkColors = {
            'supports': 0x64ffda,
            'contradicts': 0xff6b9d,
            'contains': 0xbd93f9,
            'provenance': 0xffd93d
        };

        this.data.links.forEach(link => {
            const sourceNode = this.nodeMeshes.get(link.source);
            const targetNode = this.nodeMeshes.get(link.target);

            if (!sourceNode || !targetNode) return;

            const points = [sourceNode.position, targetNode.position];
            const geom = new THREE.BufferGeometry().setFromPoints(points);
            const mat = new THREE.LineBasicMaterial({
                color: linkColors[link.type] || 0x8892b0,
                transparent: true,
                opacity: link.strength * 0.5
            });

            const line = new THREE.Line(geom, mat);
            line.userData = { link, sourceNode, targetNode };
            this.scene.add(line);
            this.linkLines.push(line);
        });
    }

    createParticleField() {
        // Background stars
        const starCount = 3000;
        const positions = new Float32Array(starCount * 3);

        for (let i = 0; i < starCount; i++) {
            positions[i * 3] = (Math.random() - 0.5) * 400;
            positions[i * 3 + 1] = (Math.random() - 0.5) * 400;
            positions[i * 3 + 2] = (Math.random() - 0.5) * 400;
        }

        const geom = new THREE.BufferGeometry();
        geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));

        const mat = new THREE.PointsMaterial({
            size: 0.3,
            color: 0x8892b0,
            transparent: true,
            opacity: 0.4
        });

        this.scene.add(new THREE.Points(geom, mat));
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        const time = Date.now() * 0.001;

        // Animate cluster clouds
        this.clusterClouds.forEach((cloud, ci) => {
            const positions = cloud.geometry.attributes.position;
            const base = cloud.userData.basePositions;

            for (let i = 0; i < positions.count; i++) {
                positions.setX(i, base[i * 3] + Math.sin(time + i * 0.1) * 0.5);
                positions.setY(i, base[i * 3 + 1] + Math.cos(time * 0.8 + i * 0.1) * 0.3);
                positions.setZ(i, base[i * 3 + 2] + Math.sin(time * 0.6 + i * 0.1) * 0.5);
            }
            positions.needsUpdate = true;
        });

        // Subtle node breathing
        this.nodeMeshes.forEach((mesh, id) => {
            const scale = 1 + Math.sin(time * 2 + mesh.position.x) * 0.05;
            mesh.scale.setScalar(scale);
        });

        // Update link positions
        this.linkLines.forEach(line => {
            const positions = line.geometry.attributes.position;
            positions.setXYZ(0,
                line.userData.sourceNode.position.x,
                line.userData.sourceNode.position.y,
                line.userData.sourceNode.position.z
            );
            positions.setXYZ(1,
                line.userData.targetNode.position.x,
                line.userData.targetNode.position.y,
                line.userData.targetNode.position.z
            );
            positions.needsUpdate = true;
        });

        this.controls.update();
        this.composer.render();
    }

    dispose() {
        this.renderer?.dispose();
        this.composer?.dispose();
    }
}

export default SemanticNebulaVisualizer;
