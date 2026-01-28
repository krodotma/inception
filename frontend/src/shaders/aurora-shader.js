/**
 * OPUS-2 ITERATION 2: Aurora Shader Engine
 * 
 * Ethereal background effects:
 * - Aurora borealis waves
 * - Chromatic aberration
 * - Noise-based distortion
 * - Provider-colored ribbons
 * - Reactive to audio/input
 */

class AuroraShaderEngine {
    constructor(canvas) {
        this.canvas = typeof canvas === 'string' ? document.querySelector(canvas) : canvas;
        if (!this.canvas) {
            this.canvas = this.createCanvas();
        }

        this.gl = this.canvas.getContext('webgl2') || this.canvas.getContext('webgl');
        if (!this.gl) {
            console.warn('[AuroraShader] WebGL not supported, using CSS fallback');
            this.useCSSFallback();
            return;
        }

        this.program = null;
        this.startTime = Date.now();
        this.mouseX = 0.5;
        this.mouseY = 0.5;
        this.audioLevel = 0;
        this.providerHue = 280; // Default purple

        this.init();
    }

    createCanvas() {
        const canvas = document.createElement('canvas');
        canvas.id = 'aurora-canvas';
        canvas.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: -1;
        `;
        document.body.insertBefore(canvas, document.body.firstChild);
        return canvas;
    }

    init() {
        this.resize();
        window.addEventListener('resize', () => this.resize());
        document.addEventListener('mousemove', (e) => {
            this.mouseX = e.clientX / window.innerWidth;
            this.mouseY = e.clientY / window.innerHeight;
        });

        this.createShaders();
        this.render();

        console.log('[AuroraShader] ✨ Ethereal effects active');
    }

    resize() {
        const dpr = window.devicePixelRatio || 1;
        this.canvas.width = window.innerWidth * dpr;
        this.canvas.height = window.innerHeight * dpr;
        if (this.gl) {
            this.gl.viewport(0, 0, this.canvas.width, this.canvas.height);
        }
    }

    createShaders() {
        const vertexSource = `
            attribute vec2 a_position;
            void main() {
                gl_Position = vec4(a_position, 0.0, 1.0);
            }
        `;

        const fragmentSource = `
            precision highp float;
            
            uniform float u_time;
            uniform vec2 u_resolution;
            uniform vec2 u_mouse;
            uniform float u_hue;
            uniform float u_audio;
            
            #define PI 3.14159265359
            
            // Simplex noise
            vec3 permute(vec3 x) { return mod(((x*34.0)+1.0)*x, 289.0); }
            
            float snoise(vec2 v) {
                const vec4 C = vec4(0.211324865405187, 0.366025403784439,
                                   -0.577350269189626, 0.024390243902439);
                vec2 i  = floor(v + dot(v, C.yy));
                vec2 x0 = v - i + dot(i, C.xx);
                vec2 i1;
                i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
                vec4 x12 = x0.xyxy + C.xxzz;
                x12.xy -= i1;
                i = mod(i, 289.0);
                vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0))
                    + i.x + vec3(0.0, i1.x, 1.0));
                vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy),
                    dot(x12.zw,x12.zw)), 0.0);
                m = m*m;
                m = m*m;
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
            
            vec3 hsv2rgb(vec3 c) {
                vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
                vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
                return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
            }
            
            void main() {
                vec2 uv = gl_FragCoord.xy / u_resolution;
                vec2 st = uv * 2.0 - 1.0;
                st.x *= u_resolution.x / u_resolution.y;
                
                float time = u_time * 0.15;
                
                // Aurora waves
                float aurora = 0.0;
                for (float i = 1.0; i <= 5.0; i++) {
                    float n = snoise(vec2(
                        st.x * 0.3 * i + time * 0.5,
                        st.y * 0.5 + time * 0.2 * i
                    ));
                    aurora += n * (0.5 / i);
                }
                
                // Mouse influence
                vec2 mouseOffset = (u_mouse - 0.5) * 0.3;
                float mouseGlow = 0.3 / (length(uv - u_mouse) + 0.3);
                
                // Vertical ribbons
                float ribbon1 = sin(st.x * 8.0 + time * 2.0 + aurora * 3.0) * 0.5 + 0.5;
                float ribbon2 = sin(st.x * 6.0 - time * 1.5 + aurora * 2.0) * 0.5 + 0.5;
                
                // Height-based fade
                float heightFade = smoothstep(-0.5, 1.5, st.y + aurora * 0.5);
                
                // Color based on provider hue
                float hue = u_hue / 360.0 + aurora * 0.1 + ribbon1 * 0.05;
                float saturation = 0.7 + ribbon2 * 0.3;
                float brightness = heightFade * (0.3 + aurora * 0.2 + mouseGlow * 0.2);
                
                // Audio reactivity
                brightness *= 1.0 + u_audio * 0.5;
                
                vec3 color = hsv2rgb(vec3(hue, saturation, brightness));
                
                // Add chromatic aberration
                float aberration = 0.003;
                vec3 finalColor;
                finalColor.r = color.r;
                finalColor.g = hsv2rgb(vec3(hue + aberration, saturation, brightness)).g;
                finalColor.b = hsv2rgb(vec3(hue - aberration, saturation, brightness)).b;
                
                // Vignette
                float vignette = 1.0 - length(st) * 0.4;
                finalColor *= vignette;
                
                gl_FragColor = vec4(finalColor, brightness * 0.6);
            }
        `;

        const gl = this.gl;

        // Compile shaders
        const vertexShader = gl.createShader(gl.VERTEX_SHADER);
        gl.shaderSource(vertexShader, vertexSource);
        gl.compileShader(vertexShader);

        const fragmentShader = gl.createShader(gl.FRAGMENT_SHADER);
        gl.shaderSource(fragmentShader, fragmentSource);
        gl.compileShader(fragmentShader);

        // Create program
        this.program = gl.createProgram();
        gl.attachShader(this.program, vertexShader);
        gl.attachShader(this.program, fragmentShader);
        gl.linkProgram(this.program);
        gl.useProgram(this.program);

        // Create fullscreen quad
        const vertices = new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]);
        const buffer = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
        gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);

        const positionLocation = gl.getAttribLocation(this.program, 'a_position');
        gl.enableVertexAttribArray(positionLocation);
        gl.vertexAttribPointer(positionLocation, 2, gl.FLOAT, false, 0, 0);

        // Enable blending
        gl.enable(gl.BLEND);
        gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
    }

    render() {
        if (!this.gl) return;

        const gl = this.gl;
        const time = (Date.now() - this.startTime) / 1000;

        gl.clearColor(0, 0, 0, 0);
        gl.clear(gl.COLOR_BUFFER_BIT);

        // Set uniforms
        gl.uniform1f(gl.getUniformLocation(this.program, 'u_time'), time);
        gl.uniform2f(gl.getUniformLocation(this.program, 'u_resolution'),
            this.canvas.width, this.canvas.height);
        gl.uniform2f(gl.getUniformLocation(this.program, 'u_mouse'),
            this.mouseX, 1.0 - this.mouseY);
        gl.uniform1f(gl.getUniformLocation(this.program, 'u_hue'), this.providerHue);
        gl.uniform1f(gl.getUniformLocation(this.program, 'u_audio'), this.audioLevel);

        // Draw
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

        requestAnimationFrame(() => this.render());
    }

    setProviderColor(provider) {
        const hues = {
            claude: 280,   // Purple
            gemini: 220,   // Blue
            codex: 160,    // Green
            kimi: 40       // Amber
        };
        this.providerHue = hues[provider] || 280;
    }

    setAudioLevel(level) {
        this.audioLevel = Math.max(0, Math.min(1, level));
    }

    useCSSFallback() {
        this.canvas.style.background = `
            linear-gradient(
                135deg,
                rgba(139, 92, 246, 0.1) 0%,
                rgba(66, 133, 244, 0.1) 50%,
                rgba(16, 185, 129, 0.1) 100%
            )
        `;
        this.canvas.style.animation = 'aurora-fallback 10s ease-in-out infinite';

        const style = document.createElement('style');
        style.textContent = `
            @keyframes aurora-fallback {
                0%, 100% { opacity: 0.3; }
                50% { opacity: 0.6; }
            }
        `;
        document.head.appendChild(style);
    }

    destroy() {
        if (this.canvas) this.canvas.remove();
    }
}

// Auto-initialize
const auroraShader = new AuroraShaderEngine();
window.auroraShader = auroraShader;

export { AuroraShaderEngine };
export default auroraShader;
