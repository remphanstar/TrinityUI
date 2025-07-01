// --- Trinity HUD JavaScript Logic ---
class TrinityHUD {
    constructor(config) {
        this.version = config.version || '1.1.0';
        this.logContainer = null;
        this.isVerbose = true;
        this.logBuffer = [];
        this.init();
    }

    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.logContainer = document.getElementById('trinity-hud-logs');
            this.bindEvents();
            console.log('Trinity HUD Initialized');
        });
    }

    bindEvents() {
        document.getElementById('trinity-hud-toggle-verbose')?.addEventListener('click', () => this.toggleVerbose());
        document.getElementById('trinity-hud-export-logs')?.addEventListener('click', () => this.exportLogs());
        document.getElementById('trinity-hud-copy-logs')?.addEventListener('click', () => this.copyLogs());
    }

    addLog(timestamp, level, component, message) {
        const logEntry = { timestamp, level, component, message };
        this.logBuffer.push(logEntry);

        if (!this.logContainer) return;

        const entryDiv = document.createElement('div');
        entryDiv.className = `trinity-hud-log-entry trinity-log-${level}`;
        entryDiv.dataset.level = level;

        const timeSpan = document.createElement('span');
        timeSpan.className = 'trinity-hud-log-timestamp';
        timeSpan.textContent = `[${timestamp.split(' ')[1]}]`;

        const levelSpan = document.createElement('span');
        levelSpan.className = 'trinity-hud-log-level';
        levelSpan.textContent = `[${level}]`;

        const msgSpan = document.createElement('span');
        msgSpan.className = 'trinity-hud-log-message';
        msgSpan.textContent = `[${component}] ${message}`;
        
        entryDiv.appendChild(timeSpan);
        entryDiv.appendChild(levelSpan);
        entryDiv.appendChild(msgSpan);
        
        this.logContainer.appendChild(entryDiv);
        this.logContainer.scrollTop = this.logContainer.scrollHeight;

        this.applyVerboseFilter();
    }

    toggleVerbose() {
        this.isVerbose = !this.isVerbose;
        const button = document.getElementById('trinity-hud-toggle-verbose');
        if (button) {
            button.innerHTML = this.isVerbose ? '🙈 Hide Debug' : '🐵 Show Debug';
            button.style.background = this.isVerbose ? '#4f46e5' : '#334155';
        }
        this.applyVerboseFilter();
    }

    applyVerboseFilter() {
        if (!this.logContainer) return;
        const entries = this.logContainer.querySelectorAll('.trinity-hud-log-entry');
        entries.forEach(entry => {
            if (this.isVerbose) {
                entry.style.display = 'flex';
            } else {
                const level = entry.dataset.level;
                if (level === 'INFO' || level === 'SUCCESS' || level === 'ERROR' || level === 'WARNING') {
                    entry.style.display = 'flex';
                } else {
                    entry.style.display = 'none';
                }
            }
        });
        this.logContainer.scrollTop = this.logContainer.scrollHeight;
    }

    getFormattedLogs() {
        return this.logBuffer.map(log => `[${log.timestamp}] [${log.level}] [${log.component}] ${log.message}`).join('\\n');
    }

    exportLogs() {
        const logText = this.getFormattedLogs();
        const blob = new Blob([logText], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `trinity-cell1-logs-${new Date().toISOString()}.log`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    copyLogs() {
        const logText = this.getFormattedLogs();
        navigator.clipboard.writeText(logText).then(() => {
            alert('Logs copied to clipboard!');
        }, (err) => {
            alert('Failed to copy logs: ' + err);
        });
    }
}

// Instantiate the HUD controller
const trinityHUD = new TrinityHUD({ version: '1.1.0' });
