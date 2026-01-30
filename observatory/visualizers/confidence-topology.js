// ════════════════════════════════════════════════════════════════════════════
// VISUALIZER 2: CONFIDENCE TOPOLOGY
// 3D terrain where height = confidence, valleys = uncertainty
// ════════════════════════════════════════════════════════════════════════════

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { DataContracts } from '../lib/mock-data.js';

export class ConfidenceTopologyVisualizer {
    constructor(container) {
        this.container = container;
        this.data = DataContracts.getConfidenceTopology();
    }

    init() {
        // Scene setup
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x050508);
        this.scene.fog = new THREE.FogExp2(0x050508, 0.015);

        // Camera
        this.camera = new THREE.PerspectiveCamera(
            60, this.container.clientWidth / this.container.clientHeight, 0.1, 1000
        );
        this.camera.position.set(50, 80, 100);

        // Renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.container.appendChild(this.renderer.domElement);

        // Controls
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;

        // Build terrain
        this.buildTerrain();
        this.addNodes();
        this.addLighting();

        this.animate();
    }

    buildTerrain() {
        // Create heightfield from node positions and confidences
        const width = 100;
        const depth = 100;
        const segments = 64;

        const geometry = new THREE.PlaneGeometry(width, depth, segments, segments);
        const positions = geometry.attributes.position;

        // Modify heights based on nearby nodes
        for (let i = 0; i < positions.count; i++) {
            const x = positions.getX(i);
            const z = positions.getY(i); // Y in plane = Z in 3D

            let height = 0;
            this.data.nodes.forEach(node => {
                const dx = (node.x - 50) - x;
                const dy = (node.y - 50) - z;
                const dist = Math.sqrt(dx * dx + dy * dy);

                // Gaussian influence
                const influence = node.z * Math.exp(-dist * dist / 200);
                height += influence;
            });

            positions.setZ(i, height);
        }

        geometry.computeVertexNormals();

        // Gradient material based on height
        const material = new THREE.ShaderMaterial({
            uniforms: {
                lowColor: { value: new THREE.Color(0x050508) },
                highColor: { value: new THREE.Color(0x64ffda) },
                maxHeight: { value: 50 }
            },
            vertexShader: `
                varying float vHeight;
                void main() {
                    vHeight = position.z;
                    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
                }
            `,
            fragmentShader: `
                uniform vec3 lowColor;
                uniform vec3 highColor;
                uniform float maxHeight;
                varying float vHeight;
                void main() {
                    float t = clamp(vHeight / maxHeight, 0.0, 1.0);
                    vec3 color = mix(lowColor, highColor, t);
                    gl_FragColor = vec4(color, 0.8);
                }
            `,
            transparent: true,
            side: THREE.DoubleSide
        });

        const terrain = new THREE.Mesh(geometry, material);
        terrain.rotation.x = -Math.PI / 2;
        this.scene.add(terrain);

        // Wireframe overlay
        const wireframe = new THREE.WireframeGeometry(geometry);
        const lines = new THREE.LineSegments(
            wireframe,
            new THREE.LineBasicMaterial({ color: 0x64ffda, opacity: 0.1, transparent: true })
        );
        lines.rotation.x = -Math.PI / 2;
        this.scene.add(lines);
    }

    addNodes() {
        const colors = {
            entity: 0xbd93f9,
            claim: 0x64ffda,
        };

        this.data.nodes.forEach(node => {
            const geometry = new THREE.SphereGeometry(1 + node.z / 20, 16, 16);
            const material = new THREE.MeshPhysicalMaterial({
                color: colors[node.type] || 0x64ffda,
                emissive: colors[node.type] || 0x64ffda,
                emissiveIntensity: 0.3,
                metalness: 0.3,
                roughness: 0.5,
                transparent: true,
                opacity: 0.9
            });

            const sphere = new THREE.Mesh(geometry, material);
            sphere.position.set(node.x - 50, node.z + 2, node.y - 50);
            this.scene.add(sphere);

            // Uncertainty ring (if high uncertainty)
            if (node.uncertainty) {
                const unc = node.uncertainty.epistemic || node.uncertainty.lower;
                if (unc > 0.1) {
                    const ringGeom = new THREE.RingGeometry(2, 2.5, 32);
                    const ringMat = new THREE.MeshBasicMaterial({
                        color: 0xff6b9d,
                        transparent: true,
                        opacity: unc,
                        side: THREE.DoubleSide
                    });
                    const ring = new THREE.Mesh(ringGeom, ringMat);
                    ring.rotation.x = -Math.PI / 2;
                    ring.position.copy(sphere.position);
                    ring.position.y += 0.1;
                    this.scene.add(ring);
                }
            }
        });
    }

    addLighting() {
        const ambient = new THREE.AmbientLight(0xffffff, 0.4);
        this.scene.add(ambient);

        const light1 = new THREE.DirectionalLight(0x64ffda, 0.8);
        light1.position.set(50, 100, 50);
        this.scene.add(light1);

        const light2 = new THREE.PointLight(0xbd93f9, 0.5, 200);
        light2.position.set(-30, 50, 30);
        this.scene.add(light2);
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }

    dispose() {
        this.renderer?.dispose();
    }
}

export default ConfidenceTopologyVisualizer;
