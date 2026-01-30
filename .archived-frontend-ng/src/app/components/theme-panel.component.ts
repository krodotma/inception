import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ThemeGeneratorService, type CachedTheme } from '../services/theme-generator.service';

@Component({
    selector: 'app-theme-panel',
    standalone: true,
    imports: [CommonModule, FormsModule],
    template: `
    <div class="theme-panel-container">
      <!-- Trigger Button -->
      <button class="theme-trigger" (click)="isOpen = !isOpen" aria-label="Theme controls">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="5"/>
          <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
        </svg>
      </button>

      <!-- Panel -->
      @if (isOpen) {
        <div class="theme-panel" @slideUp>
          <div class="panel-header">
            <h3>🎨 Theme Generator</h3>
            <button class="close-btn" (click)="isOpen = false">×</button>
          </div>

          <!-- Current Theme -->
          <div class="current-theme">
            <span class="name">{{ themeService.themeName() }}</span>
            <span class="mood" [attr.data-mood]="themeService.themeMood()">
              {{ themeService.themeMood() }}
            </span>
          </div>

          <!-- Actions -->
          <div class="actions">
            <button class="action-btn primary" (click)="randomize()" [disabled]="themeService.isLoading()">
              🎲 Randomize
            </button>
            <button class="action-btn secondary" (click)="saveFavorite()">
              ⭐ Save Favorite
            </button>
          </div>

          <!-- AI Prompt -->
          <div class="prompt-section">
            <input 
              type="text" 
              [(ngModel)]="promptInput" 
              placeholder="Describe theme... (e.g., 'cyberpunk neon')"
              (keydown.enter)="generateFromPrompt()"
            />
            <button class="generate-btn" (click)="generateFromPrompt()" [disabled]="!promptInput">
              ✨
            </button>
          </div>

          <!-- Theme Gallery -->
          <div class="gallery">
            <h4>Saved Themes ({{ themeService.cachedThemes().length }})</h4>
            <div class="theme-list">
              @for (theme of themeService.cachedThemes().slice(0, 8); track theme.id) {
                <div 
                  class="theme-card" 
                  [class.active]="themeService.currentTheme()?.id === theme.id"
                  (click)="applyTheme(theme)"
                >
                  <div 
                    class="preview" 
                    [style.background]="'hsl(' + theme.tokens['--primary'] + ')'"
                    [style.border-color]="'hsl(' + theme.tokens['--accent'] + ')'"
                  ></div>
                  <div class="info">
                    <span class="name">{{ theme.name }}</span>
                    <span class="meta">
                      {{ theme.isFavorite ? '⭐' : '' }}
                      {{ theme.generatedBy === 'ai' ? '🤖' : '🎲' }}
                    </span>
                  </div>
                  <button class="delete-btn" (click)="deleteTheme($event, theme.id)">🗑</button>
                </div>
              }
            </div>
          </div>
        </div>
      }
    </div>
  `,
    styles: [`
    .theme-panel-container {
      position: fixed;
      bottom: 20px;
      right: 20px;
      z-index: 9999;
      font-family: system-ui, -apple-system, sans-serif;
    }

    .theme-trigger {
      width: 48px;
      height: 48px;
      border-radius: 50%;
      background: hsl(var(--primary, 220 90% 56%));
      color: hsl(var(--primary-foreground, 0 0% 100%));
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .theme-trigger:hover {
      transform: scale(1.1);
      box-shadow: 0 6px 20px rgba(0,0,0,0.4);
    }

    .theme-panel {
      position: absolute;
      bottom: 60px;
      right: 0;
      width: 320px;
      max-height: 480px;
      overflow-y: auto;
      background: hsl(var(--card, 220 15% 16%));
      border: 1px solid hsl(var(--border, 220 10% 30%));
      border-radius: 12px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }

    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px;
      border-bottom: 1px solid hsl(var(--border));
    }

    .panel-header h3 {
      margin: 0;
      font-size: 16px;
      color: hsl(var(--foreground, 0 0% 100%));
    }

    .close-btn {
      background: none;
      border: none;
      color: hsl(var(--muted-foreground));
      font-size: 24px;
      cursor: pointer;
      line-height: 1;
    }

    .current-theme {
      padding: 12px 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: hsl(var(--muted, 220 10% 25%));
    }

    .current-theme .name {
      font-weight: 600;
      color: hsl(var(--foreground));
    }

    .current-theme .mood {
      font-size: 11px;
      padding: 2px 8px;
      background: hsl(var(--accent));
      border-radius: 4px;
      color: hsl(var(--accent-foreground));
      text-transform: uppercase;
    }

    .actions {
      display: flex;
      gap: 8px;
      padding: 12px 16px;
    }

    .action-btn {
      flex: 1;
      padding: 10px;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      font-size: 13px;
      font-weight: 500;
      transition: filter 0.2s ease;
    }

    .action-btn.primary {
      background: hsl(var(--primary));
      color: hsl(var(--primary-foreground));
    }

    .action-btn.secondary {
      background: hsl(var(--secondary));
      color: hsl(var(--secondary-foreground));
    }

    .action-btn:hover:not(:disabled) {
      filter: brightness(1.1);
    }

    .action-btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .prompt-section {
      padding: 0 16px 12px;
      display: flex;
      gap: 8px;
    }

    .prompt-section input {
      flex: 1;
      padding: 8px 12px;
      border: 1px solid hsl(var(--border));
      border-radius: 6px;
      background: hsl(var(--input));
      color: hsl(var(--foreground));
      font-size: 13px;
    }

    .prompt-section input::placeholder {
      color: hsl(var(--muted-foreground));
    }

    .generate-btn {
      padding: 8px 12px;
      border: none;
      border-radius: 6px;
      background: hsl(var(--accent));
      cursor: pointer;
      font-size: 16px;
    }

    .gallery {
      padding: 12px 16px;
      border-top: 1px solid hsl(var(--border));
    }

    .gallery h4 {
      margin: 0 0 12px;
      font-size: 12px;
      color: hsl(var(--muted-foreground));
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .theme-list {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .theme-card {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px;
      border-radius: 8px;
      background: hsl(var(--muted) / 0.5);
      cursor: pointer;
      transition: background 0.15s ease;
    }

    .theme-card:hover {
      background: hsl(var(--muted));
    }

    .theme-card.active {
      outline: 2px solid hsl(var(--ring));
      outline-offset: 1px;
    }

    .theme-card .preview {
      width: 28px;
      height: 28px;
      border-radius: 6px;
      border: 2px solid;
      flex-shrink: 0;
    }

    .theme-card .info {
      flex: 1;
      min-width: 0;
    }

    .theme-card .name {
      display: block;
      font-size: 12px;
      font-weight: 500;
      color: hsl(var(--foreground));
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .theme-card .meta {
      font-size: 10px;
      color: hsl(var(--muted-foreground));
    }

    .delete-btn {
      background: none;
      border: none;
      cursor: pointer;
      font-size: 14px;
      opacity: 0.5;
      transition: opacity 0.15s ease;
      padding: 4px;
    }

    .delete-btn:hover {
      opacity: 1;
    }
  `]
})
export class ThemePanelComponent {
    readonly themeService = inject(ThemeGeneratorService);

    isOpen = false;
    promptInput = '';

    randomize(): void {
        this.themeService.randomize();
    }

    saveFavorite(): void {
        this.themeService.saveCurrentAsFavorite();
    }

    applyTheme(theme: CachedTheme): void {
        this.themeService.apply(theme);
    }

    deleteTheme(event: Event, id: string): void {
        event.stopPropagation();
        this.themeService.deleteTheme(id);
    }

    async generateFromPrompt(): Promise<void> {
        if (!this.promptInput.trim()) return;
        const theme = await this.themeService.generateFromPrompt(this.promptInput);
        this.themeService.apply(theme);
        this.promptInput = '';
    }
}
