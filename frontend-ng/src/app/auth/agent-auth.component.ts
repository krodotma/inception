/**
 * GEMINI-1: Agent Auth Component
 * Angular 17 Standalone Component with M3 Theming
 */
import {
    Component,
    signal,
    computed,
    inject,
    OnInit,
    OnDestroy,
    HostListener
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AgentAuthService, Provider } from './agent-auth.service';

@Component({
    selector: 'app-agent-auth',
    standalone: true,
    imports: [CommonModule, FormsModule],
    template: `
        <div class="agent-auth-backdrop alive-modal-backdrop" 
             [class.visible]="isVisible()"
             (click)="onBackdropClick($event)">
            
            <div class="agent-auth-overlay alive-modal" 
                 role="dialog" 
                 aria-labelledby="auth-title"
                 [attr.aria-hidden]="!isVisible()">
                
                <!-- Header -->
                <div class="agent-auth-header">
                    <h2 id="auth-title" class="agent-auth-title">Connect AI Providers</h2>
                    <button class="agent-auth-close" 
                            (click)="close()" 
                            aria-label="Close dialog">×</button>
                </div>

                <!-- Filter Bar -->
                <div class="agent-auth-filters" role="tablist">
                    @for (filter of filters; track filter.value) {
                        <button class="filter-btn alive-ripple"
                                [class.active]="activeFilter() === filter.value"
                                (click)="setFilter(filter.value)"
                                role="tab"
                                [attr.aria-selected]="activeFilter() === filter.value">
                            {{ filter.label }}
                        </button>
                    }
                </div>

                <!-- Provider Grid -->
                <div class="agent-auth-providers alive-stagger" role="list">
                    @for (provider of filteredProviders(); track provider.id) {
                        <div class="provider-card alive-card-3d"
                             [class.connected]="provider.connected"
                             [attr.data-provider]="provider.id"
                             role="listitem">
                            
                            <div class="connection-badge"
                                 [class.connected]="provider.connected"
                                 [class.disconnected]="!provider.connected">
                                <span>{{ provider.connected ? 'Connected' : 'Not Set' }}</span>
                            </div>
                            
                            <div class="provider-logo">{{ provider.emoji }}</div>
                            
                            <div class="provider-info">
                                <h3 class="provider-name">{{ provider.name }}</h3>
                                <span class="provider-tier">{{ provider.tier }}</span>
                            </div>
                            
                            <button class="auth-button alive-ripple"
                                    [class.connected]="provider.connected"
                                    [disabled]="provider.connected"
                                    (click)="handleAuth(provider)">
                                {{ provider.connected ? '✓ ' + provider.model + ' Active' : 'Configure' }}
                            </button>
                        </div>
                    }
                </div>

                <!-- Footer -->
                <div class="agent-auth-footer">
                    <span class="auth-status-summary">
                        <strong>{{ connectedCount() }}</strong> of {{ providers().length }} providers connected
                    </span>
                    <a href="#" class="auth-help-link">Need help connecting?</a>
                </div>
            </div>
        </div>

        <!-- Kimi API Key Modal -->
        @if (showKimiModal()) {
            <div class="agent-auth-backdrop alive-modal-backdrop visible"
                 (click)="closeKimiModal()">
                <div class="agent-auth-overlay alive-modal" 
                     style="max-width: 420px;"
                     (click)="$event.stopPropagation()">
                    
                    <div class="agent-auth-header">
                        <h2 class="agent-auth-title">🟠 Configure Kimi API</h2>
                        <button class="agent-auth-close" (click)="closeKimiModal()">×</button>
                    </div>
                    
                    <div style="padding: 20px 0;">
                        <p style="color: rgba(255,255,255,0.7); margin-bottom: 16px; font-size: 0.9rem;">
                            Kimi uses API key authentication. Enter your Moonshot API key below.
                        </p>
                        
                        <label style="display: block; color: rgba(255,255,255,0.5); font-size: 0.75rem; margin-bottom: 6px;">
                            API Key
                        </label>
                        <input type="password" 
                               [(ngModel)]="kimiApiKey"
                               placeholder="sk-..."
                               class="api-key-input">
                        
                        <div style="display: flex; gap: 8px; align-items: center; margin: 12px 0 16px;">
                            <input type="checkbox" id="saveKey" [(ngModel)]="saveToEnv">
                            <label for="saveKey" style="color: rgba(255,255,255,0.6); font-size: 0.8rem;">
                                Save to environment
                            </label>
                        </div>
                        
                        <div style="display: flex; gap: 12px;">
                            <button class="auth-button alive-ripple" 
                                    (click)="closeKimiModal()"
                                    style="flex: 1;">Cancel</button>
                            <button class="auth-button alive-ripple" 
                                    (click)="saveKimiKey()"
                                    style="flex: 2; background: linear-gradient(135deg, #F59E0B, #D97706); border: none;">
                                ✓ Save & Connect
                            </button>
                        </div>
                    </div>
                    
                    <div style="padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.1);">
                        <a href="https://platform.moonshot.cn/" target="_blank" 
                           style="color: #F59E0B; font-size: 0.8rem; text-decoration: none;">
                            Get API key from Moonshot →
                        </a>
                    </div>
                </div>
            </div>
        }
    `,
    styles: [`
        .api-key-input {
            width: 100%;
            padding: 12px 16px;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.2);
            background: rgba(255,255,255,0.05);
            color: #fff;
            font-size: 0.9rem;
            transition: all 0.2s;
        }
        .api-key-input:focus {
            border-color: #F59E0B;
            box-shadow: 0 0 0 3px rgba(245,158,11,0.2);
            outline: none;
        }
        .agent-auth-filters {
            margin-bottom: 16px;
            display: flex;
            gap: 8px;
        }
        .filter-btn {
            padding: 6px 12px;
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.2);
            background: transparent;
            color: rgba(255,255,255,0.6);
            cursor: pointer;
            font-size: 0.75rem;
            transition: all 0.2s;
        }
        .filter-btn.active {
            background: rgba(255,255,255,0.1);
            color: #fff;
        }
    `]
})
export class AgentAuthComponent implements OnInit, OnDestroy {
    private authService = inject(AgentAuthService);

    // Signals
    isVisible = signal(false);
    activeFilter = signal<'all' | 'connected' | 'pending'>('all');
    showKimiModal = signal(false);
    kimiApiKey = '';
    saveToEnv = true;

    providers = this.authService.providers;

    filters = [
        { label: 'All', value: 'all' as const },
        { label: 'Connected', value: 'connected' as const },
        { label: 'Pending', value: 'pending' as const }
    ];

    // Computed
    filteredProviders = computed(() => {
        const filter = this.activeFilter();
        const all = this.providers();

        if (filter === 'connected') return all.filter(p => p.connected);
        if (filter === 'pending') return all.filter(p => !p.connected);
        return all;
    });

    connectedCount = computed(() => this.providers().filter(p => p.connected).length);

    ngOnInit() {
        this.authService.checkStatus();
    }

    ngOnDestroy() { }

    @HostListener('document:keydown.escape')
    onEscape() {
        if (this.showKimiModal()) {
            this.closeKimiModal();
        } else if (this.isVisible()) {
            this.close();
        }
    }

    open() {
        this.isVisible.set(true);
        document.body.style.overflow = 'hidden';
    }

    close() {
        this.isVisible.set(false);
        document.body.style.overflow = '';
    }

    onBackdropClick(event: MouseEvent) {
        if ((event.target as HTMLElement).classList.contains('agent-auth-backdrop')) {
            this.close();
        }
    }

    setFilter(filter: 'all' | 'connected' | 'pending') {
        this.activeFilter.set(filter);
    }

    handleAuth(provider: Provider) {
        if (provider.id === 'kimi') {
            this.showKimiModal.set(true);
            // Prepopulate from localStorage
            const saved = localStorage.getItem('KIMI_API_KEY');
            if (saved) this.kimiApiKey = saved;
        } else {
            this.authService.authenticate(provider.id);
        }
    }

    closeKimiModal() {
        this.showKimiModal.set(false);
        this.kimiApiKey = '';
    }

    saveKimiKey() {
        if (!this.kimiApiKey.trim()) return;

        if (this.saveToEnv) {
            localStorage.setItem('KIMI_API_KEY', this.kimiApiKey);
        }

        this.authService.setApiKey('kimi', this.kimiApiKey);
        this.closeKimiModal();
    }
}
