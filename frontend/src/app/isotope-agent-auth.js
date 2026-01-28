/**
 * Isotope Agent Auth Controller
 * 
 * Implements Metafizz Isotope for Agent Auth overlay:
 * - Masonry layout for provider cards
 * - Filter by status (all/connected/pending)
 * - Sort by provider priority
 * - Animated transitions with M3 motion tokens
 */

import Isotope from 'isotope-layout';

// Provider priority order (from provider_config.py)
const PROVIDER_PRIORITY = ['claude', 'gemini', 'codex', 'kimi', 'openrouter'];

class AgentAuthIsotope {
    constructor(gridEl, options = {}) {
        this.gridEl = typeof gridEl === 'string' ? document.querySelector(gridEl) : gridEl;
        this.iso = null;
        this.options = {
            itemSelector: '.provider-card',
            layoutMode: 'fitRows',
            percentPosition: true,
            transitionDuration: '350ms',
            stagger: 50,
            ...options
        };

        this.init();
    }

    init() {
        if (!this.gridEl) {
            console.warn('[AgentAuthIsotope] Grid element not found');
            return;
        }

        // Wait for images/fonts to load
        requestAnimationFrame(() => {
            this.iso = new Isotope(this.gridEl, {
                ...this.options,
                getSortData: {
                    priority: (el) => {
                        const provider = el.dataset.provider;
                        return PROVIDER_PRIORITY.indexOf(provider);
                    },
                    status: (el) => el.classList.contains('connected') ? 0 : 1,
                    name: (el) => el.querySelector('.provider-name')?.textContent || ''
                },
                sortBy: ['status', 'priority']
            });

            this.bindFilterButtons();
            this.bindSortButtons();

            console.log('[AgentAuthIsotope] Initialized with', this.iso.items.length, 'items');
        });
    }

    /**
     * Filter cards by status
     * @param {string} filter - 'all', 'connected', 'pending', or CSS selector
     */
    filter(filter) {
        let filterFn;

        switch (filter) {
            case 'all':
                filterFn = '*';
                break;
            case 'connected':
                filterFn = '.connected';
                break;
            case 'pending':
            case 'disconnected':
                filterFn = ':not(.connected)';
                break;
            default:
                filterFn = filter;
        }

        this.iso?.arrange({ filter: filterFn });
        this.updateActiveFilter(filter);
    }

    /**
     * Sort cards
     * @param {string|string[]} sortBy - Sort criteria
     */
    sort(sortBy) {
        this.iso?.arrange({ sortBy });
    }

    /**
     * Update a provider's status and re-layout
     * @param {string} provider - Provider name
     * @param {boolean} connected - Connection status
     */
    updateStatus(provider, connected) {
        const card = this.gridEl.querySelector(`[data-provider="${provider}"]`);
        if (!card) return;

        card.classList.toggle('connected', connected);

        // Update badge
        const badge = card.querySelector('.connection-badge');
        if (badge) {
            badge.classList.toggle('connected', connected);
            badge.classList.toggle('disconnected', !connected);
            badge.querySelector('span').textContent = connected ? 'Connected' : 'Not Set';
        }

        // Re-sort to move connected cards up
        this.iso?.updateSortData(card);
        this.iso?.arrange();
    }

    /**
     * Bind filter buttons
     */
    bindFilterButtons() {
        const filterBtns = document.querySelectorAll('[data-filter]');
        filterBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.filter(btn.dataset.filter);
            });
        });
    }

    /**
     * Bind sort buttons  
     */
    bindSortButtons() {
        const sortBtns = document.querySelectorAll('[data-sort]');
        sortBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const sortValue = btn.dataset.sort.split(',');
                this.sort(sortValue);
            });
        });
    }

    /**
     * Update active filter button state
     */
    updateActiveFilter(filter) {
        const filterBtns = document.querySelectorAll('[data-filter]');
        filterBtns.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === filter);
        });
    }

    /**
     * Force layout recalculation
     */
    relayout() {
        this.iso?.layout();
    }

    /**
     * Add a new provider card
     */
    add(cardEl) {
        this.iso?.appended(cardEl);
        this.iso?.arrange();
    }

    /**
     * Remove a provider card
     */
    remove(cardEl) {
        this.iso?.remove(cardEl);
        this.iso?.layout();
    }

    /**
     * Destroy isotope instance
     */
    destroy() {
        this.iso?.destroy();
        this.iso = null;
    }
}

// Auto-initialize if data attribute present
document.addEventListener('DOMContentLoaded', () => {
    const grid = document.querySelector('[data-isotope-agent-auth]');
    if (grid) {
        window.agentAuthIsotope = new AgentAuthIsotope(grid);
    }
});

export { AgentAuthIsotope };
export default AgentAuthIsotope;
