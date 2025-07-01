// Trinity Debug UI JavaScript
// Created: 2025-06-29 (Emergency Fix #4 - Missing Assets)
// Updated: 2025-06-30 (Verbose Debugging Toggle Restoration)

(function() {
    'use strict';
    
    // Trinity Debug System with Verbose Logging
    window.TrinityDebug = {
        version: '1.0.0',
        isActive: false,
        verboseMode: true, // Default to verbose for debugging
        logs: [],
        verboseLogs: [],
        maxLogs: 500,
        updateInterval: null,
        
        init: function() {
            console.log('🔧 Trinity Debug System v' + this.version + ' initialized');
            this.createUI();
            this.createVerboseUI();
            this.bindEvents();
            this.startMonitoring();
            this.interceptConsole();
        },
        
        createVerboseUI: function() {
            // Create verbose toggle button
            const verboseToggle = document.createElement('button');
            verboseToggle.id = 'trinity-verbose-toggle';
            verboseToggle.className = 'trinity-verbose-toggle' + (this.verboseMode ? ' active' : '');
            verboseToggle.innerHTML = '🔍 VERBOSE ' + (this.verboseMode ? 'ON' : 'OFF');
            verboseToggle.title = 'Toggle Verbose Debug Output';
            verboseToggle.onclick = () => this.toggleVerbose();
            document.body.appendChild(verboseToggle);
            
            // Create verbose output panel
            const verbosePanel = document.createElement('div');
            verbosePanel.id = 'trinity-verbose-output';
            verbosePanel.className = 'trinity-verbose-output' + (this.verboseMode ? ' active' : '');
            verbosePanel.innerHTML = '<div style="font-weight: bold; border-bottom: 1px solid #333; padding-bottom: 5px; margin-bottom: 10px;">🔍 Trinity Verbose Debug Output</div>';
            document.body.appendChild(verbosePanel);
        },
        
        toggleVerbose: function() {
            this.verboseMode = !this.verboseMode;
            const toggle = document.getElementById('trinity-verbose-toggle');
            const panel = document.getElementById('trinity-verbose-output');
            
            if (this.verboseMode) {
                toggle.className = 'trinity-verbose-toggle active';
                toggle.innerHTML = '🔍 VERBOSE ON';
                panel.className = 'trinity-verbose-output active';
                this.logVerbose('🔍 Verbose debugging ENABLED', 'success');
            } else {
                toggle.className = 'trinity-verbose-toggle';
                toggle.innerHTML = '🔍 VERBOSE OFF';
                panel.className = 'trinity-verbose-output';
                this.logVerbose('🔍 Verbose debugging DISABLED', 'warning');
            }
        },
        
        logVerbose: function(message, type = 'info') {
            if (!this.verboseMode) return;
            
            const timestamp = new Date().toLocaleTimeString();
            const verbosePanel = document.getElementById('trinity-verbose-output');
            
            if (verbosePanel) {
                const line = document.createElement('div');
                line.className = 'trinity-verbose-line ' + type;
                line.innerHTML = `[${timestamp}] ${message}`;
                verbosePanel.appendChild(line);
                
                // Auto-scroll to bottom
                verbosePanel.scrollTop = verbosePanel.scrollHeight;
                
                // Keep only last 1000 lines
                const lines = verbosePanel.getElementsByClassName('trinity-verbose-line');
                if (lines.length > 1000) {
                    lines[0].remove();
                }
            }
            
            // Also log to console for additional debugging
            console.log(`[Trinity Verbose] ${message}`);
        },
        
        interceptConsole: function() {
            // Intercept console.log to capture all output
            const originalLog = console.log;
            const originalError = console.error;
            const originalWarn = console.warn;
            
            console.log = (...args) => {
                originalLog.apply(console, args);
                if (this.verboseMode) {
                    this.logVerbose(args.join(' '), 'info');
                }
            };
            
            console.error = (...args) => {
                originalError.apply(console, args);
                if (this.verboseMode) {
                    this.logVerbose('ERROR: ' + args.join(' '), 'error');
                }
            };
            
            console.warn = (...args) => {
                originalWarn.apply(console, args);
                if (this.verboseMode) {
                    this.logVerbose('WARNING: ' + args.join(' '), 'warning');
                }
            };
        },
        
        init: function() {
            console.log('🔧 Trinity Debug System v' + this.version + ' initialized');
            this.createUI();
            this.bindEvents();
            this.startMonitoring();
        },
        
        createUI: function() {
            // Create debug toggle button
            const toggle = document.createElement('button');
            toggle.id = 'trinity-debug-toggle';
            toggle.className = 'trinity-debug-toggle';
            toggle.innerHTML = '🔧';
            toggle.title = 'Toggle Trinity Debug Panel';
            toggle.onclick = () => this.toggle();
            document.body.appendChild(toggle);
            
            // Create debug panel
            const panel = document.createElement('div');
            panel.id = 'trinity-debug-panel';
            panel.className = 'trinity-debug';
            panel.innerHTML = this.getDebugPanelHTML();
            document.body.appendChild(panel);
            
            this.updateDebugInfo();
        },
        
        toggle: function() {
            this.isActive = !this.isActive;
            const panel = document.getElementById('trinity-debug-panel');
            if (panel) {
                panel.className = 'trinity-debug' + (this.isActive ? ' active' : '');
            }
        },
        
        hide: function() {
            this.isActive = false;
            const panel = document.getElementById('trinity-debug-panel');
            if (panel) {
                panel.className = 'trinity-debug';
            }
        },
        
        clearLogs: function() {
            this.logs = [];
            this.verboseLogs = [];
            const verbosePanel = document.getElementById('trinity-verbose-output');
            if (verbosePanel) {
                verbosePanel.innerHTML = '<div style="font-weight: bold; border-bottom: 1px solid #333; padding-bottom: 5px; margin-bottom: 10px;">🔍 Trinity Verbose Debug Output (Cleared)</div>';
            }
            this.logVerbose('Debug logs cleared', 'info');
        },
        
        exportLogs: function() {
            const logs = this.verboseLogs.slice(-100); // Last 100 logs
            const logText = logs.join('\n');
            const blob = new Blob([logText], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'trinity-debug-logs.txt';
            a.click();
            URL.revokeObjectURL(url);
            this.logVerbose('Debug logs exported', 'success');
        },
        
        getDebugPanelHTML: function() {
            return `
                <div class="trinity-debug-header">
                    <div class="trinity-debug-title">Trinity Debug v${this.version}</div>
                    <button class="trinity-debug-close" onclick="TrinityDebug.hide()">×</button>
                </div>
                <div class="trinity-debug-content">
                    <div class="trinity-debug-controls">
                        <button class="trinity-debug-button" onclick="TrinityDebug.clearLogs()">Clear Logs</button>
                        <button class="trinity-debug-button" onclick="TrinityDebug.exportLogs()">Export</button>
                        <button class="trinity-debug-button" onclick="TrinityDebug.toggleVerbose()">Toggle Verbose</button>
                    </div>
                    <div class="trinity-debug-stats" id="trinity-debug-stats">
                        <div>Status: <span id="trinity-status">Initializing...</span></div>
                        <div>Version: <span>${this.version}</span></div>
                        <div>Logs: <span id="trinity-log-count">0</span></div>
                    </div>
                    <div class="trinity-debug-logs" id="trinity-debug-logs">
                        <div class="trinity-debug-log">System initialized</div>
                    </div>
                </div>
            `;
        },
        
        updateDebugInfo: function() {
            const statusEl = document.getElementById('trinity-status');
            const logCountEl = document.getElementById('trinity-log-count');
            
            if (statusEl) {
                statusEl.textContent = this.verboseMode ? 'Verbose Mode' : 'Normal Mode';
            }
            
            if (logCountEl) {
                logCountEl.textContent = this.verboseLogs.length;
            }
        },
        
        startMonitoring: function() {
            // Monitor system status every 5 seconds
            this.updateInterval = setInterval(() => {
                this.updateDebugInfo();
            }, 5000);
        },
        
        bindEvents: function() {
            // Add keyboard shortcuts
            document.addEventListener('keydown', (e) => {
                // Ctrl+Shift+D to toggle debug panel
                if (e.ctrlKey && e.shiftKey && e.key === 'D') {
                    e.preventDefault();
                    this.toggle();
                }
                
                // Ctrl+Shift+V to toggle verbose mode
                if (e.ctrlKey && e.shiftKey && e.key === 'V') {
                    e.preventDefault();
                    this.toggleVerbose();
                }
            });
        }
    };
    
    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(() => window.TrinityDebug.init(), 100);
        });
    } else {
        setTimeout(() => window.TrinityDebug.init(), 100);
    }
    
    // Global utility functions
    window.updateTrinityStatus = function(message, type = 'info') {
        if (window.TrinityDebug && window.TrinityDebug.logVerbose) {
            window.TrinityDebug.logVerbose(message, type);
        }
        console.log(`[Trinity Status] ${message}`);
    };
    
    window.initializeTestUI = function() {
        console.log('✅ Test UI initialized');
        if (window.TrinityDebug) {
            window.TrinityDebug.logVerbose('Test UI system initialized', 'success');
        }
    };
    
    window.initializeTrinityUI = function() {
        console.log('✅ Trinity UI initialized');
        if (window.TrinityDebug) {
            window.TrinityDebug.logVerbose('Trinity UI system initialized', 'success');
        }
    };
    
})();