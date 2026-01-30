import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { AuraPanelComponent } from './components/aura-panel.component';
import { AuraStyleService } from './styles/aura-style.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive, AuraPanelComponent],
  template: `
    <div class="app-shell">
      <!-- Navigation Rail -->
      <nav class="nav-rail surface-container elevation-1">
        <div class="nav-logo">
          <span class="logo-icon">🧠</span>
        </div>
        
        <div class="nav-items">
          <a routerLink="/" routerLinkActive="active" [routerLinkActiveOptions]="{exact: true}" 
             class="nav-item" title="Dashboard">
            <span class="nav-icon">📊</span>
            <span class="nav-label">Dashboard</span>
          </a>
          <a routerLink="/explorer" routerLinkActive="active" 
             class="nav-item" title="Explorer">
            <span class="nav-icon">🔍</span>
            <span class="nav-label">Explorer</span>
          </a>
          <a routerLink="/terminal" routerLinkActive="active" 
             class="nav-item" title="Terminal">
            <span class="nav-icon">💻</span>
            <span class="nav-label">Terminal</span>
          </a>
          <a routerLink="/settings" routerLinkActive="active" 
             class="nav-item" title="Settings">
            <span class="nav-icon">⚙️</span>
            <span class="nav-label">Settings</span>
          </a>
        </div>
      </nav>
      
      <!-- Main Content (View Transitions here) -->
      <main class="main-content">
        <router-outlet></router-outlet>
      </main>
      
      <!-- AURA Multi-Dimensional Style Controller -->
      <app-aura-panel />
    </div>
  `,
  styles: [`
    .app-shell {
      display: flex;
      height: 100vh;
      background: var(--md-sys-color-background);
      transition: background var(--motion-duration-base, 300ms) var(--motion-easing, ease);
    }
    
    .nav-rail {
      width: 80px;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 16px 0;
      gap: 8px;
      background: var(--md-sys-color-surface-container);
      transition: background var(--motion-duration-base, 300ms) var(--motion-easing, ease);
    }
    
    .nav-logo {
      width: 56px;
      height: 56px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 16px;
    }
    
    .logo-icon {
      font-size: 32px;
    }
    
    .nav-items {
      display: flex;
      flex-direction: column;
      gap: 8px;
      flex: 1;
    }
    
    .nav-item {
      width: 56px;
      height: 56px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 4px;
      border-radius: var(--md-sys-shape-corner-large);
      text-decoration: none;
      color: var(--md-sys-color-on-surface-variant);
      transition: all var(--md-motion-duration-short-2, 150ms) var(--md-motion-easing-emphasized, ease);
    }
    
    .nav-item:hover {
      background: var(--md-sys-color-surface-container-high);
      color: var(--md-sys-color-on-surface);
    }
    
    .nav-item.active {
      background: var(--md-sys-color-secondary-container);
      color: var(--md-sys-color-on-secondary-container);
    }
    
    .nav-icon {
      font-size: 20px;
    }
    
    .nav-label {
      font: var(--md-sys-typescale-label-small);
    }
    
    .main-content {
      flex: 1;
      overflow: auto;
      view-transition-name: main-content;
      transition: background var(--motion-duration-base, 300ms) var(--motion-easing, ease);
    }
  `]
})
export class AppComponent implements OnInit {
  title = 'Inception';
  private readonly auraService = inject(AuraStyleService);

  ngOnInit(): void {
    // Initialize AURA style system - applies saved or random preset to page
    this.auraService.loadPreferredOrRandom();
  }
}
