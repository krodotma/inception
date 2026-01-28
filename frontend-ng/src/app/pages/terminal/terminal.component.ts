import { Component, OnInit, inject, signal, ElementRef, ViewChild, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { KnowledgeService } from '../../services/knowledge.service';

/**
 * TerminalComponent - Command-line interface for Inception.
 * 
 * Features:
 * - Command input with history
 * - Quick command buttons
 * - Output display with syntax highlighting
 * - Real API integration for commands
 */
@Component({
  selector: 'app-terminal',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="terminal-container">
      <header class="terminal-header">
        <h1>Terminal</h1>
        <div class="terminal-actions">
          <button class="action-btn" (click)="clearOutput()">Clear</button>
        </div>
      </header>
      
      <div class="terminal-viewport surface-container rounded-medium elevation-1" #terminalEl>
        <div class="terminal-output">
          @for (line of outputLines(); track $index) {
            <div class="output-line" [class]="line.type">
              <span class="line-prefix">{{ line.prefix }}</span>
              <span class="line-content">{{ line.content }}</span>
            </div>
          }
          @if (outputLines().length === 0) {
            <div class="welcome-message">
              <p>Inception Terminal v3.5.0</p>
              <p class="hint">Type 'help' for available commands</p>
            </div>
          }
        </div>
        
        <div class="terminal-input-line">
          <span class="prompt">inception &gt;</span>
          <input 
            type="text" 
            #commandInput
            [(ngModel)]="currentCommand"
            (keydown.enter)="executeCommand()"
            (keydown.arrowUp)="navigateHistory(-1)"
            (keydown.arrowDown)="navigateHistory(1)"
            placeholder="Enter command..."
            autofocus
          />
        </div>
      </div>
      
      <footer class="terminal-footer">
        <button class="quick-cmd" (click)="runQuickCommand('stats')">stats</button>
        <button class="quick-cmd" (click)="runQuickCommand('entities')">entities</button>
        <button class="quick-cmd" (click)="runQuickCommand('health')">health</button>
        <button class="quick-cmd" (click)="runQuickCommand('help')">help</button>
      </footer>
    </div>
  `,
  styles: [`
    .terminal-container {
      height: 100%;
      display: flex;
      flex-direction: column;
      padding: 16px;
      gap: 16px;
    }
    
    .terminal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    
    .terminal-header h1 {
      font: var(--md-sys-typescale-headline-medium);
    }
    
    .terminal-actions {
      display: flex;
      gap: 8px;
    }
    
    .action-btn {
      padding: 8px 16px;
      background: var(--md-sys-color-surface-container-high);
      border: 1px solid var(--md-sys-color-outline-variant);
      border-radius: var(--md-sys-shape-corner-small);
      color: var(--md-sys-color-on-surface);
      cursor: pointer;
      transition: background var(--md-motion-duration-short-2) var(--md-motion-easing-standard);
    }
    
    .action-btn:hover {
      background: var(--md-sys-color-surface-container-highest);
    }
    
    .terminal-viewport {
      flex: 1;
      padding: 16px;
      font-family: 'JetBrains Mono', 'Fira Code', monospace;
      font-size: 14px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    
    .terminal-output {
      flex: 1;
      overflow-y: auto;
      margin-bottom: 16px;
    }
    
    .output-line {
      display: flex;
      gap: 8px;
      line-height: 1.6;
    }
    
    .output-line.command {
      color: var(--md-sys-color-primary);
    }
    
    .output-line.result {
      color: var(--md-sys-color-on-surface);
    }
    
    .output-line.error {
      color: var(--md-sys-color-error);
    }
    
    .output-line.info {
      color: var(--md-sys-color-tertiary);
    }
    
    .line-prefix {
      color: var(--md-sys-color-on-surface-variant);
      user-select: none;
    }
    
    .welcome-message {
      color: var(--md-sys-color-on-surface-variant);
    }
    
    .welcome-message .hint {
      font-size: 12px;
      margin-top: 8px;
    }
    
    .terminal-input-line {
      display: flex;
      align-items: center;
      gap: 8px;
      border-top: 1px solid var(--md-sys-color-outline-variant);
      padding-top: 12px;
    }
    
    .prompt {
      color: var(--md-sys-color-primary);
      font-weight: 500;
    }
    
    .terminal-input-line input {
      flex: 1;
      background: transparent;
      border: none;
      color: var(--md-sys-color-on-surface);
      font: inherit;
      outline: none;
    }
    
    .terminal-footer {
      display: flex;
      gap: 8px;
    }
    
    .quick-cmd {
      padding: 8px 16px;
      background: var(--md-sys-color-primary-container);
      border: none;
      border-radius: var(--md-sys-shape-corner-full);
      color: var(--md-sys-color-on-primary-container);
      font: var(--md-sys-typescale-label-large);
      cursor: pointer;
      transition: all var(--md-motion-duration-short-2) var(--md-motion-easing-standard);
    }
    
    .quick-cmd:hover {
      background: var(--md-sys-color-primary);
      color: var(--md-sys-color-on-primary);
    }
  `]
})
export class TerminalComponent implements OnInit {
  private readonly knowledgeService = inject(KnowledgeService);

  @ViewChild('commandInput') commandInput!: ElementRef<HTMLInputElement>;

  // State
  currentCommand = '';
  outputLines = signal<Array<{ type: string; prefix: string; content: string }>>([]);
  commandHistory: string[] = [];
  historyIndex = -1;

  ngOnInit(): void {
    // Welcome message is shown via template
  }

  executeCommand(): void {
    const cmd = this.currentCommand.trim();
    if (!cmd) return;

    // Add to history
    this.commandHistory.push(cmd);
    this.historyIndex = this.commandHistory.length;

    // Echo command
    this.addLine('command', '>', cmd);

    // Parse and execute
    this.processCommand(cmd);

    // Clear input
    this.currentCommand = '';
  }

  private processCommand(cmd: string): void {
    const [command, ...args] = cmd.split(' ');

    switch (command.toLowerCase()) {
      case 'help':
        this.showHelp();
        break;
      case 'stats':
        this.runStats();
        break;
      case 'entities':
        this.runEntities();
        break;
      case 'health':
        this.runHealth();
        break;
      case 'clear':
        this.clearOutput();
        break;
      case 'ingest':
        if (args.length > 0) {
          this.runIngest(args[0]);
        } else {
          this.addLine('error', '!', 'Usage: ingest <url>');
        }
        break;
      default:
        this.addLine('error', '!', `Unknown command: ${command}. Type 'help' for available commands.`);
    }
  }

  private showHelp(): void {
    this.addLine('info', '?', 'Available commands:');
    this.addLine('result', ' ', '  stats     - Show system statistics');
    this.addLine('result', ' ', '  entities  - List entities (first 10)');
    this.addLine('result', ' ', '  health    - Check API health');
    this.addLine('result', ' ', '  ingest    - Ingest a URL (e.g., ingest <youtube-url>)');
    this.addLine('result', ' ', '  clear     - Clear terminal output');
    this.addLine('result', ' ', '  help      - Show this help message');
  }

  private runStats(): void {
    this.knowledgeService.getStats().subscribe(stats => {
      this.addLine('info', '📊', 'System Statistics:');
      this.addLine('result', ' ', `  Entities: ${stats.entities}`);
      this.addLine('result', ' ', `  Claims: ${stats.claims}`);
      this.addLine('result', ' ', `  Gaps: ${stats.gaps}`);
      this.addLine('result', ' ', `  Sources: ${stats.sources}`);
    });
  }

  private runEntities(): void {
    this.knowledgeService.getEntities().subscribe(entities => {
      this.addLine('info', '📦', `Entities (${entities.length} total, showing first 10):`);
      entities.slice(0, 10).forEach(e => {
        this.addLine('result', ' ', `  [${e.type}] ${e.name}`);
      });
    });
  }

  private runHealth(): void {
    this.knowledgeService.healthCheck().subscribe(response => {
      const status = response.status === 'healthy' ? '✅ API Healthy' : '❌ API Unhealthy';
      this.addLine('info', '🏥', status);
    });
  }

  private runIngest(url: string): void {
    this.addLine('info', '📥', `Starting ingestion: ${url}`);
    this.knowledgeService.ingest(url).subscribe({
      next: (response) => {
        this.addLine('result', ' ', 'Ingestion started successfully');
      },
      error: (err) => {
        this.addLine('error', '!', `Ingestion failed: ${err.message || 'Unknown error'}`);
      }
    });
  }

  runQuickCommand(cmd: string): void {
    this.currentCommand = cmd;
    this.executeCommand();
  }

  clearOutput(): void {
    this.outputLines.set([]);
  }

  navigateHistory(direction: number): void {
    const newIndex = this.historyIndex + direction;
    if (newIndex >= 0 && newIndex < this.commandHistory.length) {
      this.historyIndex = newIndex;
      this.currentCommand = this.commandHistory[newIndex];
    } else if (newIndex >= this.commandHistory.length) {
      this.historyIndex = this.commandHistory.length;
      this.currentCommand = '';
    }
  }

  private addLine(type: string, prefix: string, content: string): void {
    this.outputLines.update(lines => [...lines, { type, prefix, content }]);
  }
}
