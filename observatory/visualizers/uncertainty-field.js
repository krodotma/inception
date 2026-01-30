// ════════════════════════════════════════════════════════════════════════════
// UNCERTAINTY FIELD — Epistemic/Aleatoric Noise Visualization
//
// COGNITIVE PURPOSE: Feel uncertainty, not just see numbers
// TECH: Raw WebGL with perlin noise mapped to uncertainty model
// ANTI-CORPORATE: Noise as truth — imperfection is the message
// ════════════════════════════════════════════════════════════════════════════

import { DataContracts } from '../lib/mock-data.js';

export class UncertaintyFieldVisualizer {
    constructor(container) {
        this.container = container;
        this.data = DataContracts.getConfidenceTopology();
        this.gl = null;
        this.startTime = Date.now();
    }

    init() {
        const canvas = document.createElement('canvas');
        canvas.width = this.container.clientWidth;
        canvas.height = this.container.clientHeight;
        canvas.style.cssText = 'position:absolute;top:0;left:0;';
        this.container.appendChild(canvas);
        this.canvas = canvas;

        this.gl = canvas.getContext('webgl');
        if (!this.gl) return;

        this.initShaders();
        this.initBuffers();
        this.animate();
    }

    vertexShaderSource = `
        attribute vec2 a_position;
        varying vec2 v_uv;
        void main() {
            v_uv = a_position * 0.5 + 0.5;
            gl_Position = vec4(a_position, 0.0, 1.0);
        }
    `;

    // Dual uncertainty visualization: epistemic (what we don't know) 
    // vs aleatoric (inherent randomness)
    fragmentShaderSource = `
        precision highp float;
        
        varying vec2 v_uv;
        uniform float u_time;
        uniform vec2 u_resolution;
        uniform float u_epistemic;   // Reducible uncertainty
        uniform float u_aleatoric;   // Irreducible uncertainty
        uniform vec2 u_dataPoints[10];
        uniform float u_confidence[10];
        
        // 3D gradient noise
        vec3 hash3(vec3 p) {
            p = vec3(dot(p, vec3(127.1, 311.7, 74.7)),
                     dot(p, vec3(269.5, 183.3, 246.1)),
                     dot(p, vec3(113.5, 271.9, 124.6)));
            return fract(sin(p) * 43758.5453123);
        }
        
        float gradientNoise(vec3 x) {
            vec3 i = floor(x);
            vec3 f = fract(x);
            vec3 u = f * f * (3.0 - 2.0 * f);
            
            return mix(mix(mix(dot(hash3(i + vec3(0,0,0)) - 0.5, f - vec3(0,0,0)),
                               dot(hash3(i + vec3(1,0,0)) - 0.5, f - vec3(1,0,0)), u.x),
                           mix(dot(hash3(i + vec3(0,1,0)) - 0.5, f - vec3(0,1,0)),
                               dot(hash3(i + vec3(1,1,0)) - 0.5, f - vec3(1,1,0)), u.x), u.y),
                       mix(mix(dot(hash3(i + vec3(0,0,1)) - 0.5, f - vec3(0,0,1)),
                               dot(hash3(i + vec3(1,0,1)) - 0.5, f - vec3(1,0,1)), u.x),
                           mix(dot(hash3(i + vec3(0,1,1)) - 0.5, f - vec3(0,1,1)),
                               dot(hash3(i + vec3(1,1,1)) - 0.5, f - vec3(1,1,1)), u.x), u.y), u.z);
        }
        
        // Epistemic noise: structured, reducible with more data
        float epistemicNoise(vec2 p, float time) {
            float noise = 0.0;
            float amp = 0.5;
            float freq = 3.0;
            
            // Layered, but coherent — this uncertainty has structure
            for (int i = 0; i < 4; i++) {
                noise += amp * gradientNoise(vec3(p * freq, time * 0.2));
                amp *= 0.5;
                freq *= 2.0;
            }
            return noise;
        }
        
        // Aleatoric noise: chaotic, irreducible randomness
        float aleatoricNoise(vec2 p, float time) {
            // High frequency, no coherent structure
            float noise = gradientNoise(vec3(p * 20.0, time));
            noise += 0.5 * gradientNoise(vec3(p * 40.0, time * 1.5));
            noise += 0.25 * gradientNoise(vec3(p * 80.0, time * 2.0));
            return noise;
        }
        
        void main() {
            vec2 uv = v_uv;
            float time = u_time;
            
            // Base: epistemic uncertainty field (purple-ish, structured)
            float epist = epistemicNoise(uv, time) * u_epistemic;
            
            // Overlay: aleatoric uncertainty (red-ish, chaotic)
            float aleat = aleatoricNoise(uv, time) * u_aleatoric;
            
            // Combine uncertainties
            float totalUncertainty = epist + aleat * 0.5;
            
            // Confidence wells — high confidence creates calm zones
            for (int i = 0; i < 10; i++) {
                vec2 dataPoint = u_dataPoints[i];
                if (dataPoint.x == 0.0 && dataPoint.y == 0.0) continue;
                
                float dist = length(uv - dataPoint);
                float conf = u_confidence[i];
                
                // Confidence suppresses uncertainty
                float well = smoothstep(0.15, 0.0, dist) * conf;
                totalUncertainty *= (1.0 - well * 0.8);
            }
            
            // Color mapping
            // Low uncertainty: calm cyan
            // High epistemic: structured purple
            // High aleatoric: chaotic red noise
            vec3 calmColor = vec3(0.1, 0.2, 0.25);
            vec3 epistemicColor = vec3(0.3, 0.1, 0.4);
            vec3 aleatoricColor = vec3(0.4, 0.1, 0.15);
            
            vec3 color = calmColor;
            color = mix(color, epistemicColor, smoothstep(0.0, 0.5, epist));
            color = mix(color, aleatoricColor, smoothstep(0.0, 0.5, aleat));
            
            // Noise texture on top
            float noiseTexture = fract(sin(dot(uv * 1000.0, vec2(12.9898, 78.233))) * 43758.5453);
            color += (noiseTexture - 0.5) * 0.03 * totalUncertainty;
            
            // Confidence points as stable glowing dots
            for (int i = 0; i < 10; i++) {
                vec2 dataPoint = u_dataPoints[i];
                if (dataPoint.x == 0.0 && dataPoint.y == 0.0) continue;
                
                float dist = length(uv - dataPoint);
                float conf = u_confidence[i];
                
                // Glow
                float glow = exp(-dist * 30.0) * conf;
                vec3 glowColor = mix(vec3(0.8, 0.3, 0.3), vec3(0.2, 0.8, 0.6), conf);
                color += glowColor * glow;
            }
            
            gl_FragColor = vec4(color, 1.0);
        }
    `;

    initShaders() {
        const gl = this.gl;

        const vs = gl.createShader(gl.VERTEX_SHADER);
        gl.shaderSource(vs, this.vertexShaderSource);
        gl.compileShader(vs);

        const fs = gl.createShader(gl.FRAGMENT_SHADER);
        gl.shaderSource(fs, this.fragmentShaderSource);
        gl.compileShader(fs);

        if (!gl.getShaderParameter(fs, gl.COMPILE_STATUS)) {
            console.error('Fragment shader:', gl.getShaderInfoLog(fs));
        }

        this.program = gl.createProgram();
        gl.attachShader(this.program, vs);
        gl.attachShader(this.program, fs);
        gl.linkProgram(this.program);
        gl.useProgram(this.program);

        this.uniforms = {
            time: gl.getUniformLocation(this.program, 'u_time'),
            resolution: gl.getUniformLocation(this.program, 'u_resolution'),
            epistemic: gl.getUniformLocation(this.program, 'u_epistemic'),
            aleatoric: gl.getUniformLocation(this.program, 'u_aleatoric'),
            dataPoints: gl.getUniformLocation(this.program, 'u_dataPoints'),
            confidence: gl.getUniformLocation(this.program, 'u_confidence'),
        };
    }

    initBuffers() {
        const gl = this.gl;
        const positions = new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]);
        const buffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
        gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW);

        const posLoc = gl.getAttribLocation(this.program, 'a_position');
        gl.enableVertexAttribArray(posLoc);
        gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);
    }

    render() {
        const gl = this.gl;
        const time = (Date.now() - this.startTime) * 0.001;

        gl.viewport(0, 0, this.canvas.width, this.canvas.height);

        gl.uniform1f(this.uniforms.time, time);
        gl.uniform2f(this.uniforms.resolution, this.canvas.width, this.canvas.height);

        // Uncertainty levels from data
        gl.uniform1f(this.uniforms.epistemic, 0.6);
        gl.uniform1f(this.uniforms.aleatoric, 0.4);

        // Data points with confidence - ConfidenceTopology returns 'nodes' not 'dataPoints'
        const points = [];
        const confidences = [];
        const nodes = this.data.nodes || [];
        nodes.slice(0, 10).forEach(p => {
            // Use normalized x/y from topology (they're 0-100 range)
            points.push((p.x || 50) / 100, (p.y || 50) / 100);
            confidences.push(p.z ? p.z / 50 : 0.5); // z is confidence * 50
        });
        while (points.length < 20) { points.push(0, 0); confidences.push(0); }

        gl.uniform2fv(this.uniforms.dataPoints, new Float32Array(points));
        gl.uniform1fv(this.uniforms.confidence, new Float32Array(confidences));

        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    }

    animate() {
        this.render();
        this.animationId = requestAnimationFrame(() => this.animate());
    }

    dispose() {
        cancelAnimationFrame(this.animationId);
        this.canvas?.remove();
    }
}

export default UncertaintyFieldVisualizer;
