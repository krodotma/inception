import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { KnowledgeService, Entity } from '../../services/knowledge.service';

/**
 * ExplorerComponent - Knowledge graph explorer with entity list and graph view.
 * 
 * Features:
 * - Real-time entity list from API
 * - Entity search/filter
 * - Cytoscape graph placeholder (Phase 3)
 * - Entity type color coding
 */
@Component({
  selector: 'app-explorer',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="explorer-container">
      <header class="explorer-header">
        <h1>Knowledge Explorer</h1>
        <div class="search-bar">
          <input 
            type="text" 
            placeholder="Search entities..." 
            (input)="onSearch($event)"
          />
        </div>
      </header>
      
      <div class="explorer-content">
        <aside class="sidebar surface-container rounded-medium">
          <nav class="entity-nav">
            <h3>Entities ({{ filteredEntities().length }})</h3>
            @if (loading()) {
              <p class="loading-text">Loading entities...</p>
            } @else if (filteredEntities().length === 0) {
              <p class="empty-text">No entities found.</p>
            } @else {
              <ul>
                @for (entity of filteredEntities(); track entity.id) {
                  <li 
                    class="entity-item"
                    [class.selected]="selectedEntity()?.id === entity.id"
                    (click)="selectEntity(entity)"
                  >
                    <span class="entity-badge" [style.background]="getTypeColor(entity.type)"></span>
                    <span class="entity-name">{{ entity.name }}</span>
                    <span class="entity-type">{{ entity.type }}</span>
                  </li>
                }
              </ul>
            }
          </nav>
        </aside>
        
        <main class="graph-viewport surface-container-high rounded-medium elevation-2">
          @if (selectedEntity()) {
            <div class="entity-detail">
              <h2>{{ selectedEntity()?.name }}</h2>
              <div class="detail-grid">
                <div class="detail-item">
                  <span class="detail-label">Type</span>
                  <span class="detail-value" [style.color]="getTypeColor(selectedEntity()?.type || '')">
                    {{ selectedEntity()?.type }}
                  </span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">ID</span>
                  <span class="detail-value monospace">{{ selectedEntity()?.id }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">Confidence</span>
                  <span class="detail-value">{{ ((selectedEntity()?.confidence || 0) * 100).toFixed(1) }}%</span>
                </div>
              </div>
            </div>
          } @else {
            <div class="graph-placeholder">
              <p>Select an entity to view details</p>
              <p class="hint">Graph visualization: Phase 3</p>
            </div>
          }
        </main>
      </div>
      
      <!-- Entity counts by type -->
      <footer class="type-legend">
        @for (type of uniqueTypes(); track type) {
          <span class="legend-item">
            <span class="legend-dot" [style.background]="getTypeColor(type)"></span>
            {{ type }} ({{ getTypeCount(type) }})
          </span>
        }
      </footer>
    </div>
  `,
  styles: [`
    .explorer-container {
      height: 100%;
      display: flex;
      flex-direction: column;
      padding: 16px;
      gap: 16px;
    }
    
    .explorer-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .explorer-header h1 {
      font: var(--md-sys-typescale-headline-medium);
    }
    
    .search-bar input {
      padding: 12px 16px;
      border: 1px solid var(--md-sys-color-outline);
      border-radius: var(--md-sys-shape-corner-full);
      background: var(--md-sys-color-surface-container);
      color: var(--md-sys-color-on-surface);
      width: 300px;
      font: var(--md-sys-typescale-body-medium);
      transition: border-color var(--md-motion-duration-short-3) var(--md-motion-easing-standard);
    }
    
    .search-bar input:focus {
      outline: none;
      border-color: var(--md-sys-color-primary);
    }
    
    .explorer-content {
      flex: 1;
      display: grid;
      grid-template-columns: 320px 1fr;
      gap: 16px;
      min-height: 0;
    }
    
    .sidebar {
      padding: 16px;
      overflow-y: auto;
    }
    
    .entity-nav h3 {
      font: var(--md-sys-typescale-title-medium);
      margin-bottom: 12px;
    }
    
    .entity-nav ul {
      list-style: none;
    }
    
    .entity-item {
      padding: 10px 12px;
      display: flex;
      align-items: center;
      gap: 10px;
      cursor: pointer;
      border-radius: var(--md-sys-shape-corner-small);
      transition: background var(--md-motion-duration-short-2) var(--md-motion-easing-standard);
    }
    
    .entity-item:hover {
      background: var(--md-sys-color-surface-container-high);
    }
    
    .entity-item.selected {
      background: var(--md-sys-color-primary-container);
    }
    
    .entity-badge {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      flex-shrink: 0;
    }
    
    .entity-name {
      flex: 1;
      font: var(--md-sys-typescale-body-medium);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    
    .entity-type {
      font: var(--md-sys-typescale-label-small);
      color: var(--md-sys-color-on-surface-variant);
      text-transform: uppercase;
    }
    
    .graph-viewport {
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .entity-detail {
      width: 100%;
      padding: 32px;
    }
    
    .entity-detail h2 {
      font: var(--md-sys-typescale-headline-small);
      margin-bottom: 24px;
    }
    
    .detail-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 24px;
    }
    
    .detail-item {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    
    .detail-label {
      font: var(--md-sys-typescale-label-small);
      color: var(--md-sys-color-on-surface-variant);
      text-transform: uppercase;
    }
    
    .detail-value {
      font: var(--md-sys-typescale-title-medium);
    }
    
    .detail-value.monospace {
      font-family: 'JetBrains Mono', monospace;
      font-size: 13px;
    }
    
    .graph-placeholder {
      text-align: center;
      color: var(--md-sys-color-on-surface-variant);
    }
    
    .hint {
      font: var(--md-sys-typescale-body-small);
      margin-top: 8px;
    }
    
    .loading-text, .empty-text {
      font: var(--md-sys-typescale-body-medium);
      color: var(--md-sys-color-on-surface-variant);
      padding: 12px 0;
    }
    
    .type-legend {
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
      padding: 12px 16px;
      background: var(--md-sys-color-surface-container);
      border-radius: var(--md-sys-shape-corner-small);
    }
    
    .legend-item {
      display: flex;
      align-items: center;
      gap: 6px;
      font: var(--md-sys-typescale-label-medium);
      color: var(--md-sys-color-on-surface-variant);
    }
    
    .legend-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
    }
  `]
})
export class ExplorerComponent implements OnInit {
  private readonly knowledgeService = inject(KnowledgeService);

  // State
  entities = signal<Entity[]>([]);
  filteredEntities = signal<Entity[]>([]);
  selectedEntity = signal<Entity | null>(null);
  loading = signal(true);
  searchQuery = signal('');

  // Computed
  uniqueTypes = signal<string[]>([]);

  ngOnInit(): void {
    this.fetchEntities();
  }

  private fetchEntities(): void {
    this.knowledgeService.getEntities().subscribe(data => {
      this.entities.set(data);
      this.filteredEntities.set(data);

      // Extract unique types
      const types = [...new Set(data.map(e => e.type))];
      this.uniqueTypes.set(types);

      this.loading.set(false);
    });
  }

  onSearch(event: Event): void {
    const query = (event.target as HTMLInputElement).value.toLowerCase();
    this.searchQuery.set(query);

    if (!query) {
      this.filteredEntities.set(this.entities());
    } else {
      const filtered = this.entities().filter(e =>
        e.name.toLowerCase().includes(query) ||
        e.type.toLowerCase().includes(query)
      );
      this.filteredEntities.set(filtered);
    }
  }

  selectEntity(entity: Entity): void {
    this.selectedEntity.set(entity);
  }

  getTypeCount(type: string): number {
    return this.entities().filter(e => e.type === type).length;
  }

  getTypeColor(type: string): string {
    const colors: Record<string, string> = {
      'PERSON': '#cba6f7',
      'Person': '#cba6f7',
      'ORGANIZATION': '#94e2d5',
      'Organization': '#94e2d5',
      'product': '#fab387',
      'Product': '#fab387',
      'component': '#89b4fa',
      'grant_type': '#f9e2af',
      'token_type': '#f5c2e7',
      'standard': '#a6e3a1',
      'flow': '#cba6f7',
      'DATE': '#fab387'
    };
    return colors[type] || '#89b4fa';
  }
}
