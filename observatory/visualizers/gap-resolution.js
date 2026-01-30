// ════════════════════════════════════════════════════════════════════════════
// GAP RESOLUTION INTERFACE — Deep Purpose-Aligned Reimagining
// 
// COGNITIVE PURPOSE: Guide users to fill knowledge voids
// VISUAL METAPHOR: Gaps as gravitational singularities pulling knowledge inward
// ANTI-CORPORATE: No panels, no cards, no rounded corners — organic void geometry
// ════════════════════════════════════════════════════════════════════════════

import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { DataContracts } from '../lib/mock-data.js';

// ═══════════════════════════════════════════════════════════════════════════
// PURPOSE: This is not a pretty visualization. This is a COGNITIVE TOOL.
//
// When you see a gap:
//   - You should FEEL its pull on surrounding knowledge
//   - You should SEE what knowledge is being distorted by uncertainty
//   - You should UNDERSTAND what sources could resolve it
//   - You should be MOTIVATED to act (high severity = urgent warning)
//
// The visual language is:
//   - Voids: Dark attractors that bend space around them
//   - Knowledge: Particles being pulled, stretched, distorted
//   - Resolution: Suggested sources as beacons of light
//   - Urgency: Temporal pulse rate communicates priority
// ═══════════════════════════════════════════════════════════════════════════

export class GapResolutionInterface {
    constructor(container) {
        this.container = container;
        this.data = DataContracts.getGapConstellation();
        this.gaps = [];
        this.knowledgeParticles = [];
        this.resolutionBeacons = [];
        this.selectedGap = null;
        this.time = 0;
    }

    init() {
        this.setupScene();
        this.setupPostProcessing();
        this.createVoidField();
        this.createGaps();
        this.createKnowledgeField();
        this.createResolutionBeacons();
        this.setupInteraction();
        this.animate();
    }

    setupScene() {
        // Scene: The void of unknown
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x000000);

        // Camera: Observer of knowledge gaps
        this.camera = new THREE.PerspectiveCamera(
            75, this.container.clientWidth / this.container.clientHeight, 0.1, 1000
        );
        this.camera.position.set(0, 40, 80);

        // Renderer: No antialiasing - raw, unpolished truth
        this.renderer = new THREE.WebGLRenderer({
            antialias: false, // Intentionally harsh
            powerPreference: 'high-performance'
        });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.container.appendChild(this.renderer.domElement);

        // Controls: Free exploration
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.maxDistance = 200;
        this.controls.minDistance = 20;
    }

    setupPostProcessing() {
        this.composer = new EffectComposer(this.renderer);
        this.composer.addPass(new RenderPass(this.scene, this.camera));

        // Bloom: Gaps glow with warning, resolutions glow with hope
        this.bloomPass = new UnrealBloomPass(
            new THREE.Vector2(this.container.clientWidth, this.container.clientHeight),
            0.5,  // Low strength - we're not doing eye candy
            0.4,
            0.85
        );
        this.composer.addPass(this.bloomPass);
    }

    createVoidField() {
        // The fabric of knowledge space - a field that gaps will distort
        const geometry = new THREE.BufferGeometry();
        const gridSize = 100;
        const divisions = 40;
        const positions = [];
        const colors = [];

        for (let i = 0; i <= divisions; i++) {
            for (let j = 0; j <= divisions; j++) {
                const x = (i / divisions - 0.5) * gridSize;
                const z = (j / divisions - 0.5) * gridSize;
                positions.push(x, 0, z);

                // Subtle grid coloring
                const distFromCenter = Math.sqrt(x * x + z * z) / (gridSize * 0.5);
                colors.push(0.1, 0.15 - distFromCenter * 0.05, 0.2);
            }
        }

        geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

        const material = new THREE.PointsMaterial({
            size: 0.8,
            vertexColors: true,
            transparent: true,
            opacity: 0.4
        });

        this.voidField = new THREE.Points(geometry, material);
        this.voidFieldPositions = positions.slice(); // Store original positions
        this.scene.add(this.voidField);
    }

    createGaps() {
        // Gaps as gravitational singularities
        this.data.gaps.forEach((gap, i) => {
            const gapObject = {
                data: gap,
                position: new THREE.Vector3(
                    (Math.random() - 0.5) * 60,
                    5 + Math.random() * 10,
                    (Math.random() - 0.5) * 60
                ),
                radius: 3 + gap.severity * 5,
                pullStrength: gap.severity * 2,
                pulseRate: gap.priority === 'high' ? 4 :
                    gap.priority === 'medium' ? 2 : 1,
                mesh: null,
                eventHorizon: null
            };

            // Core singularity - not a sphere, an inward-pulling form
            const coreGeometry = new THREE.IcosahedronGeometry(gapObject.radius, 2);
            const coreMaterial = new THREE.ShaderMaterial({
                uniforms: {
                    time: { value: 0 },
                    severity: { value: gap.severity },
                    pulseRate: { value: gapObject.pulseRate },
                    selected: { value: 0 }
                },
                vertexShader: `
                    uniform float time;
                    uniform float severity;
                    uniform float pulseRate;
                    varying vec3 vNormal;
                    varying float vDistortion;
                    
                    void main() {
                        vNormal = normal;
                        
                        // Inward breathing - gaps inhale knowledge
                        float breathe = sin(time * pulseRate) * 0.2 * severity;
                        vec3 pos = position * (1.0 - breathe);
                        
                        // Distortion based on normal - creates uneven, organic surface
                        float distort = sin(position.x * 3.0 + time) * 
                                       cos(position.y * 3.0 + time * 0.7) * 
                                       sin(position.z * 3.0 + time * 0.5) * 0.1 * severity;
                        pos += normal * distort;
                        vDistortion = distort;
                        
                        gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
                    }
                `,
                fragmentShader: `
                    uniform float severity;
                    uniform float time;
                    uniform float selected;
                    varying vec3 vNormal;
                    varying float vDistortion;
                    
                    void main() {
                        // Edge glow - gaps are defined by their boundary, not their center
                        float edge = 1.0 - abs(dot(vNormal, vec3(0.0, 0.0, 1.0)));
                        
                        // Color by severity: low=blue, medium=purple, high=crimson
                        vec3 lowColor = vec3(0.1, 0.2, 0.4);
                        vec3 highColor = vec3(0.6, 0.1, 0.2);
                        vec3 baseColor = mix(lowColor, highColor, severity);
                        
                        // Pulse with warning
                        float pulse = (sin(time * 3.0) * 0.5 + 0.5) * severity;
                        baseColor += pulse * 0.2;
                        
                        // Selection highlight
                        baseColor += selected * vec3(0.2, 0.4, 0.3);
                        
                        // Edge emphasis
                        float alpha = edge * 0.8 + 0.2;
                        
                        gl_FragColor = vec4(baseColor * (edge + 0.3), alpha);
                    }
                `,
                transparent: true,
                side: THREE.DoubleSide
            });

            gapObject.mesh = new THREE.Mesh(coreGeometry, coreMaterial);
            gapObject.mesh.position.copy(gapObject.position);
            gapObject.mesh.userData = { gap: gap, gapObject: gapObject };
            this.scene.add(gapObject.mesh);

            // Event horizon ring - the boundary of distortion
            const horizonGeometry = new THREE.TorusGeometry(
                gapObject.radius * 2.5,
                0.1 + gap.severity * 0.2,
                16, 64
            );
            const horizonMaterial = new THREE.MeshBasicMaterial({
                color: gap.priority === 'high' ? 0xff2222 :
                    gap.priority === 'medium' ? 0xffaa22 : 0x4488ff,
                transparent: true,
                opacity: 0.3 + gap.severity * 0.3,
                wireframe: true
            });

            gapObject.eventHorizon = new THREE.Mesh(horizonGeometry, horizonMaterial);
            gapObject.eventHorizon.position.copy(gapObject.position);
            gapObject.eventHorizon.rotation.x = Math.PI / 2;
            this.scene.add(gapObject.eventHorizon);

            // Gap label - text describing what's missing
            // (In production, use CSS2DRenderer or custom text mesh)

            this.gaps.push(gapObject);
        });
    }

    createKnowledgeField() {
        // Knowledge particles - entities and claims affected by gaps
        const relatedNodes = this.data.relatedNodes.filter(Boolean);
        const particleCount = 500;

        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);
        const velocities = new Float32Array(particleCount * 3);
        const colors = new Float32Array(particleCount * 3);
        const sizes = new Float32Array(particleCount);

        for (let i = 0; i < particleCount; i++) {
            // Initial positions spread across the space
            positions[i * 3] = (Math.random() - 0.5) * 120;
            positions[i * 3 + 1] = Math.random() * 30;
            positions[i * 3 + 2] = (Math.random() - 0.5) * 120;

            velocities[i * 3] = 0;
            velocities[i * 3 + 1] = 0;
            velocities[i * 3 + 2] = 0;

            // Knowledge confidence as brightness
            const node = relatedNodes[i % relatedNodes.length];
            const conf = node?.confidence || 0.5;
            colors[i * 3] = 0.3 + conf * 0.5;     // R - low confidence = dimmer
            colors[i * 3 + 1] = 0.6 + conf * 0.4; // G - cyan-ish for knowledge
            colors[i * 3 + 2] = 0.7 + conf * 0.3; // B

            sizes[i] = 1 + Math.random() * 2;
        }

        geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
        geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
        geometry.setAttribute('size', new THREE.Float32BufferAttribute(sizes, 1));

        const material = new THREE.PointsMaterial({
            size: 1.5,
            vertexColors: true,
            transparent: true,
            opacity: 0.8,
            blending: THREE.AdditiveBlending
        });

        this.knowledgeField = new THREE.Points(geometry, material);
        this.knowledgeField.userData = { velocities };
        this.scene.add(this.knowledgeField);
    }

    createResolutionBeacons() {
        // Resolution beacons - suggested sources that could fill gaps
        this.gaps.forEach(gapObj => {
            const gap = gapObj.data;
            if (!gap.potentialSources?.length) return;

            gap.potentialSources.forEach((source, i) => {
                const angle = (i / gap.potentialSources.length) * Math.PI * 2;
                const distance = gapObj.radius * 4;

                const beacon = {
                    source: source,
                    gap: gapObj,
                    position: new THREE.Vector3(
                        gapObj.position.x + Math.cos(angle) * distance,
                        gapObj.position.y + 15,
                        gapObj.position.z + Math.sin(angle) * distance
                    ),
                    mesh: null
                };

                // Beacon geometry - upward pointing, hopeful
                const beaconGeom = new THREE.ConeGeometry(1.5, 6, 6);
                const beaconMat = new THREE.MeshBasicMaterial({
                    color: 0x44ff88,
                    transparent: true,
                    opacity: 0.7,
                    wireframe: true
                });

                beacon.mesh = new THREE.Mesh(beaconGeom, beaconMat);
                beacon.mesh.position.copy(beacon.position);
                beacon.mesh.userData = { beacon };
                this.scene.add(beacon.mesh);

                // Connection line to gap (potential resolution path)
                const lineGeom = new THREE.BufferGeometry().setFromPoints([
                    beacon.position,
                    gapObj.position
                ]);
                const lineMat = new THREE.LineDashedMaterial({
                    color: 0x44ff88,
                    dashSize: 2,
                    gapSize: 2,
                    transparent: true,
                    opacity: 0.3
                });
                const line = new THREE.Line(lineGeom, lineMat);
                line.computeLineDistances();
                this.scene.add(line);

                this.resolutionBeacons.push(beacon);
            });
        });
    }

    setupInteraction() {
        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();

        this.renderer.domElement.addEventListener('click', (event) => {
            const rect = this.renderer.domElement.getBoundingClientRect();
            mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
            mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

            raycaster.setFromCamera(mouse, this.camera);

            const gapMeshes = this.gaps.map(g => g.mesh);
            const intersects = raycaster.intersectObjects(gapMeshes);

            if (intersects.length > 0) {
                const gapObj = intersects[0].object.userData.gapObject;
                this.selectGap(gapObj);
            } else {
                this.deselectGap();
            }
        });
    }

    selectGap(gapObj) {
        // Deselect previous
        if (this.selectedGap) {
            this.selectedGap.mesh.material.uniforms.selected.value = 0;
        }

        this.selectedGap = gapObj;
        gapObj.mesh.material.uniforms.selected.value = 1;

        // Increase bloom to emphasize
        this.bloomPass.strength = 1.0;

        // Focus camera
        this.controls.target.copy(gapObj.position);

        console.log('[GapResolution] Selected gap:', gapObj.data.description);
        console.log('[GapResolution] Severity:', gapObj.data.severity);
        console.log('[GapResolution] Priority:', gapObj.data.priority);
        console.log('[GapResolution] Potential sources:', gapObj.data.potentialSources);
    }

    deselectGap() {
        if (this.selectedGap) {
            this.selectedGap.mesh.material.uniforms.selected.value = 0;
            this.selectedGap = null;
        }
        this.bloomPass.strength = 0.5;
    }

    updateGravitationalEffects() {
        // CORE COGNITIVE MECHANIC:
        // Gaps pull knowledge toward them, distorting the field

        const positions = this.knowledgeField.geometry.attributes.position;
        const velocities = this.knowledgeField.userData.velocities;
        const voidPositions = this.voidField.geometry.attributes.position;

        for (let i = 0; i < positions.count; i++) {
            const px = positions.getX(i);
            const py = positions.getY(i);
            const pz = positions.getZ(i);

            let ax = 0, ay = 0, az = 0;

            // Each gap exerts gravitational pull
            this.gaps.forEach(gap => {
                const dx = gap.position.x - px;
                const dy = gap.position.y - py;
                const dz = gap.position.z - pz;
                const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);

                if (dist > gap.radius && dist < gap.radius * 10) {
                    const force = gap.pullStrength / (dist * dist) * 0.5;
                    ax += (dx / dist) * force;
                    ay += (dy / dist) * force;
                    az += (dz / dist) * force;
                }

                // Particles too close get "consumed" - respawn elsewhere
                if (dist < gap.radius * 0.8) {
                    positions.setX(i, (Math.random() - 0.5) * 120);
                    positions.setY(i, Math.random() * 30);
                    positions.setZ(i, (Math.random() - 0.5) * 120);
                    velocities[i * 3] = 0;
                    velocities[i * 3 + 1] = 0;
                    velocities[i * 3 + 2] = 0;
                }
            });

            // Apply acceleration with damping
            velocities[i * 3] = (velocities[i * 3] + ax) * 0.98;
            velocities[i * 3 + 1] = (velocities[i * 3 + 1] + ay) * 0.98;
            velocities[i * 3 + 2] = (velocities[i * 3 + 2] + az) * 0.98;

            // Update position
            positions.setX(i, px + velocities[i * 3]);
            positions.setY(i, py + velocities[i * 3 + 1]);
            positions.setZ(i, pz + velocities[i * 3 + 2]);
        }

        positions.needsUpdate = true;

        // Also distort the void field grid
        for (let i = 0; i < voidPositions.count; i++) {
            const origX = this.voidFieldPositions[i * 3];
            const origZ = this.voidFieldPositions[i * 3 + 2];

            let totalPull = 0;
            let pullY = 0;

            this.gaps.forEach(gap => {
                const dx = gap.position.x - origX;
                const dz = gap.position.z - origZ;
                const dist = Math.sqrt(dx * dx + dz * dz);

                if (dist < gap.radius * 8) {
                    const pull = gap.pullStrength * Math.exp(-dist / (gap.radius * 3));
                    pullY -= pull * 2; // Gaps depress the field
                }
            });

            voidPositions.setY(i, pullY);
        }

        voidPositions.needsUpdate = true;
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        this.time = Date.now() * 0.001;

        // Update gap shaders
        this.gaps.forEach(gap => {
            gap.mesh.material.uniforms.time.value = this.time;
            gap.eventHorizon.rotation.z = this.time * 0.3;
        });

        // Resolution beacons pulse with hope
        this.resolutionBeacons.forEach((beacon, i) => {
            beacon.mesh.position.y = beacon.position.y + Math.sin(this.time * 2 + i) * 0.5;
            beacon.mesh.rotation.y = this.time;
        });

        // The core purpose: gravitational knowledge distortion
        this.updateGravitationalEffects();

        this.controls.update();
        this.composer.render();
    }

    dispose() {
        this.renderer?.dispose();
        this.composer?.dispose();
    }
}

export default GapResolutionInterface;
