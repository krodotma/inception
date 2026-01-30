// ════════════════════════════════════════════════════════════════════════════
// ORGANIC MORPHING — Pure CSS + JS Animations
//
// COGNITIVE PURPOSE: Visualize knowledge state transitions
// TECH: CSS custom properties, clip-path morphing, blend modes
// ANTI-CORPORATE: No cards, no grids — liquid organic forms
// ════════════════════════════════════════════════════════════════════════════

import { DataContracts } from '../lib/mock-data.js';

export class OrganicMorphingVisualizer {
    constructor(container) {
        this.container = container;
        this.data = DataContracts.getTemporalData();
        this.shapes = [];
        this.time = 0;
    }

    init() {
        // Root container with CSS variables
        const root = document.createElement('div');
        root.id = 'organic-morph';
        root.innerHTML = `
            <style>
                #organic-morph {
                    position: absolute;
                    inset: 0;
                    background: linear-gradient(135deg, #000 0%, #050510 50%, #0a0515 100%);
                    overflow: hidden;
                    font-family: monospace;
                }
                
                /* Organic blobs representing knowledge clusters */
                .knowledge-blob {
                    position: absolute;
                    border-radius: 30% 70% 70% 30% / 30% 30% 70% 70%;
                    filter: blur(0.5px);
                    mix-blend-mode: screen;
                    animation: morph 8s ease-in-out infinite;
                    transition: transform 0.5s ease, opacity 0.3s ease;
                }
                
                .knowledge-blob:hover {
                    transform: scale(1.2);
                    filter: blur(0);
                }
                
                @keyframes morph {
                    0%, 100% {
                        border-radius: 30% 70% 70% 30% / 30% 30% 70% 70%;
                    }
                    25% {
                        border-radius: 58% 42% 75% 25% / 76% 46% 54% 24%;
                    }
                    50% {
                        border-radius: 50% 50% 33% 67% / 55% 27% 73% 45%;
                    }
                    75% {
                        border-radius: 33% 67% 58% 42% / 63% 68% 32% 37%;
                    }
                }
                
                /* Entity blobs */
                .blob-entity {
                    background: radial-gradient(
                        ellipse at 30% 30%,
                        rgba(100, 255, 218, 0.4) 0%,
                        rgba(100, 255, 218, 0.1) 50%,
                        transparent 70%
                    );
                }
                
                /* Claim blobs */
                .blob-claim {
                    background: radial-gradient(
                        ellipse at 30% 30%,
                        rgba(189, 147, 249, 0.4) 0%,
                        rgba(189, 147, 249, 0.1) 50%,
                        transparent 70%
                    );
                }
                
                /* Gap blobs — inverted, pulling inward */
                .blob-gap {
                    background: radial-gradient(
                        ellipse at 50% 50%,
                        rgba(0, 0, 0, 0.9) 0%,
                        rgba(255, 107, 157, 0.2) 40%,
                        transparent 70%
                    );
                    filter: blur(2px);
                    animation: morph 6s ease-in-out infinite reverse;
                }
                
                /* Connection lines using CSS gradients */
                .connection {
                    position: absolute;
                    height: 1px;
                    transform-origin: left center;
                    background: linear-gradient(
                        90deg,
                        transparent 0%,
                        rgba(100, 255, 218, 0.3) 50%,
                        transparent 100%
                    );
                    animation: pulse-line 2s ease-in-out infinite;
                }
                
                @keyframes pulse-line {
                    0%, 100% { opacity: 0.3; }
                    50% { opacity: 0.7; }
                }
                
                /* Confidence indicators using conic gradients */
                .confidence-ring {
                    position: absolute;
                    border-radius: 50%;
                    background: conic-gradient(
                        from 0deg,
                        var(--ring-color) 0deg,
                        var(--ring-color) var(--confidence-deg),
                        transparent var(--confidence-deg)
                    );
                    mask: radial-gradient(
                        circle,
                        transparent 60%,
                        black 61%,
                        black 100%
                    );
                    -webkit-mask: radial-gradient(
                        circle,
                        transparent 60%,
                        black 61%,
                        black 100%
                    );
                    animation: rotate-slow 20s linear infinite;
                }
                
                @keyframes rotate-slow {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
                
                /* Label that follows blobs */
                .blob-label {
                    position: absolute;
                    font-size: 9px;
                    color: rgba(255, 255, 255, 0.5);
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                    pointer-events: none;
                    text-shadow: 0 0 10px rgba(0, 0, 0, 0.8);
                }
                
                /* Temporal wave effect */
                .temporal-wave {
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    height: 100px;
                    background: linear-gradient(
                        to top,
                        rgba(100, 255, 218, 0.05) 0%,
                        transparent 100%
                    );
                    clip-path: polygon(
                        0% 100%,
                        10% 80%,
                        20% 90%,
                        30% 70%,
                        40% 85%,
                        50% 60%,
                        60% 75%,
                        70% 55%,
                        80% 70%,
                        90% 50%,
                        100% 65%,
                        100% 100%
                    );
                    animation: wave-morph 10s ease-in-out infinite;
                }
                
                @keyframes wave-morph {
                    0%, 100% {
                        clip-path: polygon(
                            0% 100%, 10% 80%, 20% 90%, 30% 70%,
                            40% 85%, 50% 60%, 60% 75%, 70% 55%,
                            80% 70%, 90% 50%, 100% 65%, 100% 100%
                        );
                    }
                    50% {
                        clip-path: polygon(
                            0% 100%, 10% 60%, 20% 75%, 30% 55%,
                            40% 70%, 50% 45%, 60% 60%, 70% 40%,
                            80% 55%, 90% 35%, 100% 50%, 100% 100%
                        );
                    }
                }
                
                /* Info overlay */
                .info-overlay {
                    position: absolute;
                    top: 20px;
                    right: 20px;
                    font-size: 10px;
                    color: #444;
                    text-align: right;
                }
            </style>
            
            <div class="temporal-wave"></div>
            <div class="blobs-container"></div>
            <div class="info-overlay">
                <div>ORGANIC MORPHING</div>
                <div style="color: #333; margin-top: 4px;">knowledge states in flux</div>
            </div>
        `;

        this.container.appendChild(root);
        this.blobsContainer = root.querySelector('.blobs-container');

        this.createBlobs();
        this.createConnections();
        this.animate();
    }

    createBlobs() {
        const entities = this.data.entities.slice(0, 8);
        const claims = this.data.claims?.slice(0, 5) || [];
        const gaps = this.data.gaps?.slice(0, 3) || [];

        // Entity blobs
        entities.forEach((entity, i) => {
            const blob = this.createBlob(entity, 'entity', i, entities.length);
            this.shapes.push(blob);
        });

        // Claim blobs (smaller, more numerous)
        claims.forEach((claim, i) => {
            const blob = this.createBlob(claim, 'claim', i, claims.length);
            this.shapes.push(blob);
        });

        // Gap blobs (inverted)
        gaps.forEach((gap, i) => {
            const blob = this.createBlob(gap, 'gap', i, gaps.length);
            this.shapes.push(blob);
        });
    }

    createBlob(item, type, index, total) {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;

        // Organic positioning based on type
        const angle = (index / total) * Math.PI * 2 + (type === 'claim' ? Math.PI / 4 : 0);
        const radius = type === 'gap' ? 150 : 200 + Math.random() * 100;

        const x = width / 2 + Math.cos(angle) * radius;
        const y = height / 2 + Math.sin(angle) * radius;

        const confidence = item.confidence || 0.7;
        const size = type === 'entity' ? 120 + confidence * 80 :
            type === 'claim' ? 80 + confidence * 40 :
                100 + (item.severity || 0.5) * 80;

        // Blob element
        const blob = document.createElement('div');
        blob.className = `knowledge-blob blob-${type}`;
        blob.style.cssText = `
            left: ${x - size / 2}px;
            top: ${y - size / 2}px;
            width: ${size}px;
            height: ${size}px;
            animation-delay: ${-index * 0.8}s;
            animation-duration: ${6 + Math.random() * 4}s;
        `;

        // Confidence ring
        if (type !== 'gap') {
            const ring = document.createElement('div');
            ring.className = 'confidence-ring';
            ring.style.cssText = `
                left: ${x - size / 2 - 10}px;
                top: ${y - size / 2 - 10}px;
                width: ${size + 20}px;
                height: ${size + 20}px;
                --ring-color: ${type === 'entity' ? 'rgba(100, 255, 218, 0.3)' : 'rgba(189, 147, 249, 0.3)'};
                --confidence-deg: ${confidence * 360}deg;
                animation-delay: ${-index * 2}s;
            `;
            this.blobsContainer.appendChild(ring);
        }

        // Label
        const label = document.createElement('div');
        label.className = 'blob-label';
        label.textContent = item.name || item.text?.slice(0, 20) || 'Gap';
        label.style.cssText = `
            left: ${x}px;
            top: ${y + size / 2 + 10}px;
            transform: translateX(-50%);
        `;

        this.blobsContainer.appendChild(blob);
        this.blobsContainer.appendChild(label);

        return { element: blob, x, y, type, item };
    }

    createConnections() {
        // Create organic connections between related blobs
        for (let i = 0; i < this.shapes.length; i++) {
            for (let j = i + 1; j < this.shapes.length; j++) {
                // Only connect some pairs for organic feel
                if (Math.random() > 0.3) continue;

                const a = this.shapes[i];
                const b = this.shapes[j];

                const line = document.createElement('div');
                line.className = 'connection';

                const dx = b.x - a.x;
                const dy = b.y - a.y;
                const length = Math.sqrt(dx * dx + dy * dy);
                const angle = Math.atan2(dy, dx) * 180 / Math.PI;

                line.style.cssText = `
                    left: ${a.x}px;
                    top: ${a.y}px;
                    width: ${length}px;
                    transform: rotate(${angle}deg);
                    animation-delay: ${-Math.random() * 2}s;
                `;

                this.blobsContainer.appendChild(line);
            }
        }
    }

    animate() {
        // Optional: add JS-driven animation updates
        // CSS handles most of it, but we can add mouse tracking

        document.addEventListener('mousemove', (e) => {
            const x = e.clientX / window.innerWidth;
            const y = e.clientY / window.innerHeight;

            this.shapes.forEach((shape, i) => {
                const offset = 10 * Math.sin(Date.now() * 0.001 + i);
                const px = (x - 0.5) * 20 + offset;
                const py = (y - 0.5) * 20 + offset;
                shape.element.style.transform = `translate(${px}px, ${py}px)`;
            });
        });
    }

    dispose() {
        this.container.querySelector('#organic-morph')?.remove();
    }
}

export default OrganicMorphingVisualizer;
