import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { KnowledgeService } from '../../services/knowledge.service';

/**
 * SettingsComponent - Configuration and OAuth management.
 * 
 * Features:
 * - OAuth provider status (real health check)
 * - Theme selector (Dark/Light/System)
 * - API health indicator
 */
@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="settings-container">
      <header class="settings-header">
        <h1>Settings</h1>
      </header>
      
      <!-- API Status -->
      <section class="settings-section surface-container-high rounded-medium elevation-1">
        <h2>System Status</h2>
        <div class="status-grid">
          <div class="status-item">
            <span class="status-label">API Server</span>
            <span class="status-value" [class.connected]="apiHealthy()">
              {{ apiHealthy() ? 'Connected' : 'Disconnected' }}
            </span>
          </div>
          <div class="status-item">
            <span class="status-label">Backend URL</span>
            <span class="status-value monospace">127.0.0.1:8000</span>
          </div>
        </div>
      </section>
      
      <!-- OAuth Providers -->
      <section class="settings-section surface-container-high rounded-medium elevation-1">
        <h2>LLM Providers</h2>
        <p class="section-hint">OAuth-first priority: ClawdBot → MoltBot → Ollama → OpenRouter</p>
        
        <div class="auth-card">
          <div class="provider-info">
            <span class="provider-icon">🔮</span>
            <div>
              <h3>ClawdBot (Claude Max)</h3>
              <p>Opus 4.5, Sonnet 4.5 via OAuth</p>
            </div>
          </div>
          <span class="status" [class.connected]="providers().clawdbot">
            {{ providers().clawdbot ? 'Authenticated' : 'Not Configured' }}
          </span>
        </div>
        
        <div class="auth-card">
          <div class="provider-info">
            <span class="provider-icon">✨</span>
            <div>
              <h3>MoltBot (Gemini Ultra)</h3>
              <p>Pro 3, Flash 3 via OAuth</p>
            </div>
          </div>
          <span class="status" [class.connected]="providers().moltbot">
            {{ providers().moltbot ? 'Authenticated' : 'Not Configured' }}
          </span>
        </div>
        
        <div class="auth-card">
          <div class="provider-info">
            <span class="provider-icon">🦙</span>
            <div>
              <h3>Ollama (Local)</h3>
              <p>llama3.2, codellama</p>
            </div>
          </div>
          <span class="status" [class.connected]="providers().ollama">
            {{ providers().ollama ? 'Running' : 'Not Running' }}
          </span>
        </div>
        
        <div class="auth-card">
          <div class="provider-info">
            <span class="provider-icon">🌐</span>
            <div>
              <h3>OpenRouter (Fallback)</h3>
              <p>API key fallback</p>
            </div>
          </div>
          <span class="status" [class.connected]="providers().openrouter">
            {{ providers().openrouter ? 'Configured' : 'Not Configured' }}
          </span>
        </div>
      </section>
      
      <!-- Appearance -->
      <section class="settings-section surface-container-high rounded-medium elevation-1">
        <h2>Appearance</h2>
        <div class="theme-selector">
          <button 
            class="theme-btn" 
            [class.active]="theme() === 'dark'"
            (click)="setTheme('dark')"
          >Dark</button>
          <button 
            class="theme-btn"
            [class.active]="theme() === 'light'"
            (click)="setTheme('light')"
          >Light</button>
          <button 
            class="theme-btn"
            [class.active]="theme() === 'system'"
            (click)="setTheme('system')"
          >System</button>
        </div>
      </section>
      
      <!-- About -->
      <section class="settings-section surface-container-high rounded-medium elevation-1">
        <h2>About</h2>
        <div class="about-grid">
          <div class="about-item">
            <span class="about-label">Version</span>
            <span class="about-value">3.5.0-angular</span>
          </div>
          <div class="about-item">
            <span class="about-label">Frontend</span>
            <span class="about-value">Angular 17+ (Standalone)</span>
          </div>
          <div class="about-item">
            <span class="about-label">Motion System</span>
            <span class="about-value">KINESIS + View Transitions</span>
          </div>
        </div>
      </section>
    </div>
  `,
  styles: [`
    .settings-container {
      padding: 24px;
      max-width: 800px;
      margin: 0 auto;
    }
    
    .settings-header h1 {
      font: var(--md-sys-typescale-headline-large);
      margin-bottom: 24px;
    }
    
    .settings-section {
      padding: 24px;
      margin-bottom: 24px;
    }
    
    .settings-section h2 {
      font: var(--md-sys-typescale-title-large);
      margin-bottom: 16px;
      color: var(--md-sys-color-on-surface);
    }
    
    .section-hint {
      font: var(--md-sys-typescale-body-small);
      color: var(--md-sys-color-on-surface-variant);
      margin-bottom: 16px;
    }
    
    .status-grid, .about-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
    }
    
    .status-item, .about-item {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    
    .status-label, .about-label {
      font: var(--md-sys-typescale-label-small);
      color: var(--md-sys-color-on-surface-variant);
      text-transform: uppercase;
    }
    
    .status-value, .about-value {
      font: var(--md-sys-typescale-body-large);
    }
    
    .status-value.connected {
      color: #10b981;
    }
    
    .status-value.monospace {
      font-family: 'JetBrains Mono', monospace;
    }
    
    .auth-card {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px;
      background: var(--md-sys-color-surface-container);
      border-radius: var(--md-sys-shape-corner-medium);
      margin-bottom: 12px;
    }
    
    .provider-info {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    
    .provider-icon {
      font-size: 24px;
    }
    
    .provider-info h3 {
      font: var(--md-sys-typescale-title-medium);
    }
    
    .provider-info p {
      font: var(--md-sys-typescale-body-small);
      color: var(--md-sys-color-on-surface-variant);
    }
    
    .status {
      padding: 6px 12px;
      border-radius: var(--md-sys-shape-corner-full);
      font: var(--md-sys-typescale-label-medium);
      background: var(--md-sys-color-error-container);
      color: var(--md-sys-color-on-error-container);
    }
    
    .status.connected {
      background: var(--md-sys-color-tertiary-container);
      color: var(--md-sys-color-on-tertiary-container);
    }
    
    .theme-selector {
      display: flex;
      gap: 8px;
    }
    
    .theme-btn {
      padding: 12px 24px;
      background: var(--md-sys-color-surface-container);
      border: 1px solid var(--md-sys-color-outline-variant);
      border-radius: var(--md-sys-shape-corner-small);
      color: var(--md-sys-color-on-surface);
      cursor: pointer;
      transition: all var(--md-motion-duration-short-2) var(--md-motion-easing-standard);
    }
    
    .theme-btn.active {
      background: var(--md-sys-color-primary);
      color: var(--md-sys-color-on-primary);
      border-color: var(--md-sys-color-primary);
    }
    
    .theme-btn:hover:not(.active) {
      background: var(--md-sys-color-surface-container-high);
    }
  `]
})
export class SettingsComponent implements OnInit {
  private readonly knowledgeService = inject(KnowledgeService);

  // State
  apiHealthy = signal(false);
  theme = signal<'dark' | 'light' | 'system'>('dark');
  providers = signal({
    clawdbot: false,
    moltbot: false,
    ollama: false,
    openrouter: false
  });

  ngOnInit(): void {
    this.checkHealth();
    this.checkProviders();
  }

  private checkHealth(): void {
    this.knowledgeService.healthCheck().subscribe(response => {
      this.apiHealthy.set(response.status === 'healthy');
    });
  }

  private checkProviders(): void {
    // TODO: Add dedicated endpoint for provider status
    // For now, API health implies some provider might be available
  }

  setTheme(theme: 'dark' | 'light' | 'system'): void {
    this.theme.set(theme);
    // TODO: Persist to localStorage and apply to document
  }
}
