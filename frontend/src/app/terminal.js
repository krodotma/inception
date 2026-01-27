/**
 * NOVA-1 ULTRATHINK: Enhanced Terminal Integration
 * 
 * Additions:
 * - Real WebSocket connection to backend
 * - Reconnection with exponential backoff
 * - Multiple terminal tabs
 * - Search within buffer
 * - Session persistence
 * 
 * Model: Opus 4.5 ULTRATHINK
 */

// =============================================================================
// TERMINAL MANAGER
// =============================================================================

class InceptionTerminal {
    constructor(container, options = {}) {
        this.container = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        this.options = {
            wsUrl: options.wsUrl || `ws://${location.host}/ws/terminal`,
            reconnect: options.reconnect !== false,
            maxReconnectAttempts: options.maxReconnectAttempts || 10,
            fontSize: options.fontSize || 14,
            ...options
        };

        this.terminals = new Map(); // tabId -> terminal instance
        this.activeTabId = null;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.reconnectTimer = null;

        this.init();
    }

    async init() {
        // Dynamic imports
        const { Terminal } = await import('xterm');
        const { FitAddon } = await import('xterm-addon-fit');
        const { WebLinksAddon } = await import('xterm-addon-web-links');
        const { SearchAddon } = await import('xterm-addon-search');

        this.Terminal = Terminal;
        this.FitAddon = FitAddon;
        this.WebLinksAddon = WebLinksAddon;
        this.SearchAddon = SearchAddon;

        // Create UI
        this.createUI();

        // Create initial tab
        this.createTab('main');

        // Connect WebSocket
        this.connect();

        // Handle resize
        window.addEventListener('resize', () => this.fit());

        // Keyboard shortcuts
        this.setupKeyboard();

        // Restore session
        this.restoreSession();
    }

    // ===========================================================================
    // UI
    // ===========================================================================

    createUI() {
        this.container.innerHTML = `
      <div class="terminal-tabs">
        <div class="terminal-tabs-list"></div>
        <button class="terminal-tab-add" title="New tab">+</button>
      </div>
      <div class="terminal-panels"></div>
      <div class="terminal-search-overlay">
        <input type="text" class="terminal-search-input" placeholder="Search...">
        <span class="terminal-search-count"></span>
        <button class="terminal-search-prev">↑</button>
        <button class="terminal-search-next">↓</button>
        <button class="terminal-search-close">×</button>
      </div>
      <div class="terminal-status">
        <span class="terminal-status-connection">Disconnected</span>
        <span class="terminal-status-info"></span>
      </div>
    `;

        // Tab events
        this.container.querySelector('.terminal-tab-add').addEventListener('click', () => {
            const tabId = `tab-${Date.now()}`;
            this.createTab(tabId);
        });

        // Search events
        const searchInput = this.container.querySelector('.terminal-search-input');
        const searchCount = this.container.querySelector('.terminal-search-count');

        searchInput.addEventListener('input', () => {
            const term = this.getActiveTerminal();
            if (term?.searchAddon) {
                term.searchAddon.findNext(searchInput.value);
            }
        });

        this.container.querySelector('.terminal-search-prev').addEventListener('click', () => {
            const term = this.getActiveTerminal();
            if (term?.searchAddon) term.searchAddon.findPrevious(searchInput.value);
        });

        this.container.querySelector('.terminal-search-next').addEventListener('click', () => {
            const term = this.getActiveTerminal();
            if (term?.searchAddon) term.searchAddon.findNext(searchInput.value);
        });

        this.container.querySelector('.terminal-search-close').addEventListener('click', () => {
            this.hideSearch();
        });
    }

    createTab(tabId, title = 'Terminal') {
        const tabsList = this.container.querySelector('.terminal-tabs-list');
        const panels = this.container.querySelector('.terminal-panels');

        // Create tab button
        const tabBtn = document.createElement('button');
        tabBtn.className = 'terminal-tab';
        tabBtn.dataset.tabId = tabId;
        tabBtn.innerHTML = `
      <span class="terminal-tab-title">${title}</span>
      <button class="terminal-tab-close" title="Close">×</button>
    `;
        tabsList.appendChild(tabBtn);

        // Tab click
        tabBtn.addEventListener('click', (e) => {
            if (!e.target.classList.contains('terminal-tab-close')) {
                this.activateTab(tabId);
            }
        });

        // Tab close
        tabBtn.querySelector('.terminal-tab-close').addEventListener('click', (e) => {
            e.stopPropagation();
            this.closeTab(tabId);
        });

        // Create panel
        const panel = document.createElement('div');
        panel.className = 'terminal-panel';
        panel.dataset.tabId = tabId;
        panels.appendChild(panel);

        // Create terminal
        const term = new this.Terminal({
            fontFamily: '"JetBrains Mono", "Fira Code", monospace',
            fontSize: this.options.fontSize,
            theme: {
                background: '#1e1e2e',
                foreground: '#cdd6f4',
                cursor: '#f5e0dc',
                cursorAccent: '#1e1e2e',
                selectionBackground: 'rgba(245, 194, 231, 0.3)',
                black: '#45475a',
                red: '#f38ba8',
                green: '#a6e3a1',
                yellow: '#f9e2af',
                blue: '#89b4fa',
                magenta: '#f5c2e7',
                cyan: '#94e2d5',
                white: '#bac2de',
                brightBlack: '#585b70',
                brightRed: '#f38ba8',
                brightGreen: '#a6e3a1',
                brightYellow: '#f9e2af',
                brightBlue: '#89b4fa',
                brightMagenta: '#f5c2e7',
                brightCyan: '#94e2d5',
                brightWhite: '#a6adc8',
            },
            cursorBlink: true,
            cursorStyle: 'bar',
            scrollback: 10000,
        });

        // Addons
        const fitAddon = new this.FitAddon();
        const webLinksAddon = new this.WebLinksAddon();
        const searchAddon = new this.SearchAddon();

        term.loadAddon(fitAddon);
        term.loadAddon(webLinksAddon);
        term.loadAddon(searchAddon);

        term.open(panel);
        fitAddon.fit();

        // Store
        this.terminals.set(tabId, {
            term,
            fitAddon,
            searchAddon,
            history: [],
            historyIndex: -1,
            currentLine: '',
        });

        // Input handling
        term.onData(data => this.handleInput(tabId, data));

        // Activate
        this.activateTab(tabId);

        // Welcome message
        term.writeln('\x1b[38;5;141mInception Terminal v2.0\x1b[0m');
        term.writeln('\x1b[90mType "help" for available commands\x1b[0m');
        term.writeln('');
        this.writePrompt(tabId);

        return tabId;
    }

    activateTab(tabId) {
        // Deactivate all
        this.container.querySelectorAll('.terminal-tab').forEach(t => t.classList.remove('active'));
        this.container.querySelectorAll('.terminal-panel').forEach(p => p.classList.remove('active'));

        // Activate target
        this.container.querySelector(`.terminal-tab[data-tab-id="${tabId}"]`)?.classList.add('active');
        this.container.querySelector(`.terminal-panel[data-tab-id="${tabId}"]`)?.classList.add('active');

        this.activeTabId = tabId;

        // Focus and fit
        const term = this.getActiveTerminal();
        if (term) {
            term.fitAddon.fit();
            term.term.focus();
        }
    }

    closeTab(tabId) {
        // Don't close last tab
        if (this.terminals.size <= 1) return;

        const termData = this.terminals.get(tabId);
        if (termData) {
            termData.term.dispose();
            this.terminals.delete(tabId);
        }

        this.container.querySelector(`.terminal-tab[data-tab-id="${tabId}"]`)?.remove();
        this.container.querySelector(`.terminal-panel[data-tab-id="${tabId}"]`)?.remove();

        // Activate another tab
        if (this.activeTabId === tabId) {
            const firstTabId = this.terminals.keys().next().value;
            if (firstTabId) this.activateTab(firstTabId);
        }
    }

    getActiveTerminal() {
        return this.terminals.get(this.activeTabId);
    }

    // ===========================================================================
    // WEBSOCKET
    // ===========================================================================

    connect() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) return;

        try {
            this.ws = new WebSocket(this.options.wsUrl);

            this.ws.onopen = () => {
                this.reconnectAttempts = 0;
                this.updateStatus('connected');
                console.log('Terminal WebSocket connected');
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleServerMessage(data);
            };

            this.ws.onclose = () => {
                this.updateStatus('disconnected');
                if (this.options.reconnect) {
                    this.scheduleReconnect();
                }
            };

            this.ws.onerror = (err) => {
                console.error('Terminal WebSocket error:', err);
                this.updateStatus('error');
            };
        } catch (err) {
            console.error('Failed to connect WebSocket:', err);
            this.updateStatus('error');
            if (this.options.reconnect) {
                this.scheduleReconnect();
            }
        }
    }

    scheduleReconnect() {
        if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
            this.updateStatus('failed');
            return;
        }

        // Exponential backoff: 1s, 2s, 4s, 8s, 16s, 32s max
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 32000);
        this.reconnectAttempts++;

        this.updateStatus(`reconnecting (${this.reconnectAttempts})`);

        this.reconnectTimer = setTimeout(() => {
            this.connect();
        }, delay);
    }

    updateStatus(status) {
        const statusEl = this.container.querySelector('.terminal-status-connection');
        if (!statusEl) return;

        const statusMap = {
            connected: { text: '● Connected', class: 'connected' },
            disconnected: { text: '○ Disconnected', class: 'disconnected' },
            reconnecting: { text: '◑ Reconnecting...', class: 'reconnecting' },
            error: { text: '✕ Error', class: 'error' },
            failed: { text: '✕ Connection Failed', class: 'error' },
        };

        const info = statusMap[status.split(' ')[0]] || statusMap.disconnected;
        statusEl.textContent = status.includes('(') ? `◑ Reconnecting ${status.split(' ')[1]}` : info.text;
        statusEl.className = `terminal-status-connection ${info.class}`;
    }

    handleServerMessage(data) {
        const termData = this.getActiveTerminal();
        if (!termData) return;

        switch (data.type) {
            case 'output':
                termData.term.write(data.data);
                break;
            case 'clear':
                termData.term.clear();
                break;
            case 'error':
                termData.term.writeln(`\x1b[31m${data.data}\x1b[0m`);
                break;
        }
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }

    // ===========================================================================
    // INPUT HANDLING
    // ===========================================================================

    handleInput(tabId, data) {
        const termData = this.terminals.get(tabId);
        if (!termData) return;

        const { term } = termData;

        // Handle special keys
        switch (data) {
            case '\r': // Enter
                this.executeCommand(tabId);
                break;
            case '\x7f': // Backspace
                if (termData.currentLine.length > 0) {
                    termData.currentLine = termData.currentLine.slice(0, -1);
                    term.write('\b \b');
                }
                break;
            case '\x1b[A': // Up arrow
                this.historyUp(tabId);
                break;
            case '\x1b[B': // Down arrow
                this.historyDown(tabId);
                break;
            case '\x03': // Ctrl+C
                termData.currentLine = '';
                term.writeln('^C');
                this.writePrompt(tabId);
                break;
            case '\x0c': // Ctrl+L
                term.clear();
                this.writePrompt(tabId);
                break;
            default:
                // Regular character
                if (data >= ' ' && data <= '~') {
                    termData.currentLine += data;
                    term.write(data);
                }
        }
    }

    executeCommand(tabId) {
        const termData = this.terminals.get(tabId);
        if (!termData) return;

        const { term, history } = termData;
        const command = termData.currentLine.trim();

        term.writeln('');

        if (command) {
            // Add to history
            if (history[history.length - 1] !== command) {
                history.push(command);
                if (history.length > 1000) history.shift();
            }
            termData.historyIndex = history.length;

            // Send to server
            this.send({ type: 'command', data: command, tabId });

            // Handle local commands
            if (command === 'clear') {
                term.clear();
            } else if (command === 'help') {
                this.showHelp(term);
            }
        }

        termData.currentLine = '';
        this.writePrompt(tabId);
        this.saveSession();
    }

    historyUp(tabId) {
        const termData = this.terminals.get(tabId);
        if (!termData || termData.history.length === 0) return;

        if (termData.historyIndex > 0) {
            termData.historyIndex--;
            this.replaceCurrentLine(tabId, termData.history[termData.historyIndex]);
        }
    }

    historyDown(tabId) {
        const termData = this.terminals.get(tabId);
        if (!termData) return;

        if (termData.historyIndex < termData.history.length - 1) {
            termData.historyIndex++;
            this.replaceCurrentLine(tabId, termData.history[termData.historyIndex]);
        } else {
            termData.historyIndex = termData.history.length;
            this.replaceCurrentLine(tabId, '');
        }
    }

    replaceCurrentLine(tabId, newLine) {
        const termData = this.terminals.get(tabId);
        if (!termData) return;

        const { term } = termData;

        // Clear current line
        term.write('\x1b[2K\r');
        this.writePromptInline(term);
        term.write(newLine);
        termData.currentLine = newLine;
    }

    writePrompt(tabId) {
        const termData = this.terminals.get(tabId);
        if (!termData) return;
        termData.term.write('\x1b[38;5;141minception\x1b[0m\x1b[38;5;245m>\x1b[0m ');
    }

    writePromptInline(term) {
        term.write('\x1b[38;5;141minception\x1b[0m\x1b[38;5;245m>\x1b[0m ');
    }

    showHelp(term) {
        term.writeln('\x1b[1mAvailable Commands:\x1b[0m');
        term.writeln('  help         Show this help message');
        term.writeln('  clear        Clear terminal');
        term.writeln('  status       Show system status');
        term.writeln('  auth         Auth management (setup, status, logout)');
        term.writeln('  ingest       Ingest content (ingest <url>)');
        term.writeln('  search       Search knowledge (search <query>)');
        term.writeln('  export       Export knowledge (export <format>)');
        term.writeln('');
        term.writeln('\x1b[1mKeyboard Shortcuts:\x1b[0m');
        term.writeln('  Ctrl+L       Clear screen');
        term.writeln('  Ctrl+C       Cancel current input');
        term.writeln('  Ctrl+F       Search terminal buffer');
        term.writeln('  ↑/↓          Navigate history');
    }

    // ===========================================================================
    // SEARCH
    // ===========================================================================

    showSearch() {
        this.container.querySelector('.terminal-search-overlay').classList.add('visible');
        this.container.querySelector('.terminal-search-input').focus();
    }

    hideSearch() {
        this.container.querySelector('.terminal-search-overlay').classList.remove('visible');
        const term = this.getActiveTerminal();
        if (term) term.term.focus();
    }

    // ===========================================================================
    // SESSION
    // ===========================================================================

    saveSession() {
        const session = {};
        this.terminals.forEach((termData, tabId) => {
            session[tabId] = {
                history: termData.history.slice(-100), // Last 100 commands
            };
        });
        localStorage.setItem('inception-terminal-session', JSON.stringify(session));
    }

    restoreSession() {
        try {
            const session = JSON.parse(localStorage.getItem('inception-terminal-session') || '{}');
            const mainTermData = this.terminals.get('main');
            if (mainTermData && session.main) {
                mainTermData.history = session.main.history || [];
                mainTermData.historyIndex = mainTermData.history.length;
            }
        } catch (e) {
            console.warn('Failed to restore terminal session:', e);
        }
    }

    // ===========================================================================
    // KEYBOARD
    // ===========================================================================

    setupKeyboard() {
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
                if (this.container.contains(document.activeElement)) {
                    e.preventDefault();
                    this.showSearch();
                }
            }
            if (e.key === 'Escape') {
                this.hideSearch();
            }
        });
    }

    // ===========================================================================
    // UTILITY
    // ===========================================================================

    fit() {
        this.terminals.forEach(termData => {
            termData.fitAddon.fit();
        });
    }

    focus() {
        const term = this.getActiveTerminal();
        if (term) term.term.focus();
    }

    dispose() {
        if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
        if (this.ws) this.ws.close();
        this.terminals.forEach(termData => termData.term.dispose());
    }
}

// =============================================================================
// CSS
// =============================================================================

const terminalCSS = `
.terminal-tabs {
  display: flex;
  background: #181825;
  border-bottom: 1px solid #313244;
}

.terminal-tabs-list {
  display: flex;
  flex: 1;
  overflow-x: auto;
}

.terminal-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: transparent;
  border: none;
  color: #a6adc8;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.terminal-tab:hover {
  background: rgba(255, 255, 255, 0.05);
}

.terminal-tab.active {
  color: #cdd6f4;
  border-bottom-color: #7c4dff;
  background: rgba(124, 77, 255, 0.1);
}

.terminal-tab-close {
  width: 16px;
  height: 16px;
  padding: 0;
  background: transparent;
  border: none;
  color: inherit;
  opacity: 0.5;
  cursor: pointer;
  border-radius: 4px;
}

.terminal-tab-close:hover {
  opacity: 1;
  background: rgba(255, 255, 255, 0.1);
}

.terminal-tab-add {
  padding: 8px 16px;
  background: transparent;
  border: none;
  color: #a6adc8;
  cursor: pointer;
  font-size: 18px;
}

.terminal-tab-add:hover {
  background: rgba(255, 255, 255, 0.05);
}

.terminal-panels {
  flex: 1;
  position: relative;
}

.terminal-panel {
  position: absolute;
  inset: 0;
  display: none;
  padding: 8px;
}

.terminal-panel.active {
  display: block;
}

.terminal-search-overlay {
  position: absolute;
  top: 8px;
  right: 8px;
  display: none;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  background: #313244;
  border-radius: 8px;
  z-index: 100;
}

.terminal-search-overlay.visible {
  display: flex;
}

.terminal-search-input {
  width: 200px;
  padding: 4px 8px;
  background: #1e1e2e;
  border: 1px solid #45475a;
  border-radius: 4px;
  color: #cdd6f4;
  outline: none;
}

.terminal-search-prev,
.terminal-search-next,
.terminal-search-close {
  width: 24px;
  height: 24px;
  padding: 0;
  background: transparent;
  border: none;
  color: #a6adc8;
  cursor: pointer;
  border-radius: 4px;
}

.terminal-search-prev:hover,
.terminal-search-next:hover,
.terminal-search-close:hover {
  background: rgba(255, 255, 255, 0.1);
}

.terminal-status {
  display: flex;
  justify-content: space-between;
  padding: 4px 12px;
  background: #181825;
  border-top: 1px solid #313244;
  font-size: 12px;
}

.terminal-status-connection.connected {
  color: #a6e3a1;
}

.terminal-status-connection.disconnected {
  color: #a6adc8;
}

.terminal-status-connection.reconnecting {
  color: #f9e2af;
}

.terminal-status-connection.error {
  color: #f38ba8;
}
`;

// Inject CSS
if (typeof document !== 'undefined') {
    const style = document.createElement('style');
    style.textContent = terminalCSS;
    document.head.appendChild(style);
}

// =============================================================================
// EXPORTS
// =============================================================================

export { InceptionTerminal };
export default InceptionTerminal;
