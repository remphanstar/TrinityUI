/**
 * Trinity Launch Cell JavaScript Functions
 * Version: 1.0.0
 */

class TrinityLaunchManager {
    constructor() {
        this.gradioUrlFound = false;
        this.outputBuffer = [];
        this.maxOutputLines = 100;
        this.autoScroll = true;
    }

    /**
     * Format SD progress lines with appropriate styling
     */
    formatSDProgress(line) {
        line = line.trim();
        
        // Progress bars and percentages
        if (this.containsAny(line, ['%|', 'it/s', 'steps/s', '/it'])) {
            return this.createOutputLine(line, 'output-progress', '🎨');
        }
        
        // Model loading
        if (this.containsAny(line.toLowerCase(), ['loading', 'loaded', 'applying', 'initializing'])) {
            return this.createOutputLine(line, 'output-loading', '📦');
        }
        
        // Errors and exceptions
        if (this.containsAny(line.toLowerCase(), ['error', 'failed', 'exception', 'traceback', 'critical'])) {
            return this.createOutputLine(line, 'output-error', '❌');
        }
        
        // Warnings
        if (this.containsAny(line.toLowerCase(), ['warning', 'warn', 'deprecated'])) {
            return this.createOutputLine(line, 'output-warning', '⚠️');
        }
        
        // Success messages
        if (this.containsAny(line.toLowerCase(), ['startup time', 'model loaded', 'ready', 'complete', 'successful'])) {
            return this.createOutputLine(line, 'output-success', '✅');
        }
        
        // Server info
        if (this.containsAny(line.toLowerCase(), ['running on', 'local url', 'public url', 'server', 'listening'])) {
            return this.createOutputLine(line, 'output-server', '🌐');
        }
        
        // Memory and performance info
        if (this.containsAny(line.toLowerCase(), ['vram', 'memory', 'gpu', 'cuda', 'mb', 'gb'])) {
            return this.createOutputLine(line, 'output-memory', '💾');
        }
        
        // Default formatting
        return this.createOutputLine(line, 'output-default', '');
    }

    /**
     * Create formatted output line
     */
    createOutputLine(text, className, icon) {
        const iconSpan = icon ? `<span class="output-icon">${icon}</span> ` : '';
        return `<div class="output-line ${className}">${iconSpan}${this.escapeHtml(text)}</div>`;
    }

    /**
     * Check if text contains any of the keywords
     */
    containsAny(text, keywords) {
        return keywords.some(keyword => text.includes(keyword));
    }

    /**
     * Escape HTML characters
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Extract Gradio URL from line
     */
    extractGradioUrl(line) {
        const patterns = [
            /Running on public URL:\s*(https?:\/\/[a-z0-9]+\.gradio\.live)/i,
            /(https?:\/\/[a-z0-9]+\.gradio\.live)/i,
            /(https?:\/\/[a-z0-9\-]+\.gradio\.app)/i
        ];
        
        for (const pattern of patterns) {
            const match = line.match(pattern);
            if (match) {
                return match[1];
            }
        }
        return null;
    }

    /**
     * Create Gradio announcement HTML
     */
    createGradioAnnouncement(url) {
        return `
            <div class="gradio-announcement">
                <h2>🎉 GRADIO URL DETECTED!</h2>
                <p style="margin: 5px 0; font-size: 16px;">Your WebUI is now accessible:</p>
                <a href="${url}" target="_blank" class="gradio-link">
                    🚀 Open WebUI: ${url}
                </a>
                <div style="margin-top: 10px; font-size: 14px; opacity: 0.9;">
                    Click the link above to access your Stable Diffusion WebUI
                </div>
            </div>
        `;
    }

    /**
     * Update status widget
     */
    updateStatus(message, type = 'info') {
        const statusClasses = {
            'starting': 'status-starting',
            'ready': 'status-ready',
            'error': 'status-error',
            'warning': 'status-warning',
            'stopped': 'status-stopped'
        };
        
        const className = statusClasses[type] || 'status-starting';
        return `<div class="${className}">${message}</div>`;
    }

    /**
     * Create launch command display
     */
    createLaunchCommandDisplay(command, workingDir) {
        return `
            <div class="launch-command">
                <strong>🔧 Launch Command:</strong><br>
                <code>${this.escapeHtml(command)}</code><br>
                <strong>📁 Working Directory:</strong> ${this.escapeHtml(workingDir)}
            </div>
        `;
    }

    /**
     * Auto-scroll output widget to bottom
     */
    autoScrollToBottom(outputElement) {
        if (this.autoScroll && outputElement) {
            outputElement.scrollTop = outputElement.scrollHeight;
        }
    }

    /**
     * Manage output buffer to prevent memory issues
     */
    manageOutputBuffer(outputElement) {
        if (this.outputBuffer.length > this.maxOutputLines) {
            // Remove oldest lines
            const linesToRemove = this.outputBuffer.length - this.maxOutputLines;
            this.outputBuffer.splice(0, linesToRemove);
            
            // Update DOM
            const children = outputElement.children;
            for (let i = 0; i < linesToRemove && children.length > 0; i++) {
                outputElement.removeChild(children[0]);
            }
        }
    }

    /**
     * Add line to output with management
     */
    addOutputLine(outputElement, formattedLine) {
        this.outputBuffer.push(formattedLine);
        
        const lineDiv = document.createElement('div');
        lineDiv.innerHTML = formattedLine;
        outputElement.appendChild(lineDiv);
        
        this.manageOutputBuffer(outputElement);
        this.autoScrollToBottom(outputElement);
    }

    /**
     * Toggle auto-scroll
     */
    toggleAutoScroll() {
        this.autoScroll = !this.autoScroll;
        return this.autoScroll;
    }

    /**
     * Clear output buffer and display
     */
    clearOutput(outputElement) {
        this.outputBuffer = [];
        if (outputElement) {
            outputElement.innerHTML = '';
        }
    }

    /**
     * Create completion summary
     */
    createCompletionSummary(success = true, message = '') {
        const icon = success ? '🎉' : '⚠️';
        const bgClass = success ? 'completion-summary' : 'status-warning';
        
        return `
            <div class="${bgClass}">
                <h3>${icon} TRINITY WEBUI LAUNCH COMPLETE</h3>
                <p>${message || (success ? 'WebUI launched successfully!' : 'Launch completed with warnings')}</p>
                <div style="margin-top: 10px; font-size: 14px; opacity: 0.9;">
                    💡 If you need to restart, simply run this cell again
                </div>
            </div>
        `;
    }
}

// Initialize global instance
window.trinityLaunchManager = new TrinityLaunchManager();

// Utility function to load Trinity CSS
function loadTrinityCSS() {
    const cssUrl = 'https://raw.githubusercontent.com/remphanstar/TrinityUI/main/CSS/trinity-launch.css';
    
    // Check if already loaded
    if (document.querySelector(`link[href="${cssUrl}"]`)) {
        return;
    }
    
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.type = 'text/css';
    link.href = cssUrl;
    document.head.appendChild(link);
}

// Auto-load CSS when script loads
loadTrinityCSS();

console.log('Trinity Launch Manager loaded successfully');
