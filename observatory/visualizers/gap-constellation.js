// ════════════════════════════════════════════════════════════════════════════
// VISUALIZER 4: GAP CONSTELLATION
// Void clusters representing missing knowledge - dark attractors in space
// ════════════════════════════════════════════════════════════════════════════

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { DataContracts } from '../lib/mock-data.js';

export class GapConstellationVisualizer {
    constructor(container) {
        this.container = container;
        this.data = DataContracts.getGapConstellation();
        this.gapMeshes = [];
    }

    init() {
        // Scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x020204);

        // Camera
        this.camera = new THREE.PerspectiveCamera(
            70, this.container.clientWidth / this.container.clientHeight, 0.1, 500
        );
        this.camera.position.set(0, 20, 60);

        // Renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.container.appendChild(this.renderer.domElement);

        // Controls
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;

        // Post-processing
        this.composer = new EffectComposer(this.renderer);
        this.composer.addPass(new RenderPass(this.scene, this.camera));
        this.composer.addPass(new UnrealBloomPass(
            new THREE.Vector2(this.container.clientWidth, this.container.clientHeight),
            0.8, 0.5, 0.7
        ));

        this.createGaps();
        this.createRelatedNodes();
        this.createVoidField();

        this.animate();
    }

    createGaps() {
        const gapPositions = [
            new THREE.Vector3(-20, 0, 0),
            new THREE.Vector3(15, 10, -10),
            new THREE.Vector3(5, -15, 15),
            new THREE.Vector3(-10, 20, -20),
        ];

        this.data.gaps.forEach((gap, i) => {
            const pos = gapPositions[i] || new THREE.Vector3(
                (Math.random() - 0.5) * 40,
                (Math.random() - 0.5) * 40,
                (Math.random() - 0.5) * 40
            );

            // Black hole effect - inverted sphere with distortion
            const size = 3 + gap.severity * 4;

            // Core void (absorbs light)
            const coreGeom = new THREE.SphereGeometry(size, 32, 32);
            const coreMat = new THREE.ShaderMaterial({
                uniforms: {
                    time: { value: 0 },
                    severity: { value: gap.severity }
                },
                vertexShader: `
                    uniform float time;
                    varying vec3 vNormal;
                    void main() {
                        vNormal = normal;
                        vec3 pos = position;
                        pos += normal * sin(time * 2.0 + position.x * 3.0) * 0.1;
                        gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
                    }
                `,
                fragmentShader: `
                    uniform float severity;
                    varying vec3 vNormal;
                    void main() {
                        float edge = 1.0 - dot(vNormal, vec3(0.0, 0.0, 1.0));
                        vec3 color = mix(vec3(0.0), vec3(1.0, 0.42, 0.62), edge * severity);
                        gl_FragColor = vec4(color, 1.0);
                    }
                `
            });

            const core = new THREE.Mesh(coreGeom, coreMat);
            core.position.copy(pos);
            core.userData = { gap, timeUniform: coreMat.uniforms.time };
            this.scene.add(core);
            this.gapMeshes.push(core);

            // Accretion disk
            const diskGeom = new THREE.RingGeometry(size * 1.2, size * 2, 64);
            const diskMat = new THREE.MeshBasicMaterial({
                color: 0xff6b9d,
                transparent: true,
                opacity: 0.3 + gap.severity * 0.4,
                side: THREE.DoubleSide
            });
            const disk = new THREE.Mesh(diskGeom, diskMat);
            disk.position.copy(pos);
            disk.rotation.x = Math.PI / 2 + Math.random() * 0.3;
            this.scene.add(disk);

            // Event horizon glow
            const glowGeom = new THREE.SphereGeometry(size * 1.1, 32, 32);
            const glowMat = new THREE.MeshBasicMaterial({
                color: 0xff6b9d,
                transparent: true,
                opacity: 0.2,
                wireframe: true
            });
            const glow = new THREE.Mesh(glowGeom, glowMat);
            glow.position.copy(pos);
            this.scene.add(glow);

            // Priority indicator (concentric rings)
            const priorityColors = { high: 0xff0000, medium: 0xffd93d, low: 0x64ffda };
            const ringGeom = new THREE.TorusGeometry(size * 2.5, 0.1, 8, 64);
            const ringMat = new THREE.MeshBasicMaterial({
                color: priorityColors[gap.priority] || priorityColors.medium
            });
            const ring = new THREE.Mesh(ringGeom, ringMat);
            ring.position.copy(pos);
            ring.rotation.x = Math.PI / 2;
            this.scene.add(ring);
        });
    }

    createRelatedNodes() {
        // Add related entities/claims as particles being pulled toward gaps
        this.data.relatedNodes.forEach((node, i) => {
            if (!node) return;

            const geom = new THREE.SphereGeometry(0.5, 16, 16);
            const mat = new THREE.MeshBasicMaterial({
                color: node.confidence > 0.8 ? 0x64ffda : 0xbd93f9,
                transparent: true,
                opacity: node.confidence || 0.7
            });
            const mesh = new THREE.Mesh(geom, mat);

            // Position near a gap
            const gapIndex = i % this.gapMeshes.length;
            const gapPos = this.gapMeshes[gapIndex]?.position || new THREE.Vector3();
            const offset = new THREE.Vector3(
                (Math.random() - 0.5) * 20,
                (Math.random() - 0.5) * 20,
                (Math.random() - 0.5) * 20
            );
            mesh.position.copy(gapPos).add(offset);

            this.scene.add(mesh);
        });
    }

    createVoidField() {
        // Particle field showing the fabric of knowledge being distorted
        const particleCount = 2000;
        const positions = new Float32Array(particleCount * 3);
        const colors = new Float32Array(particleCount * 3);

        for (let i = 0; i < particleCount; i++) {
            positions[i * 3] = (Math.random() - 0.5) * 100;
            positions[i * 3 + 1] = (Math.random() - 0.5) * 100;
            positions[i * 3 + 2] = (Math.random() - 0.5) * 100;

            colors[i * 3] = 0.4;
            colors[i * 3 + 1] = 0.5;
            colors[i * 3 + 2] = 0.7;
        }

        const geom = new THREE.BufferGeometry();
        geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        geom.setAttribute('color', new THREE.BufferAttribute(colors, 3));

        const mat = new THREE.PointsMaterial({
            size: 0.2,
            vertexColors: true,
            transparent: true,
            opacity: 0.5
        });

        this.particles = new THREE.Points(geom, mat);
        this.scene.add(this.particles);
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        const time = Date.now() * 0.001;

        // Update gap shaders
        this.gapMeshes.forEach(mesh => {
            if (mesh.userData.timeUniform) {
                mesh.userData.timeUniform.value = time;
            }
            mesh.rotation.y = time * 0.2;
        });

        // Warp particles toward gaps (simplified)
        if (this.particles) {
            this.particles.rotation.y = time * 0.02;
        }

        this.controls.update();
        this.composer.render();
    }

    dispose() {
        this.renderer?.dispose();
        this.composer?.dispose();
    }
}

export default GapConstellationVisualizer;
