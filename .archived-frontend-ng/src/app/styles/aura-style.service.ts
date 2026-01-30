/**
 * AURA Multi-Dimensional Style Generator
 * Generates complete style presets across 28 dimensions
 */

import { Injectable, signal, computed } from '@angular/core';
import type {
    StylePreset,
    StyleMood,
    StyleTokens,
    ColorDimensions,
    MotionDimensions,
    GlassDimensions,
    ElevationDimensions,
    LayoutDimensions,
    TypographyDimensions,
    EffectDimensions,
    GenerationOptions,
    MotionProfile,
} from './style-dimensions';
import { STYLE_PRESETS, PRESET_MAP } from './style-presets';

// ============================================================================
// Constants
// ============================================================================

const DB_NAME = 'aura-styles';
const DB_VERSION = 1;
const STORE_NAME = 'presets';
const PREFS_KEY = 'aura-preferences';
const CACHE_LIMIT = 100;

// ============================================================================
// PRNG - Mulberry32
// ============================================================================

function createRng(seed: number): () => number {
    let t = (Math.floor(seed * 0xffffffff) >>> 0) || 0x6d2b79f5;
    return () => {
        t += 0x6d2b79f5;
        let r = Math.imul(t ^ (t >>> 15), 1 | t);
        r ^= r + Math.imul(r ^ (r >>> 7), 61 | r);
        return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
    };
}

// Scale a 0-1 random value to a range
function scale(rng: () => number, min: number, max: number): number {
    return min + rng() * (max - min);
}

// Weighted choice from array
function choose<T>(rng: () => number, options: readonly T[]): T {
    return options[Math.floor(rng() * options.length)];
}

// ============================================================================
// Angular Service
// ============================================================================

@Injectable({ providedIn: 'root' })
export class AuraStyleService {

    // Reactive state
    readonly currentPreset = signal<StylePreset | null>(null);
    readonly cachedPresets = signal<StylePreset[]>([]);
    readonly isLoading = signal(false);

    // Computed
    readonly presetName = computed(() => this.currentPreset()?.name ?? 'Default');
    readonly presetMood = computed(() => this.currentPreset()?.mood ?? 'minimal');

    private dbPromise: Promise<IDBDatabase> | null = null;

    constructor() {
        this.initialize();
    }

    private async initialize(): Promise<void> {
        await this.refreshCache();
        await this.loadPreferredOrRandom();
    }

    // ==========================================================================
    // Generation Engine
    // ==========================================================================

    generate(options: GenerationOptions = {}): StylePreset {
        const seed = options.seed ?? Math.random();
        const rng = createRng(seed);

        // If mood specified, start from that preset and vary
        const baseMood = options.mood ?? choose(rng, ['ethereal', 'brutalist', 'organic', 'techno', 'minimal', 'maximal'] as StyleMood[]);
        const basePreset = options.basePreset ?? PRESET_MAP[baseMood];

        // Generate all dimensions
        const color = this.generateColorDimensions(rng, basePreset?.color);
        const motion = this.generateMotionDimensions(rng, options.motionProfile, basePreset?.motion);
        const glass = this.generateGlassDimensions(rng, baseMood, basePreset?.glass);
        const elevation = this.generateElevationDimensions(rng, basePreset?.elevation);
        const layout = this.generateLayoutDimensions(rng, baseMood, basePreset?.layout);
        const typography = this.generateTypographyDimensions(rng, basePreset?.typography);
        const effects = this.generateEffectDimensions(rng, baseMood, basePreset?.effects);

        return {
            id: crypto.randomUUID?.() ?? this.fallbackUUID(),
            name: this.generateName(rng, baseMood),
            mood: this.inferMood(color, motion, layout),
            seed,
            color,
            motion,
            glass,
            elevation,
            layout,
            typography,
            effects,
            createdAt: new Date().toISOString(),
            generatedBy: 'algorithm',
            isFavorite: false,
            usageCount: 0,
        };
    }

    // ==========================================================================
    // Dimension Generators
    // ==========================================================================

    private generateColorDimensions(rng: () => number, base?: ColorDimensions): ColorDimensions {
        // Anchor hues that produce pleasing palettes
        const anchors = [200, 220, 250, 280, 320, 20, 40, 90, 140, 170, 180, 260, 300];
        const anchor = choose(rng, anchors);
        const hueVariation = scale(rng, -15, 15);

        return {
            primaryHue: base?.primaryHue ?? ((anchor + hueVariation + 360) % 360),
            chromaIntensity: base?.chromaIntensity ?? scale(rng, 0.2, 1.0),
            backgroundLightness: base?.backgroundLightness ?? scale(rng, 0.04, 0.15),
            contrastRatio: base?.contrastRatio ?? scale(rng, 0.5, 1.0),
            glowStrength: base?.glowStrength ?? scale(rng, 0, 1.0),
            glowSpread: base?.glowSpread ?? scale(rng, 0.3, 0.9),
            gradientAngle: base?.gradientAngle ?? scale(rng, 0, 360),
            gradientComplexity: base?.gradientComplexity ?? Math.floor(scale(rng, 2, 5)),
        };
    }

    private generateMotionDimensions(
        rng: () => number,
        profileHint?: MotionProfile,
        base?: MotionDimensions
    ): MotionDimensions {
        const profiles: MotionProfile[] = ['snappy', 'smooth', 'bouncy', 'theatrical', 'zen'];
        const profile = profileHint ?? base?.profile ?? choose(rng, profiles);

        // Profile-specific ranges
        const profileSettings: Record<MotionProfile, { stiffness: [number, number]; damping: [number, number]; duration: [number, number] }> = {
            snappy: { stiffness: [300, 400], damping: [18, 24], duration: [0.5, 0.7] },
            smooth: { stiffness: [200, 280], damping: [16, 22], duration: [0.8, 1.0] },
            bouncy: { stiffness: [150, 220], damping: [8, 14], duration: [0.9, 1.2] },
            theatrical: { stiffness: [120, 180], damping: [10, 16], duration: [1.2, 1.6] },
            zen: { stiffness: [100, 150], damping: [16, 20], duration: [1.4, 2.0] },
        };

        const settings = profileSettings[profile];

        return {
            springStiffness: base?.springStiffness ?? scale(rng, ...settings.stiffness),
            springDamping: base?.springDamping ?? scale(rng, ...settings.damping),
            durationScale: base?.durationScale ?? scale(rng, ...settings.duration),
            staggerDelay: base?.staggerDelay ?? scale(rng, 5, 50),
            profile,
        };
    }

    private generateGlassDimensions(
        rng: () => number,
        mood: StyleMood,
        base?: GlassDimensions
    ): GlassDimensions {
        const intensities = ['subtle', 'standard', 'heavy', 'opaque'] as const;
        const depthModes = ['flat', 'elevated', 'glass', 'neumorphic'] as const;

        // Mood influences glass style
        const moodGlassIntensity: Record<StyleMood, number> = {
            ethereal: 0.8, brutalist: 0, organic: 0.4, techno: 0.6, minimal: 0.2, maximal: 0.9
        };

        const glassLevel = moodGlassIntensity[mood] ?? 0.5;

        return {
            blurAmount: base?.blurAmount ?? scale(rng, 0, 32) * glassLevel,
            tintOpacity: base?.tintOpacity ?? scale(rng, 0, 0.5) * glassLevel,
            intensity: base?.intensity ?? choose(rng, intensities),
            noiseOpacity: base?.noiseOpacity ?? scale(rng, 0, 0.15),
            depthMode: base?.depthMode ?? choose(rng, depthModes),
        };
    }

    private generateElevationDimensions(rng: () => number, base?: ElevationDimensions): ElevationDimensions {
        return {
            shadowIntensity: base?.shadowIntensity ?? scale(rng, 0, 1),
            shadowBlur: base?.shadowBlur ?? scale(rng, 8, 40),
            shadowSpread: base?.shadowSpread ?? scale(rng, -4, 8),
            shadowOpacity: base?.shadowOpacity ?? scale(rng, 0.05, 0.35),
            levels: base?.levels ?? Math.floor(scale(rng, 3, 6)),
        };
    }

    private generateLayoutDimensions(
        rng: () => number,
        mood: StyleMood,
        base?: LayoutDimensions
    ): LayoutDimensions {
        const cornerModes = ['sharp', 'soft', 'rounded', 'pill'] as const;
        const densities = ['compact', 'default', 'spacious'] as const;

        // Mood influences layout
        const moodRadii: Record<StyleMood, number> = {
            ethereal: 24, brutalist: 0, organic: 16, techno: 4, minimal: 8, maximal: 20
        };

        return {
            cornerRadius: base?.cornerRadius ?? moodRadii[mood] ?? scale(rng, 0, 32),
            cornerMode: base?.cornerMode ?? choose(rng, cornerModes),
            borderWidth: base?.borderWidth ?? Math.floor(scale(rng, 0, 3)),
            spacingBase: base?.spacingBase ?? scale(rng, 4, 12),
            density: base?.density ?? choose(rng, densities),
            asymmetry: base?.asymmetry ?? scale(rng, 0, 0.5),
        };
    }

    private generateTypographyDimensions(rng: () => number, base?: TypographyDimensions): TypographyDimensions {
        // Type scale ratios with names
        const scales = [1.125, 1.15, 1.2, 1.25, 1.333, 1.414];

        return {
            scaleRatio: base?.scaleRatio ?? choose(rng, scales),
            headingWeight: base?.headingWeight ?? Math.floor(scale(rng, 5, 9)) * 100,
            bodyWeight: base?.bodyWeight ?? Math.floor(scale(rng, 3, 5)) * 100,
            letterSpacing: base?.letterSpacing ?? scale(rng, -0.02, 0.05),
            lineHeight: base?.lineHeight ?? scale(rng, 1.3, 1.8),
        };
    }

    private generateEffectDimensions(
        rng: () => number,
        mood: StyleMood,
        base?: EffectDimensions
    ): EffectDimensions {
        const moodParticles: Record<StyleMood, number> = {
            ethereal: 30, brutalist: 0, organic: 15, techno: 50, minimal: 0, maximal: 80
        };

        return {
            particleCount: base?.particleCount ?? moodParticles[mood] ?? scale(rng, 0, 100),
            particleSpeed: base?.particleSpeed ?? scale(rng, 0.2, 1.5),
            hoverScale: base?.hoverScale ?? scale(rng, 1.0, 1.08),
            hoverLift: base?.hoverLift ?? scale(rng, 0, 6),
            focusRingWidth: base?.focusRingWidth ?? scale(rng, 2, 4),
        };
    }

    // ==========================================================================
    // Name Generation
    // ==========================================================================

    private generateName(rng: () => number, mood: StyleMood): string {
        const prefixes: Record<StyleMood, string[]> = {
            ethereal: ['Celestial', 'Dreaming', 'Moonlit', 'Whisper', 'Aurora'],
            brutalist: ['Stark', 'Raw', 'Concrete', 'Edge', 'Forge'],
            organic: ['Terra', 'Moss', 'Amber', 'Bark', 'Stone'],
            techno: ['Neon', 'Circuit', 'Quantum', 'Cyber', 'Pulse'],
            minimal: ['Pure', 'Core', 'Zen', 'Echo', 'Void'],
            maximal: ['Grand', 'Luxe', 'Royal', 'Vivid', 'Blaze'],
        };

        const suffixes = ['Flow', 'Shift', 'Drift', 'Wave', 'Arc', 'Sphere', 'Matrix', 'Spectrum'];

        return `${choose(rng, prefixes[mood])} ${choose(rng, suffixes)}`;
    }

    // ==========================================================================
    // Mood Inference
    // ==========================================================================

    private inferMood(
        color: ColorDimensions,
        motion: MotionDimensions,
        layout: LayoutDimensions
    ): StyleMood {
        // Score each mood based on dimension values
        const scores: Record<StyleMood, number> = {
            ethereal: 0, brutalist: 0, organic: 0, techno: 0, minimal: 0, maximal: 0
        };

        // Color analysis
        if (color.chromaIntensity < 0.4) scores.minimal += 2;
        if (color.chromaIntensity > 0.8) { scores.techno += 2; scores.maximal += 2; }
        if (color.glowStrength > 0.7) { scores.techno += 2; scores.ethereal += 1; }
        if (color.glowStrength < 0.2) scores.brutalist += 2;
        if (color.primaryHue >= 170 && color.primaryHue <= 200) scores.techno += 1;
        if (color.primaryHue >= 20 && color.primaryHue <= 50) scores.organic += 2;

        // Motion analysis - snappy/bouncy/theatrical are motion profiles, not moods
        if (motion.springStiffness > 300) { scores.techno += 1; scores.brutalist += 1; }
        if (motion.springDamping < 14) scores.organic += 2;
        if (motion.durationScale > 1.2) { scores.ethereal += 2; scores.maximal += 1; }

        // Layout analysis
        if (layout.cornerRadius < 4) scores.brutalist += 2;
        if (layout.cornerRadius > 20) { scores.ethereal += 2; scores.maximal += 1; }
        if (layout.density === 'compact') scores.minimal += 1;
        if (layout.density === 'spacious') { scores.ethereal += 1; scores.maximal += 1; }

        // Find highest scoring mood
        let maxMood: StyleMood = 'minimal';
        let maxScore = 0;
        for (const [mood, score] of Object.entries(scores)) {
            if (score > maxScore) {
                maxScore = score;
                maxMood = mood as StyleMood;
            }
        }

        return maxMood;
    }

    // ==========================================================================
    // Token Compilation
    // ==========================================================================

    compileTokens(preset: StylePreset): StyleTokens {
        const { color, motion, glass, elevation, layout, typography, effects } = preset;

        // OKLCH color generation
        const primary = `oklch(65% ${color.chromaIntensity * 0.3} ${color.primaryHue})`;
        const primaryContainer = `oklch(25% ${color.chromaIntensity * 0.15} ${color.primaryHue})`;
        const secondary = `oklch(60% ${color.chromaIntensity * 0.25} ${(color.primaryHue + 30) % 360})`;
        const accent = `oklch(70% ${color.chromaIntensity * 0.35} ${(color.primaryHue + 180) % 360})`;
        const background = `oklch(${color.backgroundLightness * 100}% 0.02 ${color.primaryHue})`;
        const surface = `oklch(${(color.backgroundLightness + 0.05) * 100}% 0.025 ${color.primaryHue})`;
        const surfaceContainer = `oklch(${(color.backgroundLightness + 0.08) * 100}% 0.03 ${color.primaryHue})`;
        const foreground = `oklch(95% 0.01 ${color.primaryHue})`;
        const muted = `oklch(40% 0.02 ${color.primaryHue})`;
        const border = `oklch(25% 0.02 ${color.primaryHue})`;
        const glow = `oklch(75% ${color.chromaIntensity * 0.4} ${color.primaryHue})`;
        const shadow = `oklch(5% 0.01 ${color.primaryHue})`;

        // Motion tokens
        const durationBase = Math.round(300 * motion.durationScale);

        // Spacing scale
        const spaceUnit = layout.spacingBase;

        // Typography scale
        const baseSize = 16;
        const scale = typography.scaleRatio;

        // Elevation shadows
        const shadowColor = `oklch(0% 0 0 / ${elevation.shadowOpacity})`;

        // Gradient
        const gradientPrimary = `linear-gradient(${color.gradientAngle}deg, ${primary}, ${accent})`;

        return {
            // Colors
            '--color-primary': primary,
            '--color-primary-container': primaryContainer,
            '--color-secondary': secondary,
            '--color-accent': accent,
            '--color-background': background,
            '--color-surface': surface,
            '--color-surface-container': surfaceContainer,
            '--color-foreground': foreground,
            '--color-muted': muted,
            '--color-border': border,
            '--color-glow': glow,
            '--color-shadow': shadow,

            // Motion
            '--motion-stiffness': `${Math.round(motion.springStiffness)}`,
            '--motion-damping': `${Math.round(motion.springDamping)}`,
            '--motion-duration-base': `${durationBase}ms`,
            '--motion-duration-fast': `${Math.round(durationBase * 0.5)}ms`,
            '--motion-duration-slow': `${Math.round(durationBase * 1.5)}ms`,
            '--motion-easing': this.getEasingCurve(motion.profile),
            '--motion-easing-bounce': 'cubic-bezier(0.34, 1.56, 0.64, 1)',
            '--motion-stagger': `${Math.round(motion.staggerDelay)}ms`,

            // Glass
            '--glass-blur': `${Math.round(glass.blurAmount)}px`,
            '--glass-tint-opacity': `${glass.tintOpacity.toFixed(2)}`,
            '--glass-border-opacity': `${(glass.tintOpacity * 0.5).toFixed(2)}`,
            '--glass-noise-opacity': `${glass.noiseOpacity.toFixed(3)}`,

            // Elevation
            '--shadow-1': `0 1px ${Math.round(elevation.shadowBlur * 0.25)}px ${shadowColor}`,
            '--shadow-2': `0 2px ${Math.round(elevation.shadowBlur * 0.5)}px ${shadowColor}`,
            '--shadow-3': `0 4px ${Math.round(elevation.shadowBlur * 0.75)}px ${shadowColor}`,
            '--shadow-4': `0 8px ${Math.round(elevation.shadowBlur)}px ${shadowColor}`,
            '--shadow-5': `0 16px ${Math.round(elevation.shadowBlur * 1.5)}px ${shadowColor}`,
            '--shadow-intensity': `${elevation.shadowIntensity.toFixed(2)}`,

            // Layout
            '--radius-sm': `${Math.round(layout.cornerRadius * 0.25)}px`,
            '--radius-md': `${Math.round(layout.cornerRadius * 0.5)}px`,
            '--radius-lg': `${Math.round(layout.cornerRadius)}px`,
            '--radius-xl': `${Math.round(layout.cornerRadius * 1.5)}px`,
            '--radius-full': '9999px',
            '--border-width': `${layout.borderWidth}px`,
            '--space-unit': `${spaceUnit}px`,
            '--space-1': `${spaceUnit}px`,
            '--space-2': `${spaceUnit * 2}px`,
            '--space-3': `${spaceUnit * 3}px`,
            '--space-4': `${spaceUnit * 4}px`,
            '--space-6': `${spaceUnit * 6}px`,
            '--space-8': `${spaceUnit * 8}px`,
            '--space-12': `${spaceUnit * 12}px`,
            '--space-16': `${spaceUnit * 16}px`,

            // Typography
            '--type-scale': `${typography.scaleRatio}`,
            '--font-weight-body': `${typography.bodyWeight}`,
            '--font-weight-heading': `${typography.headingWeight}`,
            '--letter-spacing': `${typography.letterSpacing}em`,
            '--line-height': `${typography.lineHeight}`,
            '--font-size-xs': `${baseSize / scale / scale}px`,
            '--font-size-sm': `${baseSize / scale}px`,
            '--font-size-base': `${baseSize}px`,
            '--font-size-lg': `${baseSize * scale}px`,
            '--font-size-xl': `${baseSize * scale * scale}px`,
            '--font-size-2xl': `${baseSize * scale * scale * scale}px`,
            '--font-size-3xl': `${baseSize * Math.pow(scale, 4)}px`,
            '--font-size-4xl': `${baseSize * Math.pow(scale, 5)}px`,

            // Effects
            '--glow-strength': `${color.glowStrength.toFixed(2)}`,
            '--glow-spread': `${Math.round(color.glowSpread * 30)}px`,
            '--particle-count': `${Math.round(effects.particleCount)}`,
            '--particle-speed': `${effects.particleSpeed.toFixed(1)}`,
            '--hover-scale': `${effects.hoverScale.toFixed(3)}`,
            '--hover-lift': `${effects.hoverLift.toFixed(1)}px`,
            '--focus-ring-width': `${effects.focusRingWidth}px`,
            '--focus-ring-offset': `2px`,

            // Gradients
            '--gradient-primary': gradientPrimary,
            '--gradient-accent': `linear-gradient(${(color.gradientAngle + 90) % 360}deg, ${secondary}, ${accent})`,
            '--gradient-surface': `linear-gradient(180deg, ${surface}, ${surfaceContainer})`,
        };
    }

    private getEasingCurve(profile: MotionProfile): string {
        const curves: Record<MotionProfile, string> = {
            snappy: 'cubic-bezier(0.2, 0, 0, 1)',
            smooth: 'cubic-bezier(0.4, 0, 0.2, 1)',
            bouncy: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
            theatrical: 'cubic-bezier(0.05, 0.7, 0.1, 1)',
            zen: 'cubic-bezier(0.4, 0, 0.6, 1)',
        };
        return curves[profile];
    }

    // ==========================================================================
    // Application
    // ==========================================================================

    apply(preset: StylePreset): void {
        const tokens = this.compileTokens(preset);
        const root = document.documentElement;

        // Apply all tokens
        Object.entries(tokens).forEach(([key, value]) => {
            root.style.setProperty(key, value);
        });

        // Set data attributes for CSS selectors
        root.dataset['auraPreset'] = preset.id;
        root.dataset['auraMood'] = preset.mood;
        root.dataset['auraMotion'] = preset.motion.profile;
        root.dataset['auraDensity'] = preset.layout.density;
        root.dataset['auraDepth'] = preset.glass.depthMode;

        this.currentPreset.set(preset);

        // Dispatch custom event for other components
        window.dispatchEvent(new CustomEvent('aura-style-change', { detail: preset }));
    }

    // ==========================================================================
    // High-Level Actions
    // ==========================================================================

    randomize(options?: GenerationOptions): StylePreset {
        const preset = this.generate(options);
        this.apply(preset);
        this.cachePreset(preset);
        return preset;
    }

    applyPreset(mood: StyleMood): void {
        const preset = PRESET_MAP[mood];
        if (preset) {
            this.apply({ ...preset, id: crypto.randomUUID?.() ?? this.fallbackUUID() });
        }
    }

    async loadPreferredOrRandom(): Promise<StylePreset> {
        this.isLoading.set(true);

        try {
            const prefs = this.getPreferences();

            if (prefs.preferredPresetId) {
                const cached = this.cachedPresets().find(p => p.id === prefs.preferredPresetId);
                if (cached) {
                    this.apply(cached);
                    return cached;
                }
            }

            // Random from cache
            const allCached = this.cachedPresets();
            if (allCached.length > 0) {
                const favorites = allCached.filter(p => p.isFavorite);
                const pool = favorites.length > 0 ? favorites : allCached;
                const random = pool[Math.floor(Math.random() * pool.length)];
                this.apply(random);
                return random;
            }

            // Generate new
            return this.randomize();
        } finally {
            this.isLoading.set(false);
        }
    }

    // ==========================================================================
    // Persistence
    // ==========================================================================

    private async openDB(): Promise<IDBDatabase> {
        if (this.dbPromise) return this.dbPromise;

        this.dbPromise = new Promise((resolve, reject) => {
            const request = indexedDB.open(DB_NAME, DB_VERSION);
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
            request.onupgradeneeded = (event) => {
                const db = (event.target as IDBOpenDBRequest).result;
                if (!db.objectStoreNames.contains(STORE_NAME)) {
                    const store = db.createObjectStore(STORE_NAME, { keyPath: 'id' });
                    store.createIndex('mood', 'mood');
                    store.createIndex('isFavorite', 'isFavorite');
                    store.createIndex('createdAt', 'createdAt');
                }
            };
        });

        return this.dbPromise;
    }

    async cachePreset(preset: StylePreset): Promise<void> {
        try {
            const db = await this.openDB();
            const tx = db.transaction(STORE_NAME, 'readwrite');
            tx.objectStore(STORE_NAME).put(preset);
            await new Promise<void>((res, rej) => {
                tx.oncomplete = () => res();
                tx.onerror = () => rej(tx.error);
            });
            this.refreshCache();
        } catch (e) {
            console.warn('Failed to cache preset:', e);
        }
    }

    async refreshCache(): Promise<void> {
        try {
            const db = await this.openDB();
            const tx = db.transaction(STORE_NAME, 'readonly');
            const request = tx.objectStore(STORE_NAME).getAll();
            const presets = await new Promise<StylePreset[]>((res, rej) => {
                request.onsuccess = () => res(request.result || []);
                request.onerror = () => rej(request.error);
            });
            this.cachedPresets.set(presets);
        } catch {
            this.cachedPresets.set([]);
        }
    }

    async deletePreset(id: string): Promise<void> {
        try {
            const db = await this.openDB();
            const tx = db.transaction(STORE_NAME, 'readwrite');
            tx.objectStore(STORE_NAME).delete(id);
            await new Promise<void>((res, rej) => {
                tx.oncomplete = () => res();
                tx.onerror = () => rej(tx.error);
            });
            this.refreshCache();
        } catch (e) {
            console.warn('Failed to delete preset:', e);
        }
    }

    async toggleFavorite(id: string): Promise<void> {
        const presets = this.cachedPresets();
        const preset = presets.find(p => p.id === id);
        if (preset) {
            preset.isFavorite = !preset.isFavorite;
            await this.cachePreset(preset);
        }
    }

    getPreferences(): { preferredPresetId: string | null } {
        try {
            const stored = localStorage.getItem(PREFS_KEY);
            return stored ? JSON.parse(stored) : { preferredPresetId: null };
        } catch {
            return { preferredPresetId: null };
        }
    }

    setPreferred(presetId: string): void {
        localStorage.setItem(PREFS_KEY, JSON.stringify({ preferredPresetId: presetId }));
    }

    // ==========================================================================
    // Utilities
    // ==========================================================================

    private fallbackUUID(): string {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
            const r = (Math.random() * 16) | 0;
            const v = c === 'x' ? r : (r & 0x3) | 0x8;
            return v.toString(16);
        });
    }

    getSignaturePresets(): StylePreset[] {
        return STYLE_PRESETS;
    }
}
