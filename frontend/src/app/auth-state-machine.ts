/**
 * GEMINI-1 ULTRATHINK: XState Machine for Auth Flow
 * 
 * State machine managing:
 * - Auth overlay visibility
 * - Provider connection flow
 * - Modal states
 * - Filter states
 * - Error handling
 */

// Extend Window interface for global animation systems
declare global {
    interface Window {
        particleSystem?: {
            emitConnectionParticles: (provider: string | null, x: number, y: number) => void;
        };
        confetti?: {
            fire: (x: number, y: number) => void;
        };
    }
}

// State types
type AuthState =
    | 'closed'
    | 'opening'
    | 'open'
    | 'closing'
    | 'connecting'
    | 'error';

type ModalState =
    | 'hidden'
    | 'entering'
    | 'visible'
    | 'exiting';

type ProviderState =
    | 'disconnected'
    | 'connecting'
    | 'authenticating'
    | 'connected'
    | 'error';

interface AuthContext {
    activeFilter: 'all' | 'connected' | 'pending';
    selectedProvider: string | null;
    error: string | null;
    providers: Map<string, ProviderState>;
    kimiModalState: ModalState;
}

// XState-like machine definition
const authMachine = {
    id: 'agentAuth',
    initial: 'closed',
    context: {
        activeFilter: 'all',
        selectedProvider: null,
        error: null,
        providers: new Map([
            ['claude', 'connected'],
            ['gemini', 'connected'],
            ['codex', 'connected'],
            ['kimi', 'disconnected']
        ]),
        kimiModalState: 'hidden'
    } as AuthContext,

    states: {
        closed: {
            on: {
                OPEN: { target: 'opening' }
            }
        },

        opening: {
            entry: ['playEntryAnimation'],
            after: {
                500: { target: 'open' }
            }
        },

        open: {
            on: {
                CLOSE: { target: 'closing' },
                SELECT_PROVIDER: {
                    actions: ['setSelectedProvider'],
                    target: 'connecting'
                },
                SET_FILTER: {
                    actions: ['setFilter']
                },
                OPEN_KIMI_MODAL: {
                    actions: ['openKimiModal']
                },
                CLOSE_KIMI_MODAL: {
                    actions: ['closeKimiModal']
                }
            }
        },

        closing: {
            entry: ['playExitAnimation'],
            after: {
                300: { target: 'closed' }
            }
        },

        connecting: {
            on: {
                CONNECTION_SUCCESS: {
                    actions: ['updateProviderStatus', 'playSuccessAnimation'],
                    target: 'open'
                },
                CONNECTION_FAILURE: {
                    actions: ['setError'],
                    target: 'error'
                }
            }
        },

        error: {
            on: {
                DISMISS_ERROR: { target: 'open' },
                RETRY: { target: 'connecting' }
            }
        }
    }
};

// State machine implementation
class AuthStateMachine {
    private state: AuthState = 'closed';
    private context: AuthContext;
    private listeners: Set<(state: AuthState, context: AuthContext) => void> = new Set();

    constructor() {
        this.context = { ...authMachine.context };
    }

    getState() {
        return { state: this.state, context: this.context };
    }

    subscribe(listener: (state: AuthState, context: AuthContext) => void) {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }

    private notify() {
        this.listeners.forEach(fn => fn(this.state, this.context));
    }

    send(event: string, payload?: any) {
        console.log(`[AuthStateMachine] ${this.state} + ${event}`);

        switch (this.state) {
            case 'closed':
                if (event === 'OPEN') {
                    this.state = 'opening';
                    this.playEntryAnimation();
                    setTimeout(() => {
                        this.state = 'open';
                        this.notify();
                    }, 500);
                }
                break;

            case 'open':
                if (event === 'CLOSE') {
                    this.state = 'closing';
                    this.playExitAnimation();
                    setTimeout(() => {
                        this.state = 'closed';
                        this.notify();
                    }, 300);
                }
                else if (event === 'SELECT_PROVIDER') {
                    this.context.selectedProvider = payload;
                    this.state = 'connecting';
                    this.initiateConnection(payload);
                }
                else if (event === 'SET_FILTER') {
                    this.context.activeFilter = payload;
                    this.playFilterAnimation();
                }
                else if (event === 'OPEN_KIMI_MODAL') {
                    this.context.kimiModalState = 'entering';
                    setTimeout(() => {
                        this.context.kimiModalState = 'visible';
                        this.notify();
                    }, 300);
                }
                else if (event === 'CLOSE_KIMI_MODAL') {
                    this.context.kimiModalState = 'exiting';
                    setTimeout(() => {
                        this.context.kimiModalState = 'hidden';
                        this.notify();
                    }, 200);
                }
                break;

            case 'connecting':
                if (event === 'CONNECTION_SUCCESS') {
                    this.context.providers.set(this.context.selectedProvider!, 'connected');
                    this.context.selectedProvider = null;
                    this.playSuccessAnimation();
                    this.state = 'open';
                }
                else if (event === 'CONNECTION_FAILURE') {
                    this.context.error = payload;
                    this.state = 'error';
                }
                break;

            case 'error':
                if (event === 'DISMISS_ERROR') {
                    this.context.error = null;
                    this.state = 'open';
                }
                else if (event === 'RETRY') {
                    this.context.error = null;
                    this.state = 'connecting';
                    this.initiateConnection(this.context.selectedProvider!);
                }
                break;
        }

        this.notify();
    }

    // Animation actions
    private playEntryAnimation() {
        const overlay = document.querySelector('.agent-auth-backdrop');
        const modal = document.querySelector('.agent-auth-overlay');

        if (overlay) overlay.classList.add('visible');
        if (modal) {
            modal.classList.add('entering');
            setTimeout(() => modal.classList.remove('entering'), 500);
        }
    }

    private playExitAnimation() {
        const overlay = document.querySelector('.agent-auth-backdrop');
        const modal = document.querySelector('.agent-auth-overlay');

        if (modal) modal.classList.add('exiting');
        setTimeout(() => {
            if (overlay) overlay.classList.remove('visible');
            if (modal) modal.classList.remove('exiting');
        }, 300);
    }

    private playFilterAnimation() {
        const cards = document.querySelectorAll('.provider-card');
        const filter = this.context.activeFilter;

        cards.forEach((card, i) => {
            const isConnected = card.classList.contains('connected');
            const shouldShow =
                filter === 'all' ||
                (filter === 'connected' && isConnected) ||
                (filter === 'pending' && !isConnected);

            (card as HTMLElement).style.transition = `opacity 0.3s ${i * 50}ms, transform 0.3s ${i * 50}ms`;
            (card as HTMLElement).style.opacity = shouldShow ? '1' : '0';
            (card as HTMLElement).style.transform = shouldShow ? 'scale(1)' : 'scale(0.9)';
        });
    }

    private playSuccessAnimation() {
        const provider = this.context.selectedProvider;
        const card = document.querySelector(`[data-provider="${provider}"]`);

        if (card && window.particleSystem) {
            const rect = card.getBoundingClientRect();
            window.particleSystem.emitConnectionParticles(
                provider,
                rect.left + rect.width / 2,
                rect.top + rect.height / 2
            );
        }

        if (window.confetti) {
            window.confetti.fire(window.innerWidth / 2, window.innerHeight / 2);
        }
    }

    private async initiateConnection(provider: string) {
        try {
            // Simulated API call
            await new Promise(resolve => setTimeout(resolve, 1500));

            // Check if we have credentials
            if (provider === 'kimi') {
                const key = localStorage.getItem('KIMI_API_KEY');
                if (!key) {
                    this.send('CONNECTION_FAILURE', 'API key required');
                    return;
                }
            }

            this.send('CONNECTION_SUCCESS');
        } catch (error: unknown) {
            const message = error instanceof Error ? error.message : 'Unknown error';
            this.send('CONNECTION_FAILURE', message);
        }
    }
}

// Singleton instance
const authStateMachine = new AuthStateMachine();

// Connect to DOM
document.addEventListener('DOMContentLoaded', () => {
    const trigger = document.querySelector('.demo-trigger');
    const closeBtn = document.querySelector('.agent-auth-close');
    const filterBtns = document.querySelectorAll('.filter-btn');
    const backdrop = document.querySelector('.agent-auth-backdrop');

    trigger?.addEventListener('click', () => authStateMachine.send('OPEN'));
    closeBtn?.addEventListener('click', () => authStateMachine.send('CLOSE'));
    backdrop?.addEventListener('click', (e) => {
        if ((e.target as Element).classList.contains('agent-auth-backdrop')) {
            authStateMachine.send('CLOSE');
        }
    });

    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const filter = (btn as HTMLElement).dataset.filter;
            authStateMachine.send('SET_FILTER', filter);

            // Update active state
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });

    // Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const { context } = authStateMachine.getState();
            if (context.kimiModalState !== 'hidden') {
                authStateMachine.send('CLOSE_KIMI_MODAL');
            } else {
                authStateMachine.send('CLOSE');
            }
        }
    });
});

export { AuthStateMachine, authStateMachine };
export default authStateMachine;
