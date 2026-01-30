import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { KnowledgeService, Stats, Entity, LearningStats } from '../../services/knowledge.service';

/**
 * DashboardComponent - Main dashboard view with live data binding.
 * 
 * Displays:
 * - System stats (entities, claims, gaps, sources) from /api/stats
 * - Recent activity derived from entities
 * - Learning engine status from /api/learning/stats
 */
@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="dashboard-container">
      <header class="dashboard-header">
        <h1>Inception Dashboard</h1>
        <p class="subtitle">Knowledge Extraction Intelligence</p>
      </header>
      
      <!-- Stats Grid -->
      <section class="stats-grid">
        <div class="stat-card md-animate-slide-up" style="animation-delay: 0ms">
          <span class="stat-value">{{ stats().entities }}</span>
          <span class="stat-label">Entities</span>
        </div>
        <div class="stat-card md-animate-slide-up" style="animation-delay: 50ms">
          <span class="stat-value">{{ stats().claims }}</span>
          <span class="stat-label">Claims</span>
        </div>
        <div class="stat-card md-animate-slide-up" style="animation-delay: 100ms">
          <span class="stat-value">{{ stats().gaps }}</span>
          <span class="stat-label">Gaps</span>
        </div>
        <div class="stat-card md-animate-slide-up" style="animation-delay: 150ms">
          <span class="stat-value">{{ stats().sources }}</span>
          <span class="stat-label">Sources</span>
        </div>
      </section>
      
      <!-- Content Grid -->
      <section class="content-grid">
        <!-- Recent Activity Card -->
        <div class="activity-card surface-container-high rounded-medium elevation-1">
          <h2>Recent Activity</h2>
          @if (loadingActivity()) {
            <div class="loading-state">
              <span class="loading-dot"></span>
              <span>Fetching activity...</span>
            </div>
          } @else if (recentEntities().length === 0) {
            <p class="empty-state">No entities yet. Start by ingesting a source.</p>
          } @else {
            <ul class="activity-list">
              @for (entity of recentEntities(); track entity.id) {
                <li class="activity-item">
                  <span class="activity-type" [attr.data-type]="entity.type">{{ entity.type }}</span>
                  <span class="activity-name">{{ entity.name }}</span>
                  <span class="activity-confidence">{{ (entity.confidence * 100).toFixed(0) }}%</span>
                </li>
              }
            </ul>
          }
        </div>
        
        <!-- Learning Engine Card -->
        <div class="learning-card surface-container-high rounded-medium elevation-1">
          <h2>Learning Engine</h2>
          @if (loadingLearning()) {
            <div class="loading-state">
              <span class="loading-dot"></span>
              <span>Connecting to learning engine...</span>
            </div>
          } @else if (learningStats() === null) {
            <div class="ready-state">
              <p>DAPO / GRPO / RLVR</p>
              <p class="ready-hint">Learning engine ready. Ingest data to start training.</p>
            </div>
          } @else {
            <div class="learning-metrics">
              <div class="metric">
                <span class="metric-label">Total Steps</span>
                <span class="metric-value">{{ learningStats()?.total_steps || 0 }}</span>
              </div>
              <div class="metric">
                <span class="metric-label">Buffer Size</span>
                <span class="metric-value">{{ learningStats()?.buffer_size || 0 }}</span>
              </div>
              <div class="metric">
                <span class="metric-label">RLVR Rate</span>
                <span class="metric-value">{{ ((learningStats()?.rlvr?.verification_rate || 0) * 100).toFixed(1) }}%</span>
              </div>
            </div>
          }
        </div>
      </section>
      
      <!-- System Health Indicator -->
      <footer class="health-bar">
        <span class="health-dot" [class.healthy]="apiHealthy()"></span>
        <span class="health-text">{{ apiHealthy() ? 'API Connected' : 'API Disconnected' }}</span>
      </footer>
    </div>
  `,
  styles: [`
    .dashboard-container {
      padding: 24px;
      max-width: 1400px;
      margin: 0 auto;
    }
    
    .dashboard-header {
      margin-bottom: 32px;
    }
    
    .dashboard-header h1 {
      font: var(--md-sys-typescale-headline-large);
      color: var(--md-sys-color-on-surface);
      margin-bottom: 8px;
    }
    
    .subtitle {
      font: var(--md-sys-typescale-body-large);
      color: var(--md-sys-color-on-surface-variant);
    }
    
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      margin-bottom: 32px;
    }
    
    .stat-card {
      background: var(--md-sys-color-surface-container-high);
      border-radius: var(--md-sys-shape-corner-medium);
      padding: 24px;
      display: flex;
      flex-direction: column;
      box-shadow: var(--md-sys-elevation-level1);
    }
    
    .stat-value {
      font: var(--md-sys-typescale-display-small);
      color: var(--md-sys-color-primary);
    }
    
    .stat-label {
      font: var(--md-sys-typescale-label-large);
      color: var(--md-sys-color-on-surface-variant);
      margin-top: 8px;
    }
    
    .content-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 24px;
    }
    
    .activity-card, .learning-card {
      padding: 24px;
    }
    
    .activity-card h2, .learning-card h2 {
      font: var(--md-sys-typescale-title-large);
      color: var(--md-sys-color-on-surface);
      margin-bottom: 16px;
    }
    
    .loading-state {
      display: flex;
      align-items: center;
      gap: 12px;
      color: var(--md-sys-color-on-surface-variant);
    }
    
    .loading-dot {
      width: 8px;
      height: 8px;
      background: var(--md-sys-color-primary);
      border-radius: 50%;
      animation: md-pulse 1.5s infinite;
    }
    
    .empty-state, .ready-hint {
      color: var(--md-sys-color-on-surface-variant);
      font: var(--md-sys-typescale-body-medium);
    }
    
    .activity-list {
      list-style: none;
      padding: 0;
      margin: 0;
    }
    
    .activity-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 0;
      border-bottom: 1px solid var(--md-sys-color-outline-variant);
    }
    
    .activity-item:last-child {
      border-bottom: none;
    }
    
    .activity-type {
      font: var(--md-sys-typescale-label-small);
      padding: 4px 8px;
      border-radius: var(--md-sys-shape-corner-small);
      background: var(--md-sys-color-surface-container);
      color: var(--md-sys-color-tertiary);
      text-transform: uppercase;
    }
    
    .activity-type[data-type="Person"] { color: var(--md-sys-color-primary); }
    .activity-type[data-type="Organization"] { color: var(--md-sys-color-secondary); }
    .activity-type[data-type="Product"] { color: var(--md-sys-color-tertiary); }
    
    .activity-name {
      flex: 1;
      font: var(--md-sys-typescale-body-medium);
      color: var(--md-sys-color-on-surface);
    }
    
    .activity-confidence {
      font: var(--md-sys-typescale-label-medium);
      color: var(--md-sys-color-on-surface-variant);
    }
    
    .learning-metrics {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
    }
    
    .metric {
      text-align: center;
    }
    
    .metric-label {
      display: block;
      font: var(--md-sys-typescale-label-small);
      color: var(--md-sys-color-on-surface-variant);
      margin-bottom: 4px;
    }
    
    .metric-value {
      font: var(--md-sys-typescale-title-medium);
      color: var(--md-sys-color-primary);
    }
    
    .health-bar {
      margin-top: 32px;
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 16px;
      background: var(--md-sys-color-surface-container);
      border-radius: var(--md-sys-shape-corner-small);
    }
    
    .health-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--md-sys-color-error);
    }
    
    .health-dot.healthy {
      background: #10b981;
    }
    
    .health-text {
      font: var(--md-sys-typescale-label-medium);
      color: var(--md-sys-color-on-surface-variant);
    }
  `]
})
export class DashboardComponent implements OnInit {
  private readonly knowledgeService = inject(KnowledgeService);

  // Reactive state using Angular signals
  stats = signal<Stats>({ entities: 0, claims: 0, procedures: 0, gaps: 0, sources: 0 });
  recentEntities = signal<Entity[]>([]);
  learningStats = signal<LearningStats | null>(null);

  loadingActivity = signal(true);
  loadingLearning = signal(true);
  apiHealthy = signal(false);

  ngOnInit(): void {
    // Fetch all data on init
    this.fetchStats();
    this.fetchRecentActivity();
    this.fetchLearningStats();
    this.checkHealth();
  }

  private fetchStats(): void {
    this.knowledgeService.getStats().subscribe(data => {
      this.stats.set(data);
    });
  }

  private fetchRecentActivity(): void {
    this.knowledgeService.getEntities().subscribe(entities => {
      // Show last 5 entities as recent activity
      this.recentEntities.set(entities.slice(0, 5));
      this.loadingActivity.set(false);
    });
  }

  private fetchLearningStats(): void {
    this.knowledgeService.getLearningStats().subscribe(data => {
      this.learningStats.set(data);
      this.loadingLearning.set(false);
    });
  }

  private checkHealth(): void {
    this.knowledgeService.healthCheck().subscribe(response => {
      this.apiHealthy.set(response.status === 'healthy');
    });
  }
}
