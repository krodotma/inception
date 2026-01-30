// ════════════════════════════════════════════════════════════════════════════
// VOID SHADER — Shadertoy-Style Raw WebGL
//
// COGNITIVE PURPOSE: Visualize the unknown — the territory beyond knowledge
// VISUAL: Fractal noise void with event horizon distortion
// TECH: Pure WebGL, no libraries, Shadertoy-inspired GLSL
// ════════════════════════════════════════════════════════════════════════════

import { DataContracts } from '../lib/mock-data.js';

export class VoidShaderVisualizer {
    constructor(container) {
        this.container = container;
        this.data = DataContracts.getGapConstellation();
        this.gl = null;
        this.program = null;
        this.startTime = Date.now();
    }

    init() {
        const canvas = document.createElement('canvas');
        canvas.width = this.container.clientWidth;
        canvas.height = this.container.clientHeight;
        canvas.style.cssText = 'position:absolute;top:0;left:0;';
        this.container.appendChild(canvas);
        this.canvas = canvas;

        this.gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
        if (!this.gl) {
            console.error('WebGL not supported');
            return;
        }

        this.initShaders();
        this.initBuffers();
        this.animate();
    }

    // Shadertoy-inspired vertex shader
    vertexShaderSource = `
        attribute vec2 a_position;
        varying vec2 v_uv;
        void main() {
            v_uv = a_position * 0.5 + 0.5;
            gl_Position = vec4(a_position, 0.0, 1.0);
        }
    `;

    // Shadertoy-inspired fragment shader — fractal void with knowledge gaps
    fragmentShaderSource = `
        precision highp float;
        
        varying vec2 v_uv;
        uniform float u_time;
        uniform vec2 u_resolution;
        uniform vec2 u_gaps[5];    // Gap positions (normalized)
        uniform float u_severity[5]; // Gap severities
        uniform int u_gapCount;
        
        // Simplex noise for organic void texture
        vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
        vec2 mod289(vec2 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
        vec3 permute(vec3 x) { return mod289(((x*34.0)+1.0)*x); }
        
        float snoise(vec2 v) {
            const vec4 C = vec4(0.211324865405187, 0.366025403784439,
                               -0.577350269189626, 0.024390243902439);
            vec2 i  = floor(v + dot(v, C.yy));
            vec2 x0 = v - i + dot(i, C.xx);
            vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
            vec4 x12 = x0.xyxy + C.xxzz;
            x12.xy -= i1;
            i = mod289(i);
            vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0))
                           + i.x + vec3(0.0, i1.x, 1.0));
            vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy),
                                    dot(x12.zw,x12.zw)), 0.0);
            m = m*m*m*m;
            vec3 x = 2.0 * fract(p * C.www) - 1.0;
            vec3 h = abs(x) - 0.5;
            vec3 ox = floor(x + 0.5);
            vec3 a0 = x - ox;
            m *= 1.79284291400159 - 0.85373472095314 * (a0*a0 + h*h);
            vec3 g;
            g.x = a0.x * x0.x + h.x * x0.y;
            g.yz = a0.yz * x12.xz + h.yz * x12.yw;
            return 130.0 * dot(m, g);
        }
        
        // Fractal Brownian Motion
        float fbm(vec2 p) {
            float value = 0.0;
            float amplitude = 0.5;
            float frequency = 1.0;
            for (int i = 0; i < 6; i++) {
                value += amplitude * snoise(p * frequency);
                amplitude *= 0.5;
                frequency *= 2.0;
            }
            return value;
        }
        
        // Event horizon distortion
        vec2 distort(vec2 uv, vec2 center, float strength) {
            vec2 dir = uv - center;
            float dist = length(dir);
            float pull = strength / (dist * dist + 0.1);
            return uv - normalize(dir) * pull * 0.1;
        }
        
        void main() {
            vec2 uv = v_uv;
            vec2 aspect = vec2(u_resolution.x / u_resolution.y, 1.0);
            vec2 uvAspect = uv * aspect;
            
            // Apply distortion from each gap (event horizons)
            for (int i = 0; i < 5; i++) {
                if (i >= u_gapCount) break;
                vec2 gapPos = u_gaps[i] * aspect;
                float severity = u_severity[i];
                uvAspect = distort(uvAspect, gapPos, severity * 0.3);
            }
            
            vec2 distortedUV = uvAspect / aspect;
            
            // Layered fractal void
            float time = u_time * 0.15;
            
            // Deep void layer (slow, large scale)
            float void1 = fbm(distortedUV * 2.0 + time * 0.2);
            
            // Turbulent layer (medium)
            float void2 = fbm(distortedUV * 5.0 - time * 0.3 + vec2(void1 * 0.5));
            
            // Detail layer (fast, small scale)
            float void3 = fbm(distortedUV * 12.0 + time * 0.5 + vec2(void2 * 0.3));
            
            // Combine layers
            float voidValue = void1 * 0.5 + void2 * 0.3 + void3 * 0.2;
            
            // Color: deep indigo to void black
            vec3 deepColor = vec3(0.02, 0.02, 0.08);
            vec3 midColor = vec3(0.1, 0.05, 0.2);
            vec3 highlightColor = vec3(0.3, 0.15, 0.4);
            
            float t = smoothstep(-0.5, 0.8, voidValue);
            vec3 color = mix(deepColor, midColor, t);
            color = mix(color, highlightColor, smoothstep(0.6, 1.0, voidValue));
            
            // Gap event horizons — rings of light at the edge of knowledge
            for (int i = 0; i < 5; i++) {
                if (i >= u_gapCount) break;
                vec2 gapPos = u_gaps[i];
                float dist = length(v_uv - gapPos);
                float severity = u_severity[i];
                
                // Event horizon ring
                float ring = smoothstep(0.12 * severity, 0.1 * severity, abs(dist - 0.15));
                ring *= 0.5 + 0.5 * sin(u_time * 3.0 + dist * 20.0);
                
                // Gap glow color based on severity
                vec3 gapColor = mix(
                    vec3(0.2, 0.4, 0.8),  // Low severity: blue
                    vec3(0.8, 0.2, 0.3),  // High severity: red
                    severity
                );
                
                color += gapColor * ring * severity;
                
                // Inner darkness (the void itself)
                float innerVoid = smoothstep(0.08, 0.02, dist) * severity;
                color = mix(color, vec3(0.0), innerVoid);
            }
            
            // Subtle vignette
            float vignette = 1.0 - length(v_uv - 0.5) * 0.8;
            color *= vignette;
            
            gl_FragColor = vec4(color, 1.0);
        }
    `;

    initShaders() {
        const gl = this.gl;

        // Compile vertex shader
        const vertexShader = gl.createShader(gl.VERTEX_SHADER);
        gl.shaderSource(vertexShader, this.vertexShaderSource);
        gl.compileShader(vertexShader);

        if (!gl.getShaderParameter(vertexShader, gl.COMPILE_STATUS)) {
            console.error('Vertex shader error:', gl.getShaderInfoLog(vertexShader));
            return;
        }

        // Compile fragment shader
        const fragmentShader = gl.createShader(gl.FRAGMENT_SHADER);
        gl.shaderSource(fragmentShader, this.fragmentShaderSource);
        gl.compileShader(fragmentShader);

        if (!gl.getShaderParameter(fragmentShader, gl.COMPILE_STATUS)) {
            console.error('Fragment shader error:', gl.getShaderInfoLog(fragmentShader));
            return;
        }

        // Link program
        this.program = gl.createProgram();
        gl.attachShader(this.program, vertexShader);
        gl.attachShader(this.program, fragmentShader);
        gl.linkProgram(this.program);

        if (!gl.getProgramParameter(this.program, gl.LINK_STATUS)) {
            console.error('Program link error:', gl.getProgramInfoLog(this.program));
            return;
        }

        gl.useProgram(this.program);

        // Get uniform locations
        this.uniforms = {
            time: gl.getUniformLocation(this.program, 'u_time'),
            resolution: gl.getUniformLocation(this.program, 'u_resolution'),
            gaps: gl.getUniformLocation(this.program, 'u_gaps'),
            severity: gl.getUniformLocation(this.program, 'u_severity'),
            gapCount: gl.getUniformLocation(this.program, 'u_gapCount'),
        };
    }

    initBuffers() {
        const gl = this.gl;

        // Full-screen quad
        const positions = new Float32Array([
            -1, -1,
            1, -1,
            -1, 1,
            1, 1,
        ]);

        const buffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
        gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW);

        const positionLoc = gl.getAttribLocation(this.program, 'a_position');
        gl.enableVertexAttribArray(positionLoc);
        gl.vertexAttribPointer(positionLoc, 2, gl.FLOAT, false, 0, 0);
    }

    render() {
        const gl = this.gl;
        const time = (Date.now() - this.startTime) * 0.001;

        gl.viewport(0, 0, this.canvas.width, this.canvas.height);

        // Set uniforms
        gl.uniform1f(this.uniforms.time, time);
        gl.uniform2f(this.uniforms.resolution, this.canvas.width, this.canvas.height);

        // Set gap data from mock data
        const gaps = this.data.gaps.slice(0, 5);
        const gapPositions = [];
        const severities = [];

        gaps.forEach((gap, i) => {
            // Distribute gaps across the canvas
            gapPositions.push(0.2 + (i % 3) * 0.3, 0.3 + Math.floor(i / 3) * 0.4);
            severities.push(gap.severity || 0.5);
        });

        // Pad to 5 gaps
        while (gapPositions.length < 10) {
            gapPositions.push(0, 0);
            severities.push(0);
        }

        gl.uniform2fv(this.uniforms.gaps, new Float32Array(gapPositions));
        gl.uniform1fv(this.uniforms.severity, new Float32Array(severities));
        gl.uniform1i(this.uniforms.gapCount, gaps.length);

        // Draw
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

export default VoidShaderVisualizer;
