/**
 * Three.js 3D Provider Visualization - Agent Auth
 * 
 * Creates an orbital 3D visualization of AI providers:
 * - Provider nodes as glowing spheres
 * - Animated connection lines with particles
 * - Real-time status visualization (color/intensity)
 * - Smooth orbit animation
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer, RenderPass, UnrealBloomPass } from 'three/addons/postprocessing/EffectComposer.js';

// Provider configuration matching provider_config.py
const PROVIDERS = {
    claude: {
        color: 0x8B5CF6, // Purple
        name: 'Claude',
        model: 'Opus 4.5',
        position: { x: 2, y: 0, z: 0 }
    },
    gemini: {
        color: 0x4285F4, // Blue
        name: 'Gemini',
        model: '2.5 Flash',
        position: { x: -2, y: 0, z: 0 }
    },
    codex: {
        color: 0x10B981, // Green
        name: 'Codex',
        model: 'gpt-5.2-codex',
        position: { x: 0, y: 2, z: 0 }
    },
    kimi: {
        color: 0xF59E0B, // Orange
        name: 'Kimi',
        model: 'API Key',
        position: { x: 0, y: -2, z: 0 }
    }
};

class AgentAuthThreeJS {
    constructor(container, options = {}) {
        this.container = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        this.options = {
            width: 600,
            height: 400,
            enableBloom: true,
            autoRotate: true,
            ...options
        };

        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.composer = null;
        this.nodes = {};
        this.connections = [];
        this.centerNode = null;
        this.clock = new THREE.Clock();

        this.init();
    }

    init() {
        // Scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0a0a0f);

        // Camera
        this.camera = new THREE.PerspectiveCamera(
            60,
            this.options.width / this.options.height,
            0.1,
            1000
        );
        this.camera.position.set(0, 0, 8);

        // Renderer
        this.renderer = new THREE.WebGLRenderer({
            antialias: true,
            alpha: true
        });
        this.renderer.setSize(this.options.width, this.options.height);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.container.appendChild(this.renderer.domElement);

        // Controls
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.autoRotate = this.options.autoRotate;
        this.controls.autoRotateSpeed = 0.5;

        // Bloom post-processing
        if (this.options.enableBloom) {
            this.setupBloom();
        }

        // Create center node (Inception logo)
        this.createCenterNode();

        // Create provider nodes
        Object.entries(PROVIDERS).forEach(([key, config]) => {
            this.createProviderNode(key, config);
        });

        // Create connections
        this.createConnections();

        // Start animation
        this.animate();
    }

    setupBloom() {
        const renderScene = new RenderPass(this.scene, this.camera);
        const bloomPass = new UnrealBloomPass(
            new THREE.Vector2(this.options.width, this.options.height),
            1.5,  // strength
            0.4,  // radius
            0.85  // threshold
        );
        bloomPass.threshold = 0;
        bloomPass.strength = 1.2;
        bloomPass.radius = 0.5;

        this.composer = new EffectComposer(this.renderer);
        this.composer.addPass(renderScene);
        this.composer.addPass(bloomPass);
    }

    createCenterNode() {
        // Central node representing Inception
        const geometry = new THREE.IcosahedronGeometry(0.5, 2);
        const material = new THREE.MeshStandardMaterial({
            color: 0xffffff,
            emissive: 0x444444,
            metalness: 0.8,
            roughness: 0.2
        });

        this.centerNode = new THREE.Mesh(geometry, material);
        this.scene.add(this.centerNode);

        // Add ambient and point lights
        const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
        this.scene.add(ambientLight);

        const pointLight = new THREE.PointLight(0xffffff, 1, 100);
        pointLight.position.set(5, 5, 5);
        this.scene.add(pointLight);
    }

    createProviderNode(key, config) {
        // Main sphere
        const geometry = new THREE.SphereGeometry(0.4, 32, 32);
        const material = new THREE.MeshStandardMaterial({
            color: config.color,
            emissive: config.color,
            emissiveIntensity: 0.3,
            metalness: 0.7,
            roughness: 0.3
        });

        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.set(config.position.x, config.position.y, config.position.z);
        mesh.userData = { provider: key, ...config };

        this.scene.add(mesh);
        this.nodes[key] = mesh;

        // Glow ring
        const ringGeometry = new THREE.RingGeometry(0.5, 0.6, 32);
        const ringMaterial = new THREE.MeshBasicMaterial({
            color: config.color,
            transparent: true,
            opacity: 0.5,
            side: THREE.DoubleSide
        });

        const ring = new THREE.Mesh(ringGeometry, ringMaterial);
        ring.position.copy(mesh.position);
        ring.lookAt(this.camera.position);
        mesh.add(ring);
    }

    createConnections() {
        Object.keys(PROVIDERS).forEach(key => {
            const node = this.nodes[key];
            const points = [
                new THREE.Vector3(0, 0, 0),
                node.position.clone()
            ];

            const geometry = new THREE.BufferGeometry().setFromPoints(points);
            const material = new THREE.LineBasicMaterial({
                color: PROVIDERS[key].color,
                transparent: true,
                opacity: 0.4
            });

            const line = new THREE.Line(geometry, material);
            this.scene.add(line);
            this.connections.push({ line, provider: key });
        });
    }

    /**
     * Update provider status
     * @param {string} provider - Provider key
     * @param {boolean} connected - Connection status
     */
    updateStatus(provider, connected) {
        const node = this.nodes[provider];
        if (!node) return;

        const intensity = connected ? 0.6 : 0.1;
        node.material.emissiveIntensity = intensity;

        // Pulse animation on connect
        if (connected) {
            const scale = { value: 1 };
            this.animatePulse(node);
        }
    }

    animatePulse(node) {
        const startScale = 1;
        const endScale = 1.3;
        const duration = 300;
        const start = performance.now();

        const pulse = () => {
            const elapsed = performance.now() - start;
            const progress = Math.min(elapsed / duration, 1);
            const scale = startScale + (endScale - startScale) * Math.sin(progress * Math.PI);

            node.scale.setScalar(scale);

            if (progress < 1) {
                requestAnimationFrame(pulse);
            } else {
                node.scale.setScalar(1);
            }
        };

        pulse();
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        const time = this.clock.getElapsedTime();

        // Rotate center node
        if (this.centerNode) {
            this.centerNode.rotation.x = time * 0.5;
            this.centerNode.rotation.y = time * 0.3;
        }

        // Float provider nodes
        Object.values(this.nodes).forEach((node, i) => {
            node.position.y += Math.sin(time * 2 + i) * 0.001;
        });

        // Update controls
        this.controls.update();

        // Render
        if (this.composer) {
            this.composer.render();
        } else {
            this.renderer.render(this.scene, this.camera);
        }
    }

    /**
     * Resize handler
     */
    resize(width, height) {
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);

        if (this.composer) {
            this.composer.setSize(width, height);
        }
    }

    /**
     * Cleanup
     */
    destroy() {
        this.renderer.dispose();
        this.container.removeChild(this.renderer.domElement);
    }
}

export { AgentAuthThreeJS };
export default AgentAuthThreeJS;
