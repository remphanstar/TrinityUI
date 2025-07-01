// Trinity UI Preflight Test JavaScript
// Created: 2025-06-29 (Emergency Fix #4 - Missing Assets)

(function() {
    'use strict';
    
    // Trinity Preflight Test System
    window.TrinityPreflight = {
        version: '1.0.0',
        tests: [],
        results: {},
        isRunning: false,
        
        init: function() {
            console.log('🚀 Trinity Preflight Test System v' + this.version + ' initialized');
            this.setupUI();
            this.registerTests();
            this.bindEvents();
        },
        
        setupUI: function() {
            // Create main container if it doesn't exist
            if (!document.getElementById('trinity-preflight-container')) {
                const container = document.createElement('div');
                container.id = 'trinity-preflight-container';
                container.className = 'trinity-preflight';
                document.body.appendChild(container);
            }
            
            // Initialize progress bar
            this.updateProgress(0, 'Initializing Trinity Preflight System...');
        },
        
        registerTests: function() {
            // Core infrastructure tests
            this.addTest('environment', 'Environment Detection', this.testEnvironment);
            this.addTest('dependencies', 'Dependency Check', this.testDependencies);
            this.addTest('modules', 'Module Imports', this.testModules);
            this.addTest('paths', 'Path Resolution', this.testPaths);
            this.addTest('permissions', 'File Permissions', this.testPermissions);
            this.addTest('network', 'Network Connectivity', this.testNetwork);
            this.addTest('storage', 'Storage Access', this.testStorage);
            this.addTest('configuration', 'Configuration Files', this.testConfiguration);
        },
        
        addTest: function(id, name, testFunction) {
            this.tests.push({
                id: id,
                name: name,
                test: testFunction,
                status: 'pending',
                result: null,
                duration: 0
            });
        },
        
        runAllTests: function() {
            if (this.isRunning) {
                console.log('⚠️ Tests already running');
                return;
            }
            
            console.log('🧪 Starting Trinity Preflight Tests...');
            this.isRunning = true;
            this.results = {};
            
            const totalTests = this.tests.length;
            let completedTests = 0;
            
            // Run tests sequentially
            const runNextTest = (index) => {
                if (index >= totalTests) {
                    this.isRunning = false;
                    this.generateReport();
                    return;
                }
                
                const test = this.tests[index];
                this.updateProgress(
                    (completedTests / totalTests) * 100,
                    `Running ${test.name}...`
                );
                
                const startTime = Date.now();
                
                try {
                    Promise.resolve(test.test.call(this))
                        .then(result => {
                            test.status = result.success ? 'passed' : 'failed';
                            test.result = result;
                            test.duration = Date.now() - startTime;
                            this.results[test.id] = test;
                            
                            completedTests++;
                            this.updateTestCard(test.id, test.status, test.result);
                            
                            setTimeout(() => runNextTest(index + 1), 100);
                        })
                        .catch(error => {
                            test.status = 'error';
                            test.result = { success: false, message: error.message, error: error };
                            test.duration = Date.now() - startTime;
                            this.results[test.id] = test;
                            
                            completedTests++;
                            this.updateTestCard(test.id, 'error', test.result);
                            
                            setTimeout(() => runNextTest(index + 1), 100);
                        });
                } catch (error) {
                    test.status = 'error';
                    test.result = { success: false, message: error.message, error: error };
                    test.duration = Date.now() - startTime;
                    this.results[test.id] = test;
                    
                    completedTests++;
                    this.updateTestCard(test.id, 'error', test.result);
                    
                    setTimeout(() => runNextTest(index + 1), 100);
                }
            };
            
            runNextTest(0);
        },
        
        // Individual test functions
        testEnvironment: function() {
            return new Promise((resolve) => {
                const env = {
                    userAgent: navigator.userAgent,
                    platform: navigator.platform,
                    language: navigator.language,
                    cookieEnabled: navigator.cookieEnabled,
                    onLine: navigator.onLine,
                    screen: {
                        width: screen.width,
                        height: screen.height,
                        colorDepth: screen.colorDepth
                    }
                };
                
                const isSupported = env.cookieEnabled && 
                                  typeof localStorage !== 'undefined' &&
                                  typeof fetch !== 'undefined';
                
                resolve({
                    success: isSupported,
                    message: isSupported ? 'Environment is compatible' : 'Environment compatibility issues detected',
                    data: env
                });
            });
        },
        
        testDependencies: function() {
            return new Promise((resolve) => {
                const dependencies = {
                    fetch: typeof fetch !== 'undefined',
                    localStorage: typeof localStorage !== 'undefined',
                    sessionStorage: typeof sessionStorage !== 'undefined',
                    WebSocket: typeof WebSocket !== 'undefined',
                    FileReader: typeof FileReader !== 'undefined',
                    FormData: typeof FormData !== 'undefined',
                    Promise: typeof Promise !== 'undefined',
                    Map: typeof Map !== 'undefined',
                    Set: typeof Set !== 'undefined'
                };
                
                const missingDeps = Object.keys(dependencies).filter(key => !dependencies[key]);
                const success = missingDeps.length === 0;
                
                resolve({
                    success: success,
                    message: success ? 'All dependencies available' : `Missing: ${missingDeps.join(', ')}`,
                    data: dependencies
                });
            });
        },
        
        testModules: function() {
            return new Promise((resolve) => {
                const modules = {
                    Trinity: typeof window.Trinity !== 'undefined',
                    TrinityPreflight: typeof window.TrinityPreflight !== 'undefined',
                    updateTrinityStatus: typeof updateTrinityStatus === 'function',
                    updateTestCard: typeof updateTestCard === 'function'
                };
                
                const missingModules = Object.keys(modules).filter(key => !modules[key]);
                const success = missingModules.length === 0;
                
                resolve({
                    success: success,
                    message: success ? 'All modules loaded' : `Missing: ${missingModules.join(', ')}`,
                    data: modules
                });
            });
        },
        
        testPaths: function() {
            return new Promise((resolve) => {
                const paths = {
                    currentURL: window.location.href,
                    protocol: window.location.protocol,
                    host: window.location.host,
                    pathname: window.location.pathname,
                    origin: window.location.origin
                };
                
                const isValidPath = paths.protocol.startsWith('http') || paths.protocol === 'file:';
                
                resolve({
                    success: isValidPath,
                    message: isValidPath ? 'Path resolution working' : 'Invalid path configuration',
                    data: paths
                });
            });
        },
        
        testPermissions: function() {
            return new Promise((resolve) => {
                try {
                    // Test localStorage write/read
                    const testKey = 'trinity-preflight-test';
                    const testValue = Date.now().toString();
                    
                    localStorage.setItem(testKey, testValue);
                    const retrieved = localStorage.getItem(testKey);
                    localStorage.removeItem(testKey);
                    
                    const success = retrieved === testValue;
                    
                    resolve({
                        success: success,
                        message: success ? 'Storage permissions OK' : 'Storage permission denied',
                        data: { localStorage: success }
                    });
                } catch (error) {
                    resolve({
                        success: false,
                        message: 'Storage access blocked: ' + error.message,
                        data: { error: error.message }
                    });
                }
            });
        },
        
        testNetwork: function() {
            return new Promise((resolve) => {
                if (!navigator.onLine) {
                    resolve({
                        success: false,
                        message: 'No network connection detected',
                        data: { online: false }
                    });
                    return;
                }
                
                // Test basic connectivity
                const img = new Image();
                const timeout = setTimeout(() => {
                    resolve({
                        success: false,
                        message: 'Network connectivity test timed out',
                        data: { timeout: true }
                    });
                }, 5000);
                
                img.onload = () => {
                    clearTimeout(timeout);
                    resolve({
                        success: true,
                        message: 'Network connectivity confirmed',
                        data: { online: true, latency: Date.now() - startTime }
                    });
                };
                
                img.onerror = () => {
                    clearTimeout(timeout);
                    resolve({
                        success: false,
                        message: 'Network connectivity test failed',
                        data: { online: false }
                    });
                };
                
                const startTime = Date.now();
                // Use a small data URI to test without external dependency
                img.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
            });
        },
        
        testStorage: function() {
            return new Promise((resolve) => {
                try {
                    const quota = navigator.storage && navigator.storage.estimate 
                        ? navigator.storage.estimate() 
                        : Promise.resolve({ quota: 0, usage: 0 });
                    
                    quota.then(estimate => {
                        resolve({
                            success: true,
                            message: `Storage available: ${this.formatBytes(estimate.quota - estimate.usage)}`,
                            data: estimate
                        });
                    }).catch(() => {
                        resolve({
                            success: true,
                            message: 'Storage available (quota unavailable)',
                            data: { quota: 'unknown', usage: 'unknown' }
                        });
                    });
                } catch (error) {
                    resolve({
                        success: false,
                        message: 'Storage access error: ' + error.message,
                        data: { error: error.message }
                    });
                }
            });
        },
        
        testConfiguration: function() {
            return new Promise((resolve) => {
                const config = {
                    trinityVersion: window.Trinity && window.Trinity.version || 'unknown',
                    preflightVersion: this.version,
                    timestamp: new Date().toISOString(),
                    userAgent: navigator.userAgent,
                    screenResolution: `${screen.width}x${screen.height}`
                };
                
                const hasValidConfig = config.trinityVersion !== 'unknown';
                
                resolve({
                    success: hasValidConfig,
                    message: hasValidConfig ? 'Configuration loaded successfully' : 'Configuration incomplete',
                    data: config
                });
            });
        },
        
        // UI Helper functions
        updateProgress: function(percentage, message) {
            const progressFill = document.getElementById('progress-fill');
            if (progressFill) {
                progressFill.style.width = percentage + '%';
                progressFill.textContent = Math.round(percentage) + '%';
            }
            
            if (typeof updateTrinityStatus === 'function') {
                updateTrinityStatus(message, 'info');
            }
            
            console.log(`📊 Progress: ${Math.round(percentage)}% - ${message}`);
        },
        
        updateTestCard: function(testId, status, result) {
            if (typeof updateTestCard === 'function') {
                updateTestCard(testId, status, result);
            }
            
            const statusEmoji = {
                passed: '✅',
                failed: '❌', 
                error: '🚨',
                pending: '⏳'
            };
            
            console.log(`${statusEmoji[status]} Test ${testId}: ${result.message}`);
        },
        
        generateReport: function() {
            const passed = this.tests.filter(t => t.status === 'passed').length;
            const failed = this.tests.filter(t => t.status === 'failed').length;
            const errors = this.tests.filter(t => t.status === 'error').length;
            const total = this.tests.length;
            
            const report = {
                summary: {
                    total: total,
                    passed: passed,
                    failed: failed,
                    errors: errors,
                    success: (failed + errors) === 0
                },
                tests: this.results,
                timestamp: new Date().toISOString(),
                duration: this.tests.reduce((sum, test) => sum + test.duration, 0)
            };
            
            console.log('📋 Trinity Preflight Test Report:', report);
            
            if (typeof updateTrinityStatus === 'function') {
                const message = report.summary.success 
                    ? `🎉 All tests passed! (${passed}/${total})`
                    : `⚠️ Tests completed: ${passed} passed, ${failed} failed, ${errors} errors`;
                updateTrinityStatus(message, report.summary.success ? 'success' : 'warning');
            }
            
            this.updateProgress(100, 'Preflight tests completed');
            
            return report;
        },
        
        // Utility functions
        formatBytes: function(bytes, decimals = 2) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const dm = decimals < 0 ? 0 : decimals;
            const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
        },
        
        bindEvents: function() {
            // Auto-run tests when DOM is ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => {
                    setTimeout(() => this.runAllTests(), 1000);
                });
            } else {
                setTimeout(() => this.runAllTests(), 1000);
            }
        }
    };
    
    // Initialize when script loads
    window.TrinityPreflight.init();
    
    // Enhanced test UI functions
    window.initializeTestUI = function() {
        console.log('✅ Trinity Preflight Test UI initialized');
        
        // Create enhanced test grid
        const testGrid = document.getElementById('test-grid');
        if (testGrid && window.TrinityPreflight) {
            testGrid.innerHTML = window.TrinityPreflight.tests.map(test => `
                <div class="preflight-card" id="test-card-${test.id}">
                    <div class="preflight-card-title">
                        <span class="preflight-status pending" id="status-${test.id}">⏳ Pending</span>
                        ${test.name}
                    </div>
                    <div class="preflight-card-content" id="content-${test.id}">
                        Waiting to run...
                    </div>
                </div>
            `).join('');
        }
    };
    
    // Enhanced test card update function
    window.updateTestCard = function(testId, status, result) {
        const statusElement = document.getElementById(`status-${testId}`);
        const contentElement = document.getElementById(`content-${testId}`);
        
        if (statusElement) {
            const statusConfig = {
                passed: { emoji: '✅', text: 'Passed', class: 'success' },
                failed: { emoji: '❌', text: 'Failed', class: 'error' },
                error: { emoji: '🚨', text: 'Error', class: 'error' },
                pending: { emoji: '⏳', text: 'Pending', class: 'info' }
            };
            
            const config = statusConfig[status] || statusConfig.pending;
            statusElement.textContent = `${config.emoji} ${config.text}`;
            statusElement.className = `preflight-status ${config.class}`;
        }
        
        if (contentElement && result) {
            contentElement.innerHTML = `
                <div>${result.message}</div>
                ${result.data ? `<pre style="font-size:10px;margin-top:8px;opacity:0.7">${JSON.stringify(result.data, null, 2)}</pre>` : ''}
            `;
        }
    };
    
})();