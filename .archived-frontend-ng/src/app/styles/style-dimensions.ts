/**
 * AURA Style Dimensions
 * 28 dimensions of style variation for multi-dimensional theming
 */

// ============================================================================
// Core Types
// ============================================================================

export type StyleMood =
    | 'ethereal'   // Soft, glass-heavy, muted, slow motion, round
    | 'brutalist'  // Sharp, no-shadow, high-contrast, instant motion
    | 'organic'    // Warm, earthy, rounded, bouncy, textured
    | 'techno'     // Neon, deep glass, sharp, snappy, grid
    | 'minimal'    // Neutral, flat, tight type, fast, clean
    | 'maximal';   // Vibrant, deep shadows, dramatic type, theatrical

export type MotionProfile = 'snappy' | 'smooth' | 'bouncy' | 'theatrical' | 'zen';
export type GlassIntensity = 'subtle' | 'standard' | 'heavy' | 'opaque';
export type LayoutDensity = 'compact' | 'default' | 'spacious';
export type CornerMode = 'sharp' | 'soft' | 'rounded' | 'pill';
export type DepthMode = 'flat' | 'elevated' | 'glass' | 'neumorphic';

// ============================================================================
// Dimension Interfaces
// ============================================================================

export interface ColorDimensions {
    primaryHue: number;           // 0-360
    chromaIntensity: number;      // 0-1 (muted to vivid)
    backgroundLightness: number;  // 0-1 (dark to light)
    contrastRatio: number;        // 0-1 (subtle to dramatic)
    glowStrength: number;         // 0-1
    glowSpread: number;           // 0-1 (focused to diffuse)
    gradientAngle: number;        // 0-360
    gradientComplexity: number;   // 2-5 stops
}

export interface MotionDimensions {
    springStiffness: number;      // 100-400
    springDamping: number;        // 8-24
    durationScale: number;        // 0.5-2.0
    staggerDelay: number;         // 5-50ms
    profile: MotionProfile;
}

export interface GlassDimensions {
    blurAmount: number;           // 0-32px
    tintOpacity: number;          // 0-0.8
    intensity: GlassIntensity;
    noiseOpacity: number;         // 0-0.15
    depthMode: DepthMode;
}

export interface ElevationDimensions {
    shadowIntensity: number;      // 0-1
    shadowBlur: number;           // 0-40px
    shadowSpread: number;         // -4 to 8px
    shadowOpacity: number;        // 0-0.5
    levels: number;               // 3-6
}

export interface LayoutDimensions {
    cornerRadius: number;         // 0-32px base
    cornerMode: CornerMode;
    borderWidth: number;          // 0-3px
    spacingBase: number;          // 4-12px
    density: LayoutDensity;
    asymmetry: number;            // 0-1
}

export interface TypographyDimensions {
    scaleRatio: number;           // 1.125-1.414
    headingWeight: number;        // 500-900
    bodyWeight: number;           // 300-500
    letterSpacing: number;        // -0.02 to 0.05em
    lineHeight: number;           // 1.2-1.8
}

export interface EffectDimensions {
    particleCount: number;        // 0-100
    particleSpeed: number;        // 0-2
    hoverScale: number;           // 1.0-1.08
    hoverLift: number;            // 0-6px
    focusRingWidth: number;       // 2-4px
}

// ============================================================================
// Complete Style Preset
// ============================================================================

export interface StylePreset {
    id: string;
    name: string;
    mood: StyleMood;
    seed: number;

    // All 28 dimensions organized by category
    color: ColorDimensions;
    motion: MotionDimensions;
    glass: GlassDimensions;
    elevation: ElevationDimensions;
    layout: LayoutDimensions;
    typography: TypographyDimensions;
    effects: EffectDimensions;

    // Metadata
    createdAt: string;
    generatedBy: 'algorithm' | 'ai' | 'preset' | 'user';
    isFavorite: boolean;
    usageCount: number;
}

// ============================================================================
// CSS Token Output
// ============================================================================

export interface StyleTokens {
    // Color tokens (OKLCH)
    '--color-primary': string;
    '--color-primary-container': string;
    '--color-secondary': string;
    '--color-accent': string;
    '--color-background': string;
    '--color-surface': string;
    '--color-surface-container': string;
    '--color-foreground': string;
    '--color-muted': string;
    '--color-border': string;
    '--color-glow': string;
    '--color-shadow': string;

    // Motion tokens
    '--motion-stiffness': string;
    '--motion-damping': string;
    '--motion-duration-base': string;
    '--motion-duration-fast': string;
    '--motion-duration-slow': string;
    '--motion-easing': string;
    '--motion-easing-bounce': string;
    '--motion-stagger': string;

    // Glass tokens
    '--glass-blur': string;
    '--glass-tint-opacity': string;
    '--glass-border-opacity': string;
    '--glass-noise-opacity': string;

    // Elevation tokens
    '--shadow-1': string;
    '--shadow-2': string;
    '--shadow-3': string;
    '--shadow-4': string;
    '--shadow-5': string;
    '--shadow-intensity': string;

    // Layout tokens
    '--radius-sm': string;
    '--radius-md': string;
    '--radius-lg': string;
    '--radius-xl': string;
    '--radius-full': string;
    '--border-width': string;
    '--space-unit': string;
    '--space-1': string;
    '--space-2': string;
    '--space-3': string;
    '--space-4': string;
    '--space-6': string;
    '--space-8': string;
    '--space-12': string;
    '--space-16': string;

    // Typography tokens
    '--type-scale': string;
    '--font-weight-body': string;
    '--font-weight-heading': string;
    '--letter-spacing': string;
    '--line-height': string;
    '--font-size-xs': string;
    '--font-size-sm': string;
    '--font-size-base': string;
    '--font-size-lg': string;
    '--font-size-xl': string;
    '--font-size-2xl': string;
    '--font-size-3xl': string;
    '--font-size-4xl': string;

    // Effect tokens
    '--glow-strength': string;
    '--glow-spread': string;
    '--particle-count': string;
    '--particle-speed': string;
    '--hover-scale': string;
    '--hover-lift': string;
    '--focus-ring-width': string;
    '--focus-ring-offset': string;

    // Gradient tokens
    '--gradient-primary': string;
    '--gradient-accent': string;
    '--gradient-surface': string;
}

// ============================================================================
// Preset Constraints (for locked dimensions)
// ============================================================================

export interface StyleConstraints {
    lockColor?: boolean;
    lockMotion?: boolean;
    lockGlass?: boolean;
    lockLayout?: boolean;
    lockTypography?: boolean;
    lockEffects?: boolean;

    // Individual dimension locks
    lockedDimensions?: Array<keyof StylePreset>;
}

// ============================================================================
// Generation Options
// ============================================================================

export interface GenerationOptions {
    seed?: number;
    mood?: StyleMood;
    motionProfile?: MotionProfile;
    constraints?: StyleConstraints;
    basePreset?: Partial<StylePreset>;
}
