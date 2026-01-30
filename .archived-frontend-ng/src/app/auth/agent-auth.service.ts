/**
 * GEMINI-1: Agent Auth Service
 * Real-time provider status with CLI detection
 */
import { Injectable, signal } from '@angular/core';

export interface Provider {
    id: string;
    name: string;
    emoji: string;
    tier: string;
    model: string;
    connected: boolean;
    color: string;
}

@Injectable({ providedIn: 'root' })
export class AgentAuthService {
    providers = signal<Provider[]>([
        {
            id: 'claude',
            name: 'Claude',
            emoji: '🟣',
            tier: 'Max Subscription',
            model: 'Opus 4.5',
            connected: false,
            color: '#8B5CF6'
        },
        {
            id: 'gemini',
            name: 'Gemini',
            emoji: '🔵',
            tier: 'Pro Subscription',
            model: '2.5 Flash',
            connected: false,
            color: '#4285F4'
        },
        {
            id: 'codex',
            name: 'Codex',
            emoji: '🟢',
            tier: 'Pro Subscription',
            model: 'gpt-5.2-codex',
            connected: false,
            color: '#10B981'
        },
        {
            id: 'kimi',
            name: 'Kimi',
            emoji: '🟠',
            tier: 'API Key (Whitelisted)',
            model: 'Moonshot',
            connected: false,
            color: '#F59E0B'
        }
    ]);

    async checkStatus() {
        try {
            const response = await fetch('/api/auth/status');
            const data = await response.json();

            this.providers.update(providers =>
                providers.map(p => ({
                    ...p,
                    connected: data[p.id]?.connected ?? false,
                    model: data[p.id]?.model ?? p.model
                }))
            );
        } catch (error) {
            console.log('[AgentAuthService] Using cached status');
            // Check localStorage for Kimi
            if (localStorage.getItem('KIMI_API_KEY')) {
                this.updateProvider('kimi', { connected: true });
            }
        }
    }

    async authenticate(providerId: string) {
        // For CLI-based providers, trigger auth flow
        console.log(`[AgentAuthService] Authenticating ${providerId}...`);

        try {
            const response = await fetch(`/api/auth/${providerId}/login`, {
                method: 'POST'
            });

            if (response.ok) {
                const data = await response.json();
                this.updateProvider(providerId, {
                    connected: true,
                    model: data.model
                });
            }
        } catch (error) {
            console.error(`[AgentAuthService] Auth failed for ${providerId}:`, error);
        }
    }

    setApiKey(providerId: string, apiKey: string) {
        // Store API key and update status
        this.updateProvider(providerId, { connected: true });

        // Optionally send to backend
        fetch(`/api/auth/${providerId}/key`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: apiKey })
        }).catch(console.error);
    }

    private updateProvider(id: string, updates: Partial<Provider>) {
        this.providers.update(providers =>
            providers.map(p => p.id === id ? { ...p, ...updates } : p)
        );
    }

    getProvider(id: string): Provider | undefined {
        return this.providers().find(p => p.id === id);
    }

    isConnected(id: string): boolean {
        return this.getProvider(id)?.connected ?? false;
    }
}
