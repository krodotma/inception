/**
 * AURA Style Panel Component
 * Advanced UI for multi-dimensional style control
 */

import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuraStyleService } from '../styles/aura-style.service';
import { STYLE_PRESETS } from '../styles/style-presets';
import type { StyleMood, StylePreset } from '../styles/style-dimensions';

@Component({
  selector: 'app-aura-panel',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="aura-container">
      <!-- Floating Trigger -->
      <button class="aura-trigger" (click)="togglePanel()" [class.active]="isOpen">
        <span class="trigger-icon">✦</span>
        <span class="trigger-pulse"></span>
      </button>

      <!-- Main Panel -->
      @if (isOpen) {
        <div class="aura-panel" [class.expanded]="isExpanded">
          <!-- Header -->
          <header class="panel-header">
            <div class="header-content">
              <h2>AURA</h2>
              <span class="subtitle">Multi-Dimensional Style</span>
            </div>
            <div class="header-actions">
              <button class="icon-btn" (click)="isExpanded = !isExpanded" title="Toggle expanded">
                {{ isExpanded ? '◀' : '▶' }}
              </button>
              <button class="icon-btn" (click)="isOpen = false" title="Close">✕</button>
            </div>
          </header>

          <!-- Current Style Display -->
          <div class="current-style">
            <div class="style-preview" [style.background]="getPreviewGradient()">
              <span class="preview-glow"></span>
            </div>
            <div class="style-info">
              <span class="style-name">{{ styleService.presetName() }}</span>
              <span class="style-mood" [attr.data-mood]="styleService.presetMood()">
                {{ styleService.presetMood() }}
              </span>
            </div>
          </div>

          <!-- Quick Actions -->
          <div class="quick-actions">
            <button class="action-btn primary" (click)="randomize()">
              <span class="btn-icon">⟳</span>
              <span>Randomize All</span>
            </button>
            <button class="action-btn secondary" (click)="saveFavorite()">
              <span class="btn-icon">★</span>
              <span>Save</span>
            </button>
          </div>

          <!-- Preset Gallery -->
          <section class="section">
            <h3 class="section-title">Signature Presets</h3>
            <div class="preset-grid">
              @for (preset of signaturePresets; track preset.id) {
                <button 
                  class="preset-card"
                  [class.active]="styleService.presetMood() === preset.mood"
                  (click)="applyPreset(preset.mood)"
                >
                  <div class="preset-preview" [style.background]="getPresetGradient(preset)"></div>
                  <span class="preset-name">{{ preset.name }}</span>
                  <span class="preset-mood">{{ preset.mood }}</span>
                </button>
              }
            </div>
          </section>

          <!-- Dimension Controls (Expanded Mode) -->
          @if (isExpanded) {
            <section class="section dimensions">
              <h3 class="section-title">Fine Tune</h3>
              
              <!-- Color Dimensions -->
              <div class="dimension-group">
                <h4 class="group-title">🎨 Color</h4>
                <div class="slider-row">
                  <label>Hue</label>
                  <input type="range" min="0" max="360" [(ngModel)]="dimensions.hue" (change)="updateDimension()">
                  <span class="value">{{ dimensions.hue }}°</span>
                </div>
                <div class="slider-row">
                  <label>Chroma</label>
                  <input type="range" min="0" max="100" [(ngModel)]="dimensions.chroma" (change)="updateDimension()">
                  <span class="value">{{ dimensions.chroma }}%</span>
                </div>
                <div class="slider-row">
                  <label>Glow</label>
                  <input type="range" min="0" max="100" [(ngModel)]="dimensions.glow" (change)="updateDimension()">
                  <span class="value">{{ dimensions.glow }}%</span>
                </div>
              </div>

              <!-- Motion Dimensions -->
              <div class="dimension-group">
                <h4 class="group-title">⚡ Motion</h4>
                <div class="slider-row">
                  <label>Stiffness</label>
                  <input type="range" min="100" max="400" [(ngModel)]="dimensions.stiffness" (change)="updateDimension()">
                  <span class="value">{{ dimensions.stiffness }}</span>
                </div>
                <div class="slider-row">
                  <label>Damping</label>
                  <input type="range" min="8" max="24" [(ngModel)]="dimensions.damping" (change)="updateDimension()">
                  <span class="value">{{ dimensions.damping }}</span>
                </div>
                <div class="slider-row">
                  <label>Duration</label>
                  <input type="range" min="50" max="200" [(ngModel)]="dimensions.duration" (change)="updateDimension()">
                  <span class="value">{{ dimensions.duration / 100 }}x</span>
                </div>
              </div>

              <!-- Glass Dimensions -->
              <div class="dimension-group">
                <h4 class="group-title">🔮 Glass</h4>
                <div class="slider-row">
                  <label>Blur</label>
                  <input type="range" min="0" max="32" [(ngModel)]="dimensions.blur" (change)="updateDimension()">
                  <span class="value">{{ dimensions.blur }}px</span>
                </div>
                <div class="slider-row">
                  <label>Tint</label>
                  <input type="range" min="0" max="80" [(ngModel)]="dimensions.tint" (change)="updateDimension()">
                  <span class="value">{{ dimensions.tint }}%</span>
                </div>
              </div>

              <!-- Layout Dimensions -->
              <div class="dimension-group">
                <h4 class="group-title">📐 Layout</h4>
                <div class="slider-row">
                  <label>Radius</label>
                  <input type="range" min="0" max="32" [(ngModel)]="dimensions.radius" (change)="updateDimension()">
                  <span class="value">{{ dimensions.radius }}px</span>
                </div>
                <div class="slider-row">
                  <label>Spacing</label>
                  <input type="range" min="4" max="12" [(ngModel)]="dimensions.spacing" (change)="updateDimension()">
                  <span class="value">{{ dimensions.spacing }}px</span>
                </div>
              </div>

              <!-- Typography Dimensions -->
              <div class="dimension-group">
                <h4 class="group-title">✏️ Typography</h4>
                <div class="slider-row">
                  <label>Scale</label>
                  <input type="range" min="112" max="141" [(ngModel)]="dimensions.scale" (change)="updateDimension()">
                  <span class="value">{{ (dimensions.scale / 100).toFixed(2) }}</span>
                </div>
                <div class="slider-row">
                  <label>Weight</label>
                  <input type="range" min="300" max="900" step="100" [(ngModel)]="dimensions.weight" (change)="updateDimension()">
                  <span class="value">{{ dimensions.weight }}</span>
                </div>
              </div>

              <!-- Effects Dimensions -->
              <div class="dimension-group">
                <h4 class="group-title">✨ Effects</h4>
                <div class="slider-row">
                  <label>Particles</label>
                  <input type="range" min="0" max="100" [(ngModel)]="dimensions.particles" (change)="updateDimension()">
                  <span class="value">{{ dimensions.particles }}</span>
                </div>
                <div class="slider-row">
                  <label>Hover</label>
                  <input type="range" min="100" max="108" [(ngModel)]="dimensions.hover" (change)="updateDimension()">
                  <span class="value">{{ (dimensions.hover / 100).toFixed(2) }}x</span>
                </div>
              </div>
            </section>
          }

          <!-- Cached Presets -->
          <section class="section">
            <h3 class="section-title">Saved ({{ styleService.cachedPresets().length }})</h3>
            <div class="cached-list">
              @for (preset of styleService.cachedPresets().slice(0, 6); track preset.id) {
                <div 
                  class="cached-item"
                  [class.active]="styleService.currentPreset()?.id === preset.id"
                  (click)="applyCustomPreset(preset)"
                >
                  <div class="cached-preview" [style.background]="getPresetGradient(preset)"></div>
                  <div class="cached-info">
                    <span class="cached-name">{{ preset.name }}</span>
                    <span class="cached-meta">
                      {{ preset.isFavorite ? '★' : '' }}
                      {{ preset.mood }}
                    </span>
                  </div>
                  <button class="delete-btn" (click)="deletePreset($event, preset.id)">×</button>
                </div>
              }
              @if (styleService.cachedPresets().length === 0) {
                <p class="empty-message">No saved presets yet</p>
              }
            </div>
          </section>
        </div>
      }
    </div>
    `,
  styleUrls: ['../styles/aura-panel.css']
})
export class AuraPanelComponent {
  readonly styleService = inject(AuraStyleService);
  readonly signaturePresets = STYLE_PRESETS;

  isOpen = false;
  isExpanded = false;

  // Dimension sliders
  dimensions = {
    hue: 220,
    chroma: 50,
    glow: 50,
    stiffness: 200,
    damping: 16,
    duration: 100,
    blur: 16,
    tint: 25,
    radius: 12,
    spacing: 8,
    scale: 120,
    weight: 600,
    particles: 30,
    hover: 103,
  };

  togglePanel(): void {
    this.isOpen = !this.isOpen;
    if (this.isOpen) {
      this.syncDimensionsFromPreset();
    }
  }

  randomize(): void {
    this.styleService.randomize();
    this.syncDimensionsFromPreset();
  }

  saveFavorite(): void {
    const current = this.styleService.currentPreset();
    if (current) {
      current.isFavorite = true;
      this.styleService.cachePreset(current);
      this.styleService.setPreferred(current.id);
    }
  }

  applyPreset(mood: StyleMood): void {
    this.styleService.applyPreset(mood);
    this.syncDimensionsFromPreset();
  }

  applyCustomPreset(preset: StylePreset): void {
    this.styleService.apply(preset);
    this.syncDimensionsFromPreset();
  }

  deletePreset(event: Event, id: string): void {
    event.stopPropagation();
    this.styleService.deletePreset(id);
  }

  updateDimension(): void {
    // Apply dimension changes directly to CSS variables
    const root = document.documentElement;

    // Colors
    const chromaValue = this.dimensions.chroma / 100 * 0.3;
    root.style.setProperty('--color-primary', 'oklch(65% ' + chromaValue + ' ' + this.dimensions.hue + ')');
    root.style.setProperty('--glow-strength', (this.dimensions.glow / 100).toFixed(2));

    // Motion
    root.style.setProperty('--motion-stiffness', String(this.dimensions.stiffness));
    root.style.setProperty('--motion-damping', String(this.dimensions.damping));
    root.style.setProperty('--motion-duration-base', Math.round(300 * this.dimensions.duration / 100) + 'ms');

    // Glass
    root.style.setProperty('--glass-blur', this.dimensions.blur + 'px');
    root.style.setProperty('--glass-tint-opacity', (this.dimensions.tint / 100).toFixed(2));

    // Layout
    root.style.setProperty('--radius-lg', this.dimensions.radius + 'px');
    root.style.setProperty('--space-unit', this.dimensions.spacing + 'px');

    // Typography
    root.style.setProperty('--type-scale', (this.dimensions.scale / 100).toFixed(2));
    root.style.setProperty('--font-weight-heading', String(this.dimensions.weight));

    // Effects
    root.style.setProperty('--particle-count', String(this.dimensions.particles));
    root.style.setProperty('--hover-scale', (this.dimensions.hover / 100).toFixed(3));
  }

  private syncDimensionsFromPreset(): void {
    const preset = this.styleService.currentPreset();
    if (!preset) return;

    this.dimensions = {
      hue: Math.round(preset.color.primaryHue),
      chroma: Math.round(preset.color.chromaIntensity * 100),
      glow: Math.round(preset.color.glowStrength * 100),
      stiffness: Math.round(preset.motion.springStiffness),
      damping: Math.round(preset.motion.springDamping),
      duration: Math.round(preset.motion.durationScale * 100),
      blur: Math.round(preset.glass.blurAmount),
      tint: Math.round(preset.glass.tintOpacity * 100),
      radius: Math.round(preset.layout.cornerRadius),
      spacing: Math.round(preset.layout.spacingBase),
      scale: Math.round(preset.typography.scaleRatio * 100),
      weight: preset.typography.headingWeight,
      particles: Math.round(preset.effects.particleCount),
      hover: Math.round(preset.effects.hoverScale * 100),
    };
  }

  getPreviewGradient(): string {
    const preset = this.styleService.currentPreset();
    if (!preset) return 'linear-gradient(135deg, #6366f1, #a855f7)';
    const hue = preset.color.primaryHue;
    const angle = preset.color.gradientAngle;
    const hue2 = (hue + 60) % 360;
    return 'linear-gradient(' + angle + 'deg, oklch(65% 0.25 ' + hue + '), oklch(70% 0.3 ' + hue2 + '))';
  }

  getPresetGradient(preset: StylePreset): string {
    const hue = preset.color.primaryHue;
    const hue2 = (hue + 60) % 360;
    return 'linear-gradient(135deg, oklch(65% 0.25 ' + hue + '), oklch(70% 0.3 ' + hue2 + '))';
  }
}
