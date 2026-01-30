/**
 * Generative Theme System - Angular Service
 * 
 * Features:
 * - Algorithmic generation with color harmony
 * - AI-assisted generation with caching  
 * - Random loading from IndexedDB cache
 * - User preference persistence (localStorage)
 * - Motion token support
 */

import { Injectable, signal, computed } from '@angular/core';

// ============================================================================
// Types
// ============================================================================

export type ThemeMood = 'cyber' | 'organic' | 'minimal' | 'vibrant' | 'dark' | 'ethereal';

export interface ThemeTokens {
    [key: string]: string;
}

export interface MotionTokens {
    '--motion-spring-stiffness': string;
    '--motion-spring-damping': string;
    '--motion-duration-base': string;
    '--motion-easing-primary': string;
    '--effect-glow-intensity': string;
    '--effect-blur-amount': string;
}

export interface CachedTheme {
    id: string;
    name: string;
    tokens: ThemeTokens;
    motionTokens?: MotionTokens;
    mood: ThemeMood;
    seed: number;
    generatedBy: 'algorithm' | 'ai' | 'user';
    createdAt: string;
    usageCount: number;
    isFavorite: boolean;
}

export interface ThemePreferences {
    mode: 'light' | 'dark' | 'chroma' | 'cached';
    preferredThemeId: string | null;
    autoRandomize: boolean;
    randomizeInterval: number;
    lastRandomizedAt: number;
}

// ============================================================================
// Constants
// ============================================================================

const DB_NAME = 'inception-themes';
const DB_VERSION = 1;
const STORE_NAME = 'themes';
const PREFS_KEY = 'inception-theme-prefs';
const CACHE_LIMIT = 100;

const DEFAULT_PREFS: ThemePreferences = {
    mode: 'chroma',
    preferredThemeId: null,
    autoRandomize: false,
    randomizeInterval: 60,
    lastRandomizedAt: 0,
};

const THEME_TOKEN_KEYS = [
    '--background', '--foreground', '--card', '--card-foreground',
    '--popover', '--popover-foreground', '--primary', '--primary-foreground',
    '--secondary', '--secondary-foreground', '--muted', '--muted-foreground',
    '--accent', '--accent-foreground', '--destructive', '--destructive-foreground',
    '--border', '--input', '--ring',
] as const;

// ============================================================================
// Angular Service
// ============================================================================

@Injectable({ providedIn: 'root' })
export class ThemeGeneratorService {

    // Signals for reactive state
    readonly currentTheme = signal<CachedTheme | null>(null);
    readonly cachedThemes = signal<CachedTheme[]>([]);
    readonly isLoading = signal(false);

    // Computed
    readonly themeName = computed(() => this.currentTheme()?.name ?? 'Default');
    readonly themeMood = computed(() => this.currentTheme()?.mood ?? 'minimal');

    private dbPromise: Promise<IDBDatabase> | null = null;

    constructor() {
        // Initialize on construction
        this.loadPreferredOrRandom();
    }

    // --------------------------------------------------------------------------
    // Color Generation (HSL-based with color theory)
    // --------------------------------------------------------------------------

    private hsl(hue: number, sat: number, light: number): string {
        const normalizedHue = ((hue % 360) + 360) % 360;
        return `${Math.round(normalizedHue)} ${Math.round(Math.max(0, Math.min(100, sat)))}% ${Math.round(Math.max(0, Math.min(100, light)))}%`;
    }

    private createRng(seed: number): () => number {
        let t = (Math.floor(seed * 0xffffffff) >>> 0) || 0x6d2b79f5;
        return () => {
            t += 0x6d2b79f5;
            let r = Math.imul(t ^ (t >>> 15), 1 | t);
            r ^= r + Math.imul(r ^ (r >>> 7), 61 | r);
            return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
        };
    }

    private generateChromaTokens(seed: number): ThemeTokens {
        const rng = this.createRng(seed);

        // Select anchor hue (avoiding muddy browns/yellows)
        const anchors = [200, 220, 250, 280, 320, 20, 40, 90, 140, 170];
        const anchor = anchors[Math.floor(rng() * anchors.length)];
        const baseHue = ((anchor + (rng() - 0.5) * 14) % 360 + 360) % 360;

        // Generate harmonious secondary (analogous)
        const analogShift = (rng() < 0.5 ? 1 : -1) * (28 + rng() * 18);
        const secondaryHue = (baseHue + analogShift + 360) % 360;

        // Generate accent (complementary-ish)
        let accentHue = (baseHue + 150 + rng() * 45) % 360;

        // Background (dark mode default)
        const bgHue = (baseHue + 210 + rng() * 20) % 360;
        const bgSat = 12 + rng() * 8;
        const bgLight = 10 + rng() * 6;

        // Color variations
        const primarySat = 74 + rng() * 14;
        const primaryLight = 58 + rng() * 8;
        const secondarySat = 62 + rng() * 16;
        const secondaryLight = 56 + rng() * 8;
        const accentSat = 70 + rng() * 18;
        const accentLight = 60 + rng() * 10;

        return {
            '--background': this.hsl(bgHue, bgSat, bgLight),
            '--foreground': this.hsl(bgHue, 18, 96),
            '--card': this.hsl(bgHue, bgSat + 4, bgLight + 4),
            '--card-foreground': this.hsl(bgHue, 16, 96),
            '--popover': this.hsl(bgHue, bgSat + 4, bgLight + 4),
            '--popover-foreground': this.hsl(bgHue, 16, 96),
            '--primary': this.hsl(baseHue, primarySat, primaryLight),
            '--primary-foreground': this.hsl(bgHue, 20, 12),
            '--secondary': this.hsl(secondaryHue, secondarySat, secondaryLight),
            '--secondary-foreground': this.hsl(bgHue, 20, 12),
            '--muted': this.hsl(bgHue, bgSat + 8, bgLight + 10),
            '--muted-foreground': this.hsl(bgHue, 12, 72),
            '--accent': this.hsl(accentHue, accentSat, accentLight),
            '--accent-foreground': this.hsl(bgHue, 18, 12),
            '--destructive': '0 85% 60%',
            '--destructive-foreground': '0 0% 100%',
            '--border': this.hsl(bgHue, bgSat + 6, bgLight + 18),
            '--input': this.hsl(bgHue, bgSat + 6, bgLight + 16),
            '--ring': this.hsl(baseHue, primarySat, primaryLight),
        };
    }

    private generateMotionTokens(seed: number): MotionTokens {
        const rng = this.createRng(seed * 1.5);
        return {
            '--motion-spring-stiffness': `${Math.round(100 + rng() * 200)}`,
            '--motion-spring-damping': `${Math.round(10 + rng() * 20)}`,
            '--motion-duration-base': `${Math.round(200 + rng() * 200)}ms`,
            '--motion-easing-primary': 'cubic-bezier(0.2, 0, 0, 1)',
            '--effect-glow-intensity': `${(0.3 + rng() * 0.5).toFixed(2)}`,
            '--effect-blur-amount': `${Math.round(4 + rng() * 8)}px`,
        };
    }

    // --------------------------------------------------------------------------
    // Theme Generation
    // --------------------------------------------------------------------------

    generate(params: { seed?: number; mood?: ThemeMood } = {}): CachedTheme {
        const seed = params.seed ?? Math.random();
        const tokens = this.generateChromaTokens(seed);
        const motionTokens = this.generateMotionTokens(seed);

        return {
            id: crypto.randomUUID?.() ?? this.fallbackUUID(),
            name: this.generateThemeName(seed),
            tokens,
            motionTokens,
            mood: params.mood ?? this.inferMood(tokens),
            seed,
            generatedBy: 'algorithm',
            createdAt: new Date().toISOString(),
            usageCount: 0,
            isFavorite: false,
        };
    }

    private fallbackUUID(): string {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
            const r = (Math.random() * 16) | 0;
            const v = c === 'x' ? r : (r & 0x3) | 0x8;
            return v.toString(16);
        });
    }

    private generateThemeName(seed: number): string {
        const adjectives = ['Cosmic', 'Neon', 'Velvet', 'Chrome', 'Aurora', 'Obsidian', 'Ember', 'Frost', 'Quantum', 'Nebula'];
        const nouns = ['Dusk', 'Dawn', 'Storm', 'Mist', 'Glow', 'Shadow', 'Dream', 'Edge', 'Flux', 'Pulse'];
        const rng = this.createRng(seed * 2);
        return `${adjectives[Math.floor(rng() * adjectives.length)]} ${nouns[Math.floor(rng() * nouns.length)]}`;
    }

    private inferMood(tokens: ThemeTokens): ThemeMood {
        const primary = tokens['--primary'] || '';
        const hue = parseInt(primary.split(' ')[0], 10) || 0;
        if (hue >= 180 && hue <= 260) return 'cyber';
        if (hue >= 80 && hue <= 160) return 'organic';
        if (hue >= 300 || hue <= 30) return 'vibrant';
        return 'minimal';
    }

    // --------------------------------------------------------------------------
    // AI-Assisted Generation
    // --------------------------------------------------------------------------

    async generateFromPrompt(prompt: string): Promise<CachedTheme> {
        const promptLower = prompt.toLowerCase();

        let mood: ThemeMood = 'vibrant';
        if (promptLower.includes('cyber') || promptLower.includes('tech') || promptLower.includes('neon')) mood = 'cyber';
        if (promptLower.includes('nature') || promptLower.includes('organic') || promptLower.includes('earth')) mood = 'organic';
        if (promptLower.includes('minimal') || promptLower.includes('clean') || promptLower.includes('simple')) mood = 'minimal';
        if (promptLower.includes('dark') || promptLower.includes('night') || promptLower.includes('shadow')) mood = 'dark';
        if (promptLower.includes('ethereal') || promptLower.includes('dream') || promptLower.includes('soft')) mood = 'ethereal';

        const theme = this.generate({ mood });
        theme.generatedBy = 'ai';
        theme.name = `AI: ${theme.name}`;

        await this.cacheTheme(theme);
        return theme;
    }

    // --------------------------------------------------------------------------
    // IndexedDB Cache
    // --------------------------------------------------------------------------

    private async openDB(): Promise<IDBDatabase> {
        if (this.dbPromise) return this.dbPromise;

        this.dbPromise = new Promise((resolve, reject) => {
            if (typeof indexedDB === 'undefined') {
                reject(new Error('IndexedDB not available'));
                return;
            }

            const request = indexedDB.open(DB_NAME, DB_VERSION);
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);

            request.onupgradeneeded = (event) => {
                const db = (event.target as IDBOpenDBRequest).result;
                if (!db.objectStoreNames.contains(STORE_NAME)) {
                    const store = db.createObjectStore(STORE_NAME, { keyPath: 'id' });
                    store.createIndex('createdAt', 'createdAt');
                    store.createIndex('usageCount', 'usageCount');
                    store.createIndex('isFavorite', 'isFavorite');
                }
            };
        });

        return this.dbPromise;
    }

    async cacheTheme(theme: CachedTheme): Promise<void> {
        try {
            const db = await this.openDB();
            const tx = db.transaction(STORE_NAME, 'readwrite');
            tx.objectStore(STORE_NAME).put(theme);
            await new Promise<void>((res, rej) => {
                tx.oncomplete = () => res();
                tx.onerror = () => rej(tx.error);
            });
            this.refreshCache();
        } catch (e) {
            console.warn('Failed to cache theme:', e);
        }
    }

    async refreshCache(): Promise<void> {
        try {
            const db = await this.openDB();
            const tx = db.transaction(STORE_NAME, 'readonly');
            const request = tx.objectStore(STORE_NAME).getAll();
            const themes = await new Promise<CachedTheme[]>((res, rej) => {
                request.onsuccess = () => res(request.result || []);
                request.onerror = () => rej(request.error);
            });
            this.cachedThemes.set(themes);
        } catch {
            this.cachedThemes.set([]);
        }
    }

    async getRandomCached(): Promise<CachedTheme | null> {
        const themes = this.cachedThemes();
        if (themes.length === 0) return null;
        const weighted = themes.flatMap(t => t.isFavorite ? [t, t, t] : [t]);
        return weighted[Math.floor(Math.random() * weighted.length)];
    }

    async deleteTheme(id: string): Promise<void> {
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
            console.warn('Failed to delete theme:', e);
        }
    }

    async toggleFavorite(id: string): Promise<void> {
        const themes = this.cachedThemes();
        const theme = themes.find(t => t.id === id);
        if (theme) {
            theme.isFavorite = !theme.isFavorite;
            await this.cacheTheme(theme);
        }
    }

    // --------------------------------------------------------------------------
    // Preferences
    // --------------------------------------------------------------------------

    getPreferences(): ThemePreferences {
        try {
            const stored = localStorage.getItem(PREFS_KEY);
            return stored ? { ...DEFAULT_PREFS, ...JSON.parse(stored) } : DEFAULT_PREFS;
        } catch {
            return DEFAULT_PREFS;
        }
    }

    savePreferences(prefs: Partial<ThemePreferences>): void {
        try {
            const updated = { ...this.getPreferences(), ...prefs };
            localStorage.setItem(PREFS_KEY, JSON.stringify(updated));
        } catch (e) {
            console.warn('Failed to save preferences:', e);
        }
    }

    setPreferred(themeId: string): void {
        this.savePreferences({ preferredThemeId: themeId, mode: 'cached' });
    }

    // --------------------------------------------------------------------------
    // Application
    // --------------------------------------------------------------------------

    apply(theme: CachedTheme): void {
        const root = document.documentElement;

        // Apply color tokens
        Object.entries(theme.tokens).forEach(([key, value]) => {
            root.style.setProperty(key, value);
        });

        // Apply motion tokens
        if (theme.motionTokens) {
            Object.entries(theme.motionTokens).forEach(([key, value]) => {
                root.style.setProperty(key, value);
            });
        }

        root.dataset['theme'] = 'generative';
        root.dataset['themeMood'] = theme.mood;

        this.currentTheme.set(theme);
    }

    // --------------------------------------------------------------------------
    // High-Level Actions
    // --------------------------------------------------------------------------

    randomize(): CachedTheme {
        const theme = this.generate();
        this.apply(theme);
        this.cacheTheme(theme);
        return theme;
    }

    async loadPreferredOrRandom(): Promise<CachedTheme> {
        this.isLoading.set(true);
        await this.refreshCache();

        const prefs = this.getPreferences();

        // Try preferred
        if (prefs.preferredThemeId) {
            const preferred = this.cachedThemes().find(t => t.id === prefs.preferredThemeId);
            if (preferred) {
                this.apply(preferred);
                this.isLoading.set(false);
                return preferred;
            }
        }

        // Try random from cache
        const cached = await this.getRandomCached();
        if (cached) {
            this.apply(cached);
            this.isLoading.set(false);
            return cached;
        }

        // Generate new
        const theme = this.randomize();
        this.isLoading.set(false);
        return theme;
    }

    async saveCurrentAsFavorite(): Promise<void> {
        const current = this.currentTheme();
        if (!current) return;
        current.isFavorite = true;
        await this.cacheTheme(current);
        this.setPreferred(current.id);
    }
}
