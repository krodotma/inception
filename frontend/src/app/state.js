/**
 * KINESIS: Inception App State Machine
 * 
 * Explicit state management for all UI states.
 * No ad-hoc booleans—every state transition is declared.
 * 
 * Model: Opus 4.5 ULTRATHINK
 * Persona: KINESIS (Motion Systems Engineer)
 */

// =============================================================================
// STATE MACHINE FACTORY
// =============================================================================

function createStateMachine(config) {
    let currentState = config.initial;
    const listeners = new Set();

    return {
        get state() { return currentState; },

        send(event, payload = {}) {
            const stateConfig = config.states[currentState];
            if (!stateConfig?.on?.[event]) return currentState;

            const transition = stateConfig.on[event];
            const nextState = typeof transition === 'string' ? transition : transition.target;

            // Exit action
            stateConfig.onExit?.({ from: currentState, to: nextState, event, payload });

            // Transition action
            if (typeof transition === 'object' && transition.action) {
                transition.action({ from: currentState, to: nextState, event, payload });
            }

            const previousState = currentState;
            currentState = nextState;

            // Entry action
            config.states[nextState]?.onEnter?.({ from: previousState, to: nextState, event, payload });

            // Notify
            listeners.forEach(fn => fn({ previousState, currentState, event, payload }));

            return currentState;
        },

        can(event) {
            return !!config.states[currentState]?.on?.[event];
        },

        subscribe(fn) {
            listeners.add(fn);
            return () => listeners.delete(fn);
        },

        matches(state) {
            return currentState === state;
        },
    };
}

// =============================================================================
// APP SHELL STATE MACHINE
// =============================================================================

const appShell = createStateMachine({
    initial: 'loading',

    states: {
        loading: {
            on: {
                LOADED: 'idle',
                ERROR: 'error',
            },
            onEnter: () => {
                document.querySelector('.loading-screen')?.classList.add('visible');
            },
            onExit: () => {
                const loader = document.querySelector('.loading-screen');
                loader?.classList.add('fade-out');
                setTimeout(() => loader?.classList.remove('visible', 'fade-out'), 500);
            },
        },

        idle: {
            on: {
                NAVIGATE: 'navigating',
                OPEN_MODAL: 'modal',
                OPEN_SEARCH: 'search',
            },
        },

        navigating: {
            on: {
                NAV_COMPLETE: 'idle',
                NAV_ERROR: 'error',
            },
        },

        modal: {
            on: {
                CLOSE_MODAL: 'idle',
            },
        },

        search: {
            on: {
                CLOSE_SEARCH: 'idle',
                NAVIGATE: 'navigating',
            },
        },

        error: {
            on: {
                RETRY: 'loading',
                DISMISS: 'idle',
            },
        },
    },
});

// =============================================================================
// SIDEBAR STATE MACHINE
// =============================================================================

const sidebar = createStateMachine({
    initial: 'expanded',

    states: {
        expanded: {
            on: {
                COLLAPSE: 'collapsing',
                HIDE: 'hiding',
            },
            onEnter: () => {
                const el = document.querySelector('.sidebar');
                el?.setAttribute('data-state', 'expanded');
            },
        },

        collapsing: {
            on: { COLLAPSED: 'collapsed' },
            onEnter: () => {
                const el = document.querySelector('.sidebar');
                el?.setAttribute('data-state', 'collapsing');
                setTimeout(() => sidebar.send('COLLAPSED'), 250); // Match animation
            },
        },

        collapsed: {
            on: {
                EXPAND: 'expanding',
                HIDE: 'hiding',
            },
            onEnter: () => {
                document.querySelector('.sidebar')?.setAttribute('data-state', 'collapsed');
            },
        },

        expanding: {
            on: { EXPANDED: 'expanded' },
            onEnter: () => {
                const el = document.querySelector('.sidebar');
                el?.setAttribute('data-state', 'expanding');
                setTimeout(() => sidebar.send('EXPANDED'), 300);
            },
        },

        hiding: {
            on: { HIDDEN: 'hidden' },
            onEnter: () => {
                const el = document.querySelector('.sidebar');
                el?.setAttribute('data-state', 'hiding');
                setTimeout(() => sidebar.send('HIDDEN'), 200);
            },
        },

        hidden: {
            on: {
                SHOW: 'expanding',
                SHOW_COLLAPSED: 'collapsed',
            },
            onEnter: () => {
                document.querySelector('.sidebar')?.setAttribute('data-state', 'hidden');
            },
        },
    },
});

// =============================================================================
// OVERLAY STATE MACHINE (Modal/Sheet)
// =============================================================================

const overlay = createStateMachine({
    initial: 'closed',

    states: {
        closed: {
            on: {
                OPEN: 'opening',
                PEEK: 'peeking',
            },
        },

        opening: {
            on: { OPENED: 'open', CANCEL: 'closing' },
            onEnter: async () => {
                const el = document.querySelector('.overlay');
                el?.classList.add('visible');
                el?.setAttribute('data-state', 'opening');
                await animationFrame(300);
                overlay.send('OPENED');
            },
        },

        open: {
            on: {
                CLOSE: 'closing',
                PEEK: 'peeking',
            },
            onEnter: () => {
                document.querySelector('.overlay')?.setAttribute('data-state', 'open');
            },
        },

        peeking: {
            on: {
                EXPAND: 'open',
                CLOSE: 'closing',
            },
            onEnter: () => {
                document.querySelector('.overlay')?.setAttribute('data-state', 'peek');
            },
        },

        closing: {
            on: { CLOSED: 'closed' },
            onEnter: async () => {
                const el = document.querySelector('.overlay');
                el?.setAttribute('data-state', 'closing');
                await animationFrame(250);
                el?.classList.remove('visible');
                overlay.send('CLOSED');
            },
        },
    },
});

// =============================================================================
// THEME STATE MACHINE
// =============================================================================

const theme = createStateMachine({
    initial: localStorage.getItem('inception-theme') || 'system',

    states: {
        light: {
            on: { TOGGLE: 'dark', SET_SYSTEM: 'system' },
            onEnter: () => applyTheme('light'),
        },
        dark: {
            on: { TOGGLE: 'light', SET_SYSTEM: 'system' },
            onEnter: () => applyTheme('dark'),
        },
        system: {
            on: { TOGGLE: 'light' },
            onEnter: () => {
                const preferred = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
                applyTheme(preferred);
            },
        },
    },
});

function applyTheme(mode) {
    document.documentElement.setAttribute('data-theme', mode);
    localStorage.setItem('inception-theme', mode);

    // Update theme toggle icon
    const icon = document.querySelector('.theme-toggle .material-symbols-outlined');
    if (icon) {
        icon.textContent = mode === 'dark' ? 'light_mode' : 'dark_mode';
    }
}

// =============================================================================
// VIEW TRANSITIONS
// =============================================================================

async function navigateWithTransition(route, direction = 'forward') {
    if (appShell.state === 'navigating') return;

    appShell.send('NAVIGATE');

    // Set direction for CSS
    document.documentElement.setAttribute('data-nav-direction', direction);

    const updateDOM = () => {
        // Hide all views
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));

        // Show target view
        const target = document.getElementById(`${route}-view`);
        target?.classList.add('active');

        // Update nav
        document.querySelectorAll('.nav-item').forEach(n => {
            n.classList.toggle('active', n.dataset.view === route);
        });

        // Update URL
        history.pushState({ route }, '', `#${route}`);
    };

    if (document.startViewTransition) {
        try {
            const transition = document.startViewTransition(updateDOM);
            await transition.finished;
        } catch (e) {
            updateDOM();
        }
    } else {
        updateDOM();
    }

    appShell.send('NAV_COMPLETE');
}

// =============================================================================
// SHARED ELEMENT TRANSITIONS
// =============================================================================

function setSharedElement(element, name) {
    if (!element) return;
    element.style.viewTransitionName = name;
}

function clearSharedElement(element) {
    if (!element) return;
    element.style.viewTransitionName = '';
}

// Entity card → detail pattern
async function navigateToEntityDetail(entityId) {
    const card = document.querySelector(`[data-entity-id="${entityId}"]`);
    const cardImage = card?.querySelector('.entity-icon');

    // Set shared element before transition
    setSharedElement(cardImage, 'entity-hero');

    await navigateWithTransition('detail');

    // Set on detail page
    const detailHero = document.querySelector('.detail-hero');
    setSharedElement(detailHero, 'entity-hero');
}

// =============================================================================
// UTILITIES
// =============================================================================

function animationFrame(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Reduced motion check
function prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

// =============================================================================
// INITIALIZATION
// =============================================================================

function initStateMachines() {
    // Initialize theme
    theme.send('SET_SYSTEM'); // Will use stored preference or system

    // Handle popstate
    window.addEventListener('popstate', (e) => {
        const route = e.state?.route || 'dashboard';
        navigateWithTransition(route, 'back');
    });

    // Sidebar toggle
    document.querySelector('.sidebar-toggle')?.addEventListener('click', () => {
        if (sidebar.matches('expanded')) {
            sidebar.send('COLLAPSE');
        } else if (sidebar.matches('collapsed')) {
            sidebar.send('EXPAND');
        }
    });

    // Theme toggle
    document.querySelector('.theme-toggle')?.addEventListener('click', () => {
        theme.send('TOGGLE');
    });

    // Nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const view = item.dataset.view;
            if (view) navigateWithTransition(view);
        });
    });

    // Mark loaded
    setTimeout(() => appShell.send('LOADED'), 800);
}

// Auto-init
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initStateMachines);
} else {
    initStateMachines();
}

// =============================================================================
// EXPORTS
// =============================================================================

window.InceptionState = {
    appShell,
    sidebar,
    overlay,
    theme,
    navigateWithTransition,
    navigateToEntityDetail,
    prefersReducedMotion,
};

export {
    appShell,
    sidebar,
    overlay,
    theme,
    navigateWithTransition,
    navigateToEntityDetail,
    createStateMachine,
};
