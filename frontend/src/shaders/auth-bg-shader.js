/**
 * OPUS-2: Auth Background Shader
 * 
 * Subtle WebGL background for Agent Auth overlay:
 * - Animated gradient mesh
 * - Cursor-reactive glow
 * - Provider-colored particle streams
 * - Performance-optimized (mobile-friendly)
 */

class AuthBackgroundShader {
    constructor(canvas, options = {}) {
        this.canvas = typeof canvas === 'string' ? document.querySelector(canvas) : canvas;
        this.gl = null;
        this.program = null;
        this.animationId = null;
        this.startTime = Date.now();
        this.mouseX = 0.5;
        this.mouseY = 0.5;

        this.options = {
            colors: {
                claude: [0.545, 0.361, 0.965],   // #8B5CF6
                gemini: [0.259, 0.522, 0.957],   // #4285F4
                codex: [0.063, 0.725, 0.506],    // #10B981
                kimi: [0.961, 0.620, 0.043]      // #F59E0B
            },
            intensity: 0.3,
            speed: 0.5,
            ...options
        };

        this.init();
    }

    init() {
        if (!this.canvas) {
            console.warn('[AuthBgShader] Canvas not found');
            return;
        }

        this.gl = this.canvas.getContext('webgl') || this.canvas.getContext('experimental-webgl');
        if (!this.gl) {
            console.warn('[AuthBgShader] WebGL not supported, falling back to CSS');
            this.canvas.classList.add('alive-gradient-bg');
            return;
        }

        this.createShaders();
        this.createBuffers();
        this.setupMouseTracking();
        this.resize();
        this.animate();

        window.addEventListener('resize', () => this.resize());
    }

    createShaders() {
        const vsSource = `
            attribute vec2 a_position;
            varying vec2 v_uv;
            void main() {
                v_uv = a_position * 0.5 + 0.5;
                gl_Position = vec4(a_position, 0.0, 1.0);
            }
        `;

        const fsSource = `
            precision mediump float;
            varying vec2 v_uv;
            uniform float u_time;
            uniform vec2 u_mouse;
            uniform vec2 u_resolution;
            uniform float u_intensity;
            
            // Provider colors
            uniform vec3 u_color1; // Claude
            uniform vec3 u_color2; // Gemini
            uniform vec3 u_color3; // Codex
            uniform vec3 u_color4; // Kimi
            
            // Simplex noise approximation
            float noise(vec2 p) {
                return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
            }
            
            float smoothNoise(vec2 p) {
                vec2 i = floor(p);
                vec2 f = fract(p);
                f = f * f * (3.0 - 2.0 * f);
                
                float a = noise(i);
                float b = noise(i + vec2(1.0, 0.0));
                float c = noise(i + vec2(0.0, 1.0));
                float d = noise(i + vec2(1.0, 1.0));
                
                return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
            }
            
            void main() {
                vec2 uv = v_uv;
                float t = u_time * 0.3;
                
                // Cursor influence
                float cursorDist = distance(uv, u_mouse);
                float cursorGlow = smoothstep(0.5, 0.0, cursorDist) * 0.3;
                
                // Animated gradient mesh
                float n1 = smoothNoise(uv * 3.0 + t);
                float n2 = smoothNoise(uv * 2.0 - t * 0.7);
                float n3 = smoothNoise(uv * 4.0 + vec2(t * 0.5, -t * 0.3));
                
                // Mix provider colors based on position and noise
                vec3 color = vec3(0.04, 0.04, 0.06); // Base dark
                
                // Claude (top-left quadrant influence)
                float c1 = smoothstep(0.3, 0.7, 1.0 - uv.x) * smoothstep(0.3, 0.7, 1.0 - uv.y) * n1;
                color += u_color1 * c1 * u_intensity;
                
                // Gemini (top-right)
                float c2 = smoothstep(0.3, 0.7, uv.x) * smoothstep(0.3, 0.7, 1.0 - uv.y) * n2;
                color += u_color2 * c2 * u_intensity;
                
                // Codex (bottom-left)
                float c3 = smoothstep(0.3, 0.7, 1.0 - uv.x) * smoothstep(0.3, 0.7, uv.y) * n3;
                color += u_color3 * c3 * u_intensity;
                
                // Kimi (bottom-right)
                float c4 = smoothstep(0.3, 0.7, uv.x) * smoothstep(0.3, 0.7, uv.y) * n1 * n2;
                color += u_color4 * c4 * u_intensity;
                
                // Cursor glow (white highlight)
                color += vec3(1.0) * cursorGlow;
                
                // Vignette
                float vignette = 1.0 - smoothstep(0.4, 1.0, length(uv - 0.5) * 1.2);
                color *= vignette;
                
                gl_FragColor = vec4(color, 1.0);
            }
        `;

        const gl = this.gl;

        // Compile shaders
        const vs = this.compileShader(gl.VERTEX_SHADER, vsSource);
        const fs = this.compileShader(gl.FRAGMENT_SHADER, fsSource);

        // Create program
        this.program = gl.createProgram();
        gl.attachShader(this.program, vs);
        gl.attachShader(this.program, fs);
        gl.linkProgram(this.program);

        if (!gl.getProgramParameter(this.program, gl.LINK_STATUS)) {
            console.error('[AuthBgShader] Program link failed:', gl.getProgramInfoLog(this.program));
            return;
        }

        gl.useProgram(this.program);

        // Get uniform locations
        this.uniforms = {
            time: gl.getUniformLocation(this.program, 'u_time'),
            mouse: gl.getUniformLocation(this.program, 'u_mouse'),
            resolution: gl.getUniformLocation(this.program, 'u_resolution'),
            intensity: gl.getUniformLocation(this.program, 'u_intensity'),
            color1: gl.getUniformLocation(this.program, 'u_color1'),
            color2: gl.getUniformLocation(this.program, 'u_color2'),
            color3: gl.getUniformLocation(this.program, 'u_color3'),
            color4: gl.getUniformLocation(this.program, 'u_color4')
        };

        // Set static uniforms
        gl.uniform1f(this.uniforms.intensity, this.options.intensity);
        gl.uniform3fv(this.uniforms.color1, this.options.colors.claude);
        gl.uniform3fv(this.uniforms.color2, this.options.colors.gemini);
        gl.uniform3fv(this.uniforms.color3, this.options.colors.codex);
        gl.uniform3fv(this.uniforms.color4, this.options.colors.kimi);
    }

    compileShader(type, source) {
        const gl = this.gl;
        const shader = gl.createShader(type);
        gl.shaderSource(shader, source);
        gl.compileShader(shader);

        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
            console.error('[AuthBgShader] Shader compile failed:', gl.getShaderInfoLog(shader));
            gl.deleteShader(shader);
            return null;
        }
        return shader;
    }

    createBuffers() {
        const gl = this.gl;
        const positions = new Float32Array([
            -1, -1,
            1, -1,
            -1, 1,
            1, 1
        ]);

        const buffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
        gl.bufferData(gl.ARRAY_BUFFER, positions, gl.STATIC_DRAW);

        const posLoc = gl.getAttribLocation(this.program, 'a_position');
        gl.enableVertexAttribArray(posLoc);
        gl.vertexAttribPointer(posLoc, 2, gl.FLOAT, false, 0, 0);
    }

    setupMouseTracking() {
        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            this.mouseX = (e.clientX - rect.left) / rect.width;
            this.mouseY = 1.0 - (e.clientY - rect.top) / rect.height;
        });
    }

    resize() {
        const dpr = window.devicePixelRatio || 1;
        const width = this.canvas.clientWidth * dpr;
        const height = this.canvas.clientHeight * dpr;

        this.canvas.width = width;
        this.canvas.height = height;
        this.gl.viewport(0, 0, width, height);
        this.gl.uniform2f(this.uniforms.resolution, width, height);
    }

    animate() {
        const gl = this.gl;
        const time = (Date.now() - this.startTime) * 0.001 * this.options.speed;

        gl.uniform1f(this.uniforms.time, time);
        gl.uniform2f(this.uniforms.mouse, this.mouseX, this.mouseY);

        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

        this.animationId = requestAnimationFrame(() => this.animate());
    }

    /**
     * Update provider connection status (affects glow intensity)
     */
    setProviderActive(provider, active) {
        const intensity = active ? 0.4 : 0.15;
        const colors = { ...this.options.colors };

        if (colors[provider]) {
            // Boost active provider color
            const boost = active ? 1.3 : 0.7;
            const boosted = colors[provider].map(c => Math.min(1, c * boost));
            this.gl.uniform3fv(this.uniforms[`color${Object.keys(colors).indexOf(provider) + 1}`], boosted);
        }
    }

    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        if (this.gl && this.program) {
            this.gl.deleteProgram(this.program);
        }
    }
}

export { AuthBackgroundShader };
export default AuthBackgroundShader;
