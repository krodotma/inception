/**
 * RheoMode Visual Metaphor
 * 
 * Priority 2 from Architect Review: Progressive disclosure with semantic zoom.
 * Replace CLI flags with interactive level switcher.
 */

// =============================================================================
// RHEOMODE LEVEL DEFINITIONS
// =============================================================================

export interface RheoModeLevel {
    level: number;
    name: string;
    description: string;
    icon: string;
    visibleTypes: string[];
}

export const RHEO_LEVELS: RheoModeLevel[] = [
    {
        level: 0,
        name: 'Gist',
        description: 'One-line summary',
        icon: 'summarize',
        visibleTypes: ['summary'],
    },
    {
        level: 1,
        name: 'Takeaways',
        description: 'Key points & action items',
        icon: 'checklist',
        visibleTypes: ['summary', 'takeaway'],
    },
    {
        level: 2,
        name: 'Evidence',
        description: 'Claims linked to sources',
        icon: 'link',
        visibleTypes: ['summary', 'takeaway', 'claim', 'source'],
    },
    {
        level: 3,
        name: 'Full',
        description: 'Complete deconstruction',
        icon: 'account_tree',
        visibleTypes: ['summary', 'takeaway', 'claim', 'source', 'entity', 'relation'],
    },
    {
        level: 4,
        name: 'Skills',
        description: 'Executable actions',
        icon: 'play_arrow',
        visibleTypes: ['summary', 'takeaway', 'claim', 'source', 'entity', 'relation', 'procedure', 'skill'],
    },
];

// =============================================================================
// MOTION TOKENS
// =============================================================================

const MOTION = {
    duration: {
        short: 150,
        medium: 300,
        long: 500,
    },
    easing: {
        emphasized: 'cubic-bezier(0.2, 0, 0, 1)',
        decelerate: 'cubic-bezier(0.05, 0.7, 0.1, 1)',
    },
};

// =============================================================================
// RHEOMODE SWITCHER COMPONENT
// =============================================================================

export class RheoModeSwitcher {
    private container: HTMLElement;
    private currentLevel: number = 2;
    private onChange?: (level: number) => void;

    constructor(container: HTMLElement, onChange?: (level: number) => void) {
        this.container = container;
        this.onChange = onChange;
        this.render();
    }

    private render(): void {
        this.container.innerHTML = `
      <div class="rheomode-switcher" role="radiogroup" aria-label="Detail level">
        <div class="rheomode-track">
          <div class="rheomode-fill" style="width: ${(this.currentLevel / 4) * 100}%"></div>
        </div>
        <div class="rheomode-levels">
          ${RHEO_LEVELS.map(level => this.renderLevel(level)).join('')}
        </div>
        <div class="rheomode-label">
          <span class="material-symbols-outlined">${RHEO_LEVELS[this.currentLevel].icon}</span>
          <span class="rheomode-label-text">${RHEO_LEVELS[this.currentLevel].name}</span>
          <span class="rheomode-label-desc">${RHEO_LEVELS[this.currentLevel].description}</span>
        </div>
      </div>
    `;

        // Add event listeners
        this.container.querySelectorAll('.rheomode-dot').forEach((dot, index) => {
            dot.addEventListener('click', () => this.setLevel(index));
        });

        // Keyboard support
        this.container.querySelector('.rheomode-levels')?.addEventListener('keydown', (e) => {
            const key = (e as KeyboardEvent).key;
            if (key === 'ArrowRight' && this.currentLevel < 4) {
                this.setLevel(this.currentLevel + 1);
            } else if (key === 'ArrowLeft' && this.currentLevel > 0) {
                this.setLevel(this.currentLevel - 1);
            }
        });

        this.addStyles();
    }

    private renderLevel(level: RheoModeLevel): string {
        const isActive = level.level === this.currentLevel;
        const isPast = level.level < this.currentLevel;

        return `
      <button 
        class="rheomode-dot ${isActive ? 'active' : ''} ${isPast ? 'past' : ''}"
        role="radio"
        aria-checked="${isActive}"
        aria-label="${level.name}: ${level.description}"
        data-level="${level.level}"
        tabindex="${isActive ? 0 : -1}"
      >
        <span class="rheomode-dot-inner"></span>
        <span class="rheomode-dot-label">${level.level}</span>
      </button>
    `;
    }

    public setLevel(level: number): void {
        if (level < 0 || level > 4) return;

        const previousLevel = this.currentLevel;
        this.currentLevel = level;

        // Animate transition
        const fill = this.container.querySelector('.rheomode-fill') as HTMLElement;
        if (fill) {
            fill.style.transition = `width ${MOTION.duration.medium}ms ${MOTION.easing.decelerate}`;
            fill.style.width = `${(level / 4) * 100}%`;
        }

        // Update dots
        this.container.querySelectorAll('.rheomode-dot').forEach((dot, index) => {
            dot.classList.toggle('active', index === level);
            dot.classList.toggle('past', index < level);
            dot.setAttribute('aria-checked', String(index === level));
            dot.setAttribute('tabindex', index === level ? '0' : '-1');
        });

        // Update label with animation
        const label = this.container.querySelector('.rheomode-label') as HTMLElement;
        if (label) {
            const direction = level > previousLevel ? 1 : -1;
            label.style.transform = `translateY(${direction * 10}px)`;
            label.style.opacity = '0';

            setTimeout(() => {
                label.querySelector('.material-symbols-outlined')!.textContent = RHEO_LEVELS[level].icon;
                label.querySelector('.rheomode-label-text')!.textContent = RHEO_LEVELS[level].name;
                label.querySelector('.rheomode-label-desc')!.textContent = RHEO_LEVELS[level].description;

                label.style.transition = `all ${MOTION.duration.medium}ms ${MOTION.easing.decelerate}`;
                label.style.transform = 'translateY(0)';
                label.style.opacity = '1';
            }, MOTION.duration.short);
        }

        // Notify callback
        if (this.onChange) {
            this.onChange(level);
        }
    }

    public getLevel(): number {
        return this.currentLevel;
    }

    private addStyles(): void {
        if (document.getElementById('rheomode-styles')) return;

        const style = document.createElement('style');
        style.id = 'rheomode-styles';
        style.textContent = `
      .rheomode-switcher {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: var(--md-sys-spacing-md, 16px);
        gap: var(--md-sys-spacing-sm, 8px);
        background: var(--md-sys-color-surface-container);
        border-radius: var(--md-sys-shape-corner-large, 16px);
        min-width: 280px;
      }
      
      .rheomode-track {
        width: 100%;
        height: 4px;
        background: var(--md-sys-color-surface-variant);
        border-radius: 2px;
        overflow: hidden;
      }
      
      .rheomode-fill {
        height: 100%;
        background: linear-gradient(
          90deg,
          var(--md-sys-color-primary) 0%,
          var(--md-sys-color-tertiary) 100%
        );
        border-radius: 2px;
      }
      
      .rheomode-levels {
        display: flex;
        justify-content: space-between;
        width: 100%;
        padding: 0 8px;
      }
      
      .rheomode-dot {
        position: relative;
        width: 32px;
        height: 32px;
        border: none;
        background: transparent;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform ${MOTION.duration.short}ms ${MOTION.easing.emphasized};
      }
      
      .rheomode-dot:hover {
        transform: scale(1.1);
      }
      
      .rheomode-dot:focus-visible {
        outline: 2px solid var(--md-sys-color-primary);
        outline-offset: 2px;
        border-radius: 50%;
      }
      
      .rheomode-dot-inner {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: var(--md-sys-color-surface-variant);
        border: 2px solid var(--md-sys-color-outline);
        transition: all ${MOTION.duration.medium}ms ${MOTION.easing.decelerate};
      }
      
      .rheomode-dot.past .rheomode-dot-inner,
      .rheomode-dot.active .rheomode-dot-inner {
        background: var(--md-sys-color-primary);
        border-color: var(--md-sys-color-primary);
      }
      
      .rheomode-dot.active .rheomode-dot-inner {
        width: 16px;
        height: 16px;
        box-shadow: 0 0 0 4px var(--md-sys-color-primary-container);
      }
      
      .rheomode-dot-label {
        position: absolute;
        bottom: -16px;
        font-size: 10px;
        color: var(--md-sys-color-on-surface-variant);
        opacity: 0.7;
      }
      
      .rheomode-label {
        display: flex;
        align-items: center;
        gap: var(--md-sys-spacing-xs, 4px);
        margin-top: var(--md-sys-spacing-sm, 8px);
        transition: all ${MOTION.duration.short}ms ${MOTION.easing.emphasized};
      }
      
      .rheomode-label .material-symbols-outlined {
        font-size: 20px;
        color: var(--md-sys-color-primary);
      }
      
      .rheomode-label-text {
        font-weight: 500;
        color: var(--md-sys-color-on-surface);
      }
      
      .rheomode-label-desc {
        color: var(--md-sys-color-on-surface-variant);
        font-size: 12px;
      }
      
      /* Reduced motion */
      @media (prefers-reduced-motion: reduce) {
        .rheomode-fill,
        .rheomode-dot,
        .rheomode-dot-inner,
        .rheomode-label {
          transition-duration: 0.01ms !important;
        }
      }
    `;
        document.head.appendChild(style);
    }
}

// =============================================================================
// SEMANTIC ZOOM CAMERA
// =============================================================================

export class SemanticZoomCamera {
    private container: HTMLElement;
    private currentLevel: number = 2;
    private onZoom?: (level: number, direction: 'in' | 'out') => void;

    constructor(
        container: HTMLElement,
        onZoom?: (level: number, direction: 'in' | 'out') => void
    ) {
        this.container = container;
        this.onZoom = onZoom;
        this.setupListeners();
    }

    private setupListeners(): void {
        // Wheel zoom
        this.container.addEventListener('wheel', (e) => {
            if (e.ctrlKey || e.metaKey) {
                e.preventDefault();
                const direction = e.deltaY < 0 ? 'in' : 'out';
                this.zoom(direction);
            }
        }, { passive: false });

        // Pinch zoom (touch)
        let initialDistance = 0;

        this.container.addEventListener('touchstart', (e) => {
            if (e.touches.length === 2) {
                initialDistance = this.getTouchDistance(e.touches);
            }
        });

        this.container.addEventListener('touchmove', (e) => {
            if (e.touches.length === 2) {
                const currentDistance = this.getTouchDistance(e.touches);
                const delta = currentDistance - initialDistance;

                if (Math.abs(delta) > 50) {
                    const direction = delta > 0 ? 'in' : 'out';
                    this.zoom(direction);
                    initialDistance = currentDistance;
                }
            }
        });

        // Keyboard
        this.container.addEventListener('keydown', (e) => {
            if (e.key === '+' || e.key === '=') {
                this.zoom('in');
            } else if (e.key === '-') {
                this.zoom('out');
            }
        });
    }

    private getTouchDistance(touches: TouchList): number {
        const dx = touches[0].clientX - touches[1].clientX;
        const dy = touches[0].clientY - touches[1].clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }

    private zoom(direction: 'in' | 'out'): void {
        const newLevel = direction === 'in'
            ? Math.min(4, this.currentLevel + 1)
            : Math.max(0, this.currentLevel - 1);

        if (newLevel !== this.currentLevel) {
            this.currentLevel = newLevel;
            if (this.onZoom) {
                this.onZoom(newLevel, direction);
            }
        }
    }

    public setLevel(level: number): void {
        this.currentLevel = Math.max(0, Math.min(4, level));
    }

    public getLevel(): number {
        return this.currentLevel;
    }
}

// =============================================================================
// EXPORTS
// =============================================================================

export function initRheoModeSwitcher(
    container: HTMLElement,
    onChange?: (level: number) => void
): RheoModeSwitcher {
    return new RheoModeSwitcher(container, onChange);
}

export function initSemanticZoom(
    container: HTMLElement,
    onZoom?: (level: number, direction: 'in' | 'out') => void
): SemanticZoomCamera {
    return new SemanticZoomCamera(container, onZoom);
}
