/**
 * AURA Signature Style Presets
 * 6 carefully crafted presets representing distinct design philosophies
 */

import type { StylePreset, StyleMood } from './style-dimensions';

// ============================================================================
// Ethereal - Soft, glass-heavy, muted, slow motion, round
// ============================================================================

export const PRESET_ETHEREAL: StylePreset = {
    id: 'preset-ethereal',
    name: 'Ethereal Dream',
    mood: 'ethereal',
    seed: 0.1618, // Golden ratio fractional

    color: {
        primaryHue: 260,            // Soft purple
        chromaIntensity: 0.35,      // Muted
        backgroundLightness: 0.08,  // Dark
        contrastRatio: 0.5,         // Subtle
        glowStrength: 0.7,          // Strong glow
        glowSpread: 0.8,            // Diffuse
        gradientAngle: 135,
        gradientComplexity: 4,
    },

    motion: {
        springStiffness: 120,       // Soft
        springDamping: 18,          // Smooth
        durationScale: 1.5,         // Slow
        staggerDelay: 40,           // Gentle cascade
        profile: 'zen',
    },

    glass: {
        blurAmount: 24,             // Heavy blur
        tintOpacity: 0.4,           // Visible tint
        intensity: 'heavy',
        noiseOpacity: 0.03,         // Subtle texture
        depthMode: 'glass',
    },

    elevation: {
        shadowIntensity: 0.3,
        shadowBlur: 30,
        shadowSpread: 0,
        shadowOpacity: 0.15,
        levels: 4,
    },

    layout: {
        cornerRadius: 24,           // Very rounded
        cornerMode: 'rounded',
        borderWidth: 1,
        spacingBase: 10,            // Spacious
        density: 'spacious',
        asymmetry: 0.1,
    },

    typography: {
        scaleRatio: 1.25,           // Major third
        headingWeight: 300,         // Light
        bodyWeight: 300,
        letterSpacing: 0.02,        // Airy
        lineHeight: 1.7,
    },

    effects: {
        particleCount: 30,          // Light particles
        particleSpeed: 0.3,         // Slow drift
        hoverScale: 1.02,
        hoverLift: 2,
        focusRingWidth: 2,
    },

    createdAt: new Date().toISOString(),
    generatedBy: 'preset',
    isFavorite: false,
    usageCount: 0,
};

// ============================================================================
// Brutalist - Sharp, no-shadow, high-contrast, instant motion
// ============================================================================

export const PRESET_BRUTALIST: StylePreset = {
    id: 'preset-brutalist',
    name: 'Brutal Edge',
    mood: 'brutalist',
    seed: 0.4142, // sqrt(2) - 1

    color: {
        primaryHue: 0,              // Pure white/black focus
        chromaIntensity: 0.1,       // Almost none
        backgroundLightness: 0.02,  // Near black
        contrastRatio: 1.0,         // Maximum
        glowStrength: 0,            // No glow
        glowSpread: 0,
        gradientAngle: 0,
        gradientComplexity: 2,
    },

    motion: {
        springStiffness: 400,       // Maximum snap
        springDamping: 24,          // No bounce
        durationScale: 0.5,         // Fast
        staggerDelay: 0,            // Instant
        profile: 'snappy',
    },

    glass: {
        blurAmount: 0,              // No glass
        tintOpacity: 0,
        intensity: 'subtle',
        noiseOpacity: 0.08,         // Raw texture
        depthMode: 'flat',
    },

    elevation: {
        shadowIntensity: 0,         // No shadows
        shadowBlur: 0,
        shadowSpread: 0,
        shadowOpacity: 0,
        levels: 3,
    },

    layout: {
        cornerRadius: 0,            // Sharp corners
        cornerMode: 'sharp',
        borderWidth: 2,             // Bold borders
        spacingBase: 8,
        density: 'default',
        asymmetry: 0.3,             // Some chaos
    },

    typography: {
        scaleRatio: 1.414,          // Augmented fourth - dramatic
        headingWeight: 900,         // Black
        bodyWeight: 400,
        letterSpacing: -0.02,       // Tight
        lineHeight: 1.3,            // Compact
    },

    effects: {
        particleCount: 0,           // No effects
        particleSpeed: 0,
        hoverScale: 1.0,            // No scale
        hoverLift: 0,
        focusRingWidth: 3,          // Bold focus
    },

    createdAt: new Date().toISOString(),
    generatedBy: 'preset',
    isFavorite: false,
    usageCount: 0,
};

// ============================================================================
// Organic - Warm, earthy, rounded, bouncy, textured
// ============================================================================

export const PRESET_ORGANIC: StylePreset = {
    id: 'preset-organic',
    name: 'Living Earth',
    mood: 'organic',
    seed: 0.3183, // 1/pi

    color: {
        primaryHue: 35,             // Warm amber
        chromaIntensity: 0.55,      // Natural saturation
        backgroundLightness: 0.12,  // Warm dark
        contrastRatio: 0.6,
        glowStrength: 0.4,
        glowSpread: 0.6,
        gradientAngle: 160,
        gradientComplexity: 3,
    },

    motion: {
        springStiffness: 180,
        springDamping: 12,          // Bouncy!
        durationScale: 1.0,
        staggerDelay: 25,
        profile: 'bouncy',
    },

    glass: {
        blurAmount: 12,
        tintOpacity: 0.25,
        intensity: 'standard',
        noiseOpacity: 0.1,          // Paper texture
        depthMode: 'elevated',
    },

    elevation: {
        shadowIntensity: 0.5,
        shadowBlur: 20,
        shadowSpread: -2,
        shadowOpacity: 0.2,
        levels: 5,
    },

    layout: {
        cornerRadius: 16,
        cornerMode: 'soft',
        borderWidth: 0,             // No borders
        spacingBase: 8,
        density: 'default',
        asymmetry: 0.2,
    },

    typography: {
        scaleRatio: 1.2,            // Minor third
        headingWeight: 600,
        bodyWeight: 400,
        letterSpacing: 0,
        lineHeight: 1.6,
    },

    effects: {
        particleCount: 15,          // Subtle dust
        particleSpeed: 0.5,
        hoverScale: 1.03,
        hoverLift: 3,
        focusRingWidth: 2,
    },

    createdAt: new Date().toISOString(),
    generatedBy: 'preset',
    isFavorite: false,
    usageCount: 0,
};

// ============================================================================
// Techno - Neon, deep glass, sharp, snappy, grid
// ============================================================================

export const PRESET_TECHNO: StylePreset = {
    id: 'preset-techno',
    name: 'Neon Circuit',
    mood: 'techno',
    seed: 0.7071, // 1/sqrt(2)

    color: {
        primaryHue: 180,            // Cyan
        chromaIntensity: 0.95,      // Maximum saturation
        backgroundLightness: 0.04,  // Near black
        contrastRatio: 0.9,         // High
        glowStrength: 1.0,          // Full neon
        glowSpread: 0.5,            // Focused
        gradientAngle: 45,
        gradientComplexity: 3,
    },

    motion: {
        springStiffness: 350,       // Snappy
        springDamping: 20,
        durationScale: 0.7,         // Quick
        staggerDelay: 15,           // Fast cascade
        profile: 'snappy',
    },

    glass: {
        blurAmount: 20,             // Deep glass
        tintOpacity: 0.15,
        intensity: 'standard',
        noiseOpacity: 0.02,
        depthMode: 'glass',
    },

    elevation: {
        shadowIntensity: 0.8,
        shadowBlur: 25,
        shadowSpread: -4,
        shadowOpacity: 0.3,
        levels: 4,
    },

    layout: {
        cornerRadius: 4,            // Technical sharp
        cornerMode: 'sharp',
        borderWidth: 1,
        spacingBase: 8,
        density: 'compact',
        asymmetry: 0,               // Grid aligned
    },

    typography: {
        scaleRatio: 1.125,          // Major second - technical
        headingWeight: 700,
        bodyWeight: 400,
        letterSpacing: 0.05,        // Spaced for tech
        lineHeight: 1.4,
    },

    effects: {
        particleCount: 50,          // Digital rain
        particleSpeed: 1.2,
        hoverScale: 1.04,
        hoverLift: 4,
        focusRingWidth: 2,
    },

    createdAt: new Date().toISOString(),
    generatedBy: 'preset',
    isFavorite: false,
    usageCount: 0,
};

// ============================================================================
// Minimal - Neutral, flat, tight type, fast, clean
// ============================================================================

export const PRESET_MINIMAL: StylePreset = {
    id: 'preset-minimal',
    name: 'Pure Clarity',
    mood: 'minimal',
    seed: 0.5,

    color: {
        primaryHue: 220,            // Cool blue
        chromaIntensity: 0.2,       // Very muted
        backgroundLightness: 0.06,
        contrastRatio: 0.65,
        glowStrength: 0.1,
        glowSpread: 0.3,
        gradientAngle: 180,
        gradientComplexity: 2,
    },

    motion: {
        springStiffness: 280,
        springDamping: 22,
        durationScale: 0.6,         // Fast
        staggerDelay: 10,
        profile: 'smooth',
    },

    glass: {
        blurAmount: 8,
        tintOpacity: 0.1,
        intensity: 'subtle',
        noiseOpacity: 0,            // Clean
        depthMode: 'flat',
    },

    elevation: {
        shadowIntensity: 0.2,
        shadowBlur: 12,
        shadowSpread: 0,
        shadowOpacity: 0.08,
        levels: 3,
    },

    layout: {
        cornerRadius: 8,
        cornerMode: 'soft',
        borderWidth: 1,
        spacingBase: 6,             // Compact
        density: 'compact',
        asymmetry: 0,
    },

    typography: {
        scaleRatio: 1.15,
        headingWeight: 500,
        bodyWeight: 400,
        letterSpacing: 0,
        lineHeight: 1.5,
    },

    effects: {
        particleCount: 0,
        particleSpeed: 0,
        hoverScale: 1.01,
        hoverLift: 1,
        focusRingWidth: 2,
    },

    createdAt: new Date().toISOString(),
    generatedBy: 'preset',
    isFavorite: false,
    usageCount: 0,
};

// ============================================================================
// Maximal - Vibrant, deep shadows, dramatic type, theatrical
// ============================================================================

export const PRESET_MAXIMAL: StylePreset = {
    id: 'preset-maximal',
    name: 'Grand Theater',
    mood: 'maximal',
    seed: 0.8284, // sqrt(2) - 1 + 0.4142

    color: {
        primaryHue: 320,            // Magenta
        chromaIntensity: 0.85,      // Vivid
        backgroundLightness: 0.1,
        contrastRatio: 0.85,
        glowStrength: 0.9,
        glowSpread: 0.7,
        gradientAngle: 225,
        gradientComplexity: 5,      // Complex
    },

    motion: {
        springStiffness: 160,
        springDamping: 10,          // Very bouncy
        durationScale: 1.3,         // Theatrical timing
        staggerDelay: 50,           // Dramatic cascade
        profile: 'theatrical',
    },

    glass: {
        blurAmount: 28,
        tintOpacity: 0.35,
        intensity: 'heavy',
        noiseOpacity: 0.05,
        depthMode: 'glass',
    },

    elevation: {
        shadowIntensity: 1.0,       // Maximum
        shadowBlur: 40,
        shadowSpread: 4,
        shadowOpacity: 0.35,
        levels: 6,
    },

    layout: {
        cornerRadius: 20,
        cornerMode: 'rounded',
        borderWidth: 0,
        spacingBase: 12,            // Generous
        density: 'spacious',
        asymmetry: 0.4,             // Dynamic
    },

    typography: {
        scaleRatio: 1.333,          // Perfect fourth - dramatic
        headingWeight: 800,
        bodyWeight: 400,
        letterSpacing: -0.01,
        lineHeight: 1.4,
    },

    effects: {
        particleCount: 80,          // Rich particles
        particleSpeed: 0.8,
        hoverScale: 1.06,
        hoverLift: 6,
        focusRingWidth: 3,
    },

    createdAt: new Date().toISOString(),
    generatedBy: 'preset',
    isFavorite: false,
    usageCount: 0,
};

// ============================================================================
// Export All Presets
// ============================================================================

export const STYLE_PRESETS: StylePreset[] = [
    PRESET_ETHEREAL,
    PRESET_BRUTALIST,
    PRESET_ORGANIC,
    PRESET_TECHNO,
    PRESET_MINIMAL,
    PRESET_MAXIMAL,
];

export const PRESET_MAP: Record<StyleMood, StylePreset> = {
    ethereal: PRESET_ETHEREAL,
    brutalist: PRESET_BRUTALIST,
    organic: PRESET_ORGANIC,
    techno: PRESET_TECHNO,
    minimal: PRESET_MINIMAL,
    maximal: PRESET_MAXIMAL,
};

export function getPresetByMood(mood: StyleMood): StylePreset {
    return PRESET_MAP[mood];
}

export function getRandomPreset(): StylePreset {
    return STYLE_PRESETS[Math.floor(Math.random() * STYLE_PRESETS.length)];
}
