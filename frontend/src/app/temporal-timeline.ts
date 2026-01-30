/**
 * Temporal Timeline Component
 * 
 * Priority 3 from Architect Review: "What did I know at time X?"
 * Interactive timeline with validity windows and playback.
 */

// =============================================================================
// TYPES
// =============================================================================

export interface TimelineEvent {
    id: string;
    label: string;
    startTime: Date;
    endTime?: Date;  // null = ongoing
    type: 'entity' | 'claim' | 'source' | 'gap';
    confidence: number;
    metadata?: Record<string, any>;
}

export interface TimelineConfig {
    minDate?: Date;
    maxDate?: Date;
    showMarkers?: boolean;
    playbackSpeed?: number;  // ms per day
}

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
        accelerate: 'cubic-bezier(0.3, 0, 0.8, 0.15)',
    },
};

// =============================================================================
// TEMPORAL TIMELINE
// =============================================================================

export class TemporalTimeline {
    private container: HTMLElement;
    private canvas: HTMLCanvasElement;
    private ctx: CanvasRenderingContext2D;

    private events: TimelineEvent[] = [];
    private config: TimelineConfig;

    // Viewport
    private viewStart: Date;
    private viewEnd: Date;
    private scrubberPosition: number = 0;  // 0-1

    // State
    private isPlaying: boolean = false;
    private playbackInterval: number | null = null;
    private isDragging: boolean = false;
    private hoveredEvent: TimelineEvent | null = null;

    // Callbacks
    onTimeChange?: (date: Date) => void;
    onEventHover?: (event: TimelineEvent | null) => void;
    onEventClick?: (event: TimelineEvent) => void;

    // Dimensions
    private width: number = 0;
    private height: number = 0;
    private trackHeight: number = 24;
    private scrubberWidth: number = 4;

    constructor(container: HTMLElement, config: TimelineConfig = {}) {
        this.container = container;
        this.config = {
            showMarkers: true,
            playbackSpeed: 50,
            ...config,
        };

        const now = new Date();
        this.viewStart = config.minDate || new Date(now.getFullYear() - 5, 0, 1);
        this.viewEnd = config.maxDate || now;

        // Create canvas
        this.canvas = document.createElement('canvas');
        this.canvas.className = 'temporal-timeline-canvas';
        this.container.appendChild(this.canvas);

        this.ctx = this.canvas.getContext('2d')!;

        // Create controls
        this.createControls();

        // Setup
        this.resize();
        this.setupListeners();
        this.render();

        // Resize observer
        const observer = new ResizeObserver(() => this.resize());
        observer.observe(container);
    }

    private createControls(): void {
        const controls = document.createElement('div');
        controls.className = 'temporal-timeline-controls';
        controls.innerHTML = `
      <button class="timeline-btn" data-action="play" aria-label="Play/Pause">
        <span class="material-symbols-outlined">play_arrow</span>
      </button>
      <button class="timeline-btn" data-action="reset" aria-label="Go to start">
        <span class="material-symbols-outlined">skip_previous</span>
      </button>
      <div class="timeline-date-display">
        <span class="timeline-current-date"></span>
      </div>
      <button class="timeline-btn" data-action="today" aria-label="Go to today">
        <span class="material-symbols-outlined">today</span>
      </button>
    `;

        this.container.appendChild(controls);

        // Event listeners
        controls.querySelector('[data-action="play"]')?.addEventListener('click', () => this.togglePlayback());
        controls.querySelector('[data-action="reset"]')?.addEventListener('click', () => this.goToStart());
        controls.querySelector('[data-action="today"]')?.addEventListener('click', () => this.goToToday());

        this.addStyles();
    }

    // ---------------------------------------------------------------------------
    // DATA
    // ---------------------------------------------------------------------------

    public setEvents(events: TimelineEvent[]): void {
        this.events = events.sort((a, b) => a.startTime.getTime() - b.startTime.getTime());

        // Auto-adjust view range
        if (events.length > 0) {
            const minTime = Math.min(...events.map(e => e.startTime.getTime()));
            const maxTime = Math.max(...events.map(e => (e.endTime || new Date()).getTime()));

            this.viewStart = new Date(minTime - (maxTime - minTime) * 0.1);
            this.viewEnd = new Date(maxTime + (maxTime - minTime) * 0.1);
        }

        this.render();
    }

    public async loadFromAPI(endpoint: string): Promise<void> {
        try {
            const response = await fetch(endpoint);
            const data = await response.json();

            const events: TimelineEvent[] = [];

            // Transform entities
            if (data.entities) {
                for (const entity of data.entities) {
                    if (entity.first_seen) {
                        events.push({
                            id: entity.id,
                            label: entity.name,
                            startTime: new Date(entity.first_seen),
                            endTime: entity.last_seen ? new Date(entity.last_seen) : undefined,
                            type: 'entity',
                            confidence: entity.confidence || 0.8,
                        });
                    }
                }
            }

            // Transform claims with validity windows
            if (data.claims) {
                for (const claim of data.claims) {
                    if (claim.valid_from) {
                        events.push({
                            id: claim.id,
                            label: claim.text?.slice(0, 30) || claim.subject,
                            startTime: new Date(claim.valid_from),
                            endTime: claim.valid_until ? new Date(claim.valid_until) : undefined,
                            type: 'claim',
                            confidence: claim.confidence?.epistemic || 0.7,
                        });
                    }
                }
            }

            this.setEvents(events);
        } catch (error) {
            console.error('Failed to load timeline data:', error);
        }
    }

    // ---------------------------------------------------------------------------
    // RENDERING
    // ---------------------------------------------------------------------------

    private resize(): void {
        const rect = this.container.getBoundingClientRect();
        this.width = rect.width;
        this.height = Math.max(120, rect.height);

        this.canvas.width = this.width * window.devicePixelRatio;
        this.canvas.height = this.height * window.devicePixelRatio;
        this.canvas.style.width = `${this.width}px`;
        this.canvas.style.height = `${this.height}px`;

        this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

        this.render();
    }

    private render(): void {
        this.ctx.clearRect(0, 0, this.width, this.height);

        // Background
        this.ctx.fillStyle = 'var(--md-sys-color-surface, #1a1a2e)';
        this.ctx.fillRect(0, 0, this.width, this.height);

        // Track
        this.renderTrack();

        // Events
        this.renderEvents();

        // Scrubber
        this.renderScrubber();

        // Markers
        if (this.config.showMarkers) {
            this.renderMarkers();
        }

        // Update date display
        this.updateDateDisplay();
    }

    private renderTrack(): void {
        const y = this.height / 2;

        this.ctx.beginPath();
        this.ctx.moveTo(0, y);
        this.ctx.lineTo(this.width, y);
        this.ctx.strokeStyle = 'rgba(148, 163, 184, 0.3)';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
    }

    private renderEvents(): void {
        const y = this.height / 2;
        const range = this.viewEnd.getTime() - this.viewStart.getTime();

        for (const event of this.events) {
            const startX = ((event.startTime.getTime() - this.viewStart.getTime()) / range) * this.width;
            const endX = event.endTime
                ? ((event.endTime.getTime() - this.viewStart.getTime()) / range) * this.width
                : this.width;

            // Skip if out of view
            if (endX < 0 || startX > this.width) continue;

            // Color by type
            const colors = {
                entity: '#8B5CF6',
                claim: '#3B82F6',
                source: '#10B981',
                gap: '#EF4444',
            };

            const color = colors[event.type] || colors.entity;
            const isHovered = this.hoveredEvent?.id === event.id;

            // Validity window
            this.ctx.beginPath();
            this.ctx.roundRect(
                Math.max(0, startX),
                y - this.trackHeight / 2,
                Math.min(endX - startX, this.width - startX),
                this.trackHeight,
                4
            );
            this.ctx.fillStyle = isHovered ? color : `${color}88`;
            this.ctx.fill();

            // Confidence indicator
            const confidenceHeight = this.trackHeight * event.confidence;
            this.ctx.beginPath();
            this.ctx.roundRect(
                Math.max(0, startX),
                y - confidenceHeight / 2,
                Math.min(endX - startX, this.width - startX),
                confidenceHeight,
                4
            );
            this.ctx.fillStyle = color;
            this.ctx.fill();

            // Start marker
            if (startX >= 0 && startX <= this.width) {
                this.ctx.beginPath();
                this.ctx.arc(startX, y, 4, 0, Math.PI * 2);
                this.ctx.fillStyle = 'white';
                this.ctx.fill();
            }
        }
    }

    private renderScrubber(): void {
        const x = this.scrubberPosition * this.width;
        const y = this.height / 2;

        // Line
        this.ctx.beginPath();
        this.ctx.moveTo(x, 20);
        this.ctx.lineTo(x, this.height - 20);
        this.ctx.strokeStyle = 'var(--md-sys-color-primary, #8B5CF6)';
        this.ctx.lineWidth = this.scrubberWidth;
        this.ctx.stroke();

        // Handle
        this.ctx.beginPath();
        this.ctx.arc(x, y, 10, 0, Math.PI * 2);
        this.ctx.fillStyle = 'var(--md-sys-color-primary, #8B5CF6)';
        this.ctx.fill();
        this.ctx.strokeStyle = 'white';
        this.ctx.lineWidth = 2;
        this.ctx.stroke();
    }

    private renderMarkers(): void {
        const range = this.viewEnd.getTime() - this.viewStart.getTime();
        const years = Math.ceil(range / (365.25 * 24 * 60 * 60 * 1000));

        // Determine marker interval
        let interval = 1;  // years
        if (years > 20) interval = 5;
        if (years > 50) interval = 10;
        if (years < 2) interval = 0.25;  // quarters

        const startYear = this.viewStart.getFullYear();
        const endYear = this.viewEnd.getFullYear();

        this.ctx.font = '11px system-ui';
        this.ctx.fillStyle = 'rgba(148, 163, 184, 0.7)';
        this.ctx.textAlign = 'center';

        for (let year = startYear; year <= endYear; year += interval) {
            const date = new Date(year, 0, 1);
            const x = ((date.getTime() - this.viewStart.getTime()) / range) * this.width;

            if (x >= 0 && x <= this.width) {
                // Tick
                this.ctx.beginPath();
                this.ctx.moveTo(x, this.height - 30);
                this.ctx.lineTo(x, this.height - 20);
                this.ctx.strokeStyle = 'rgba(148, 163, 184, 0.5)';
                this.ctx.lineWidth = 1;
                this.ctx.stroke();

                // Label
                this.ctx.fillText(String(year), x, this.height - 8);
            }
        }
    }

    private updateDateDisplay(): void {
        const currentDate = this.getCurrentDate();
        const display = this.container.querySelector('.timeline-current-date');
        if (display) {
            display.textContent = currentDate.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
            });
        }
    }

    // ---------------------------------------------------------------------------
    // INTERACTIONS
    // ---------------------------------------------------------------------------

    private setupListeners(): void {
        // Mouse scrubbing
        this.canvas.addEventListener('mousedown', (e) => {
            this.isDragging = true;
            this.handleScrub(e.offsetX);
        });

        window.addEventListener('mousemove', (e) => {
            if (this.isDragging) {
                const rect = this.canvas.getBoundingClientRect();
                this.handleScrub(e.clientX - rect.left);
            }

            // Hover detection
            this.handleHover(e.offsetX, e.offsetY);
        });

        window.addEventListener('mouseup', () => {
            this.isDragging = false;
        });

        // Touch scrubbing
        this.canvas.addEventListener('touchstart', (e) => {
            this.isDragging = true;
            const touch = e.touches[0];
            const rect = this.canvas.getBoundingClientRect();
            this.handleScrub(touch.clientX - rect.left);
        });

        this.canvas.addEventListener('touchmove', (e) => {
            if (this.isDragging) {
                const touch = e.touches[0];
                const rect = this.canvas.getBoundingClientRect();
                this.handleScrub(touch.clientX - rect.left);
            }
        });

        this.canvas.addEventListener('touchend', () => {
            this.isDragging = false;
        });

        // Click on event
        this.canvas.addEventListener('click', (e) => {
            if (this.hoveredEvent && this.onEventClick) {
                this.onEventClick(this.hoveredEvent);
            }
        });

        // Keyboard
        this.container.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') {
                this.scrubberPosition = Math.max(0, this.scrubberPosition - 0.01);
                this.render();
                this.emitTimeChange();
            } else if (e.key === 'ArrowRight') {
                this.scrubberPosition = Math.min(1, this.scrubberPosition + 0.01);
                this.render();
                this.emitTimeChange();
            } else if (e.key === ' ') {
                e.preventDefault();
                this.togglePlayback();
            }
        });
    }

    private handleScrub(x: number): void {
        this.scrubberPosition = Math.max(0, Math.min(1, x / this.width));
        this.render();
        this.emitTimeChange();
    }

    private handleHover(x: number, y: number): void {
        const range = this.viewEnd.getTime() - this.viewStart.getTime();
        const centerY = this.height / 2;

        let found: TimelineEvent | null = null;

        for (const event of this.events) {
            const startX = ((event.startTime.getTime() - this.viewStart.getTime()) / range) * this.width;
            const endX = event.endTime
                ? ((event.endTime.getTime() - this.viewStart.getTime()) / range) * this.width
                : this.width;

            if (
                x >= startX &&
                x <= endX &&
                y >= centerY - this.trackHeight / 2 &&
                y <= centerY + this.trackHeight / 2
            ) {
                found = event;
                break;
            }
        }

        if (found !== this.hoveredEvent) {
            this.hoveredEvent = found;
            this.canvas.style.cursor = found ? 'pointer' : 'ew-resize';
            this.render();

            if (this.onEventHover) {
                this.onEventHover(found);
            }
        }
    }

    // ---------------------------------------------------------------------------
    // PLAYBACK
    // ---------------------------------------------------------------------------

    private togglePlayback(): void {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }

    public play(): void {
        this.isPlaying = true;
        this.updatePlayButton();

        this.playbackInterval = window.setInterval(() => {
            this.scrubberPosition += 0.005;

            if (this.scrubberPosition >= 1) {
                this.scrubberPosition = 1;
                this.pause();
            }

            this.render();
            this.emitTimeChange();
        }, this.config.playbackSpeed);
    }

    public pause(): void {
        this.isPlaying = false;
        this.updatePlayButton();

        if (this.playbackInterval) {
            clearInterval(this.playbackInterval);
            this.playbackInterval = null;
        }
    }

    private updatePlayButton(): void {
        const btn = this.container.querySelector('[data-action="play"] .material-symbols-outlined');
        if (btn) {
            btn.textContent = this.isPlaying ? 'pause' : 'play_arrow';
        }
    }

    // ---------------------------------------------------------------------------
    // PUBLIC API
    // ---------------------------------------------------------------------------

    public getCurrentDate(): Date {
        const range = this.viewEnd.getTime() - this.viewStart.getTime();
        return new Date(this.viewStart.getTime() + range * this.scrubberPosition);
    }

    public goToDate(date: Date): void {
        const range = this.viewEnd.getTime() - this.viewStart.getTime();
        this.scrubberPosition = (date.getTime() - this.viewStart.getTime()) / range;
        this.scrubberPosition = Math.max(0, Math.min(1, this.scrubberPosition));
        this.render();
        this.emitTimeChange();
    }

    public goToStart(): void {
        this.scrubberPosition = 0;
        this.render();
        this.emitTimeChange();
    }

    public goToToday(): void {
        this.goToDate(new Date());
    }

    public getEventsAtCurrentTime(): TimelineEvent[] {
        const currentTime = this.getCurrentDate().getTime();
        return this.events.filter(e => {
            const start = e.startTime.getTime();
            const end = e.endTime?.getTime() || Date.now();
            return currentTime >= start && currentTime <= end;
        });
    }

    private emitTimeChange(): void {
        if (this.onTimeChange) {
            this.onTimeChange(this.getCurrentDate());
        }
    }

    private addStyles(): void {
        if (document.getElementById('temporal-timeline-styles')) return;

        const style = document.createElement('style');
        style.id = 'temporal-timeline-styles';
        style.textContent = `
      .temporal-timeline-canvas {
        width: 100%;
        display: block;
        border-radius: var(--md-sys-shape-corner-medium, 8px);
      }
      
      .temporal-timeline-controls {
        display: flex;
        align-items: center;
        gap: var(--md-sys-spacing-sm, 8px);
        padding: var(--md-sys-spacing-sm, 8px);
        background: var(--md-sys-color-surface-container);
        border-radius: var(--md-sys-shape-corner-medium, 8px);
        margin-top: var(--md-sys-spacing-xs, 4px);
      }
      
      .timeline-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        border: none;
        border-radius: 50%;
        background: var(--md-sys-color-surface-variant);
        color: var(--md-sys-color-on-surface);
        cursor: pointer;
        transition: background ${MOTION.duration.short}ms ${MOTION.easing.emphasized};
      }
      
      .timeline-btn:hover {
        background: var(--md-sys-color-primary-container);
      }
      
      .timeline-btn:focus-visible {
        outline: 2px solid var(--md-sys-color-primary);
        outline-offset: 2px;
      }
      
      .timeline-date-display {
        flex: 1;
        text-align: center;
        font-weight: 500;
        color: var(--md-sys-color-on-surface);
      }
      
      @media (prefers-reduced-motion: reduce) {
        .timeline-btn {
          transition-duration: 0.01ms !important;
        }
      }
    `;
        document.head.appendChild(style);
    }

    public destroy(): void {
        this.pause();
        this.container.innerHTML = '';
    }
}

// =============================================================================
// EXPORTS
// =============================================================================

export function initTemporalTimeline(
    container: HTMLElement,
    config?: TimelineConfig
): TemporalTimeline {
    return new TemporalTimeline(container, config);
}
