// ================================
// LAPLACIAN - AI CODE ASSISTANT
// by Perfionix AI
// Interactive JavaScript
// ================================

class LaplacianAssistant {
    constructor() {
        this.currentView = 'chat';
        this.notes = [];
        this.tasks = [];
        this.reminders = [];
        this.dociqDocuments = [];
        this.viziqCharts = [];
        this.viziqData = null;
        this.currentModel = 'gpt';

        // Generation control state
        this.isGenerating = false;
        this.isPaused = false;
        this.isStopped = false;
        this.pauseResolve = null;
        this.currentGenerationText = '';
        this.currentGenerationIndex = 0;

        // Follow-up suggestion chips state
        this.pendingSuggestions = [];

        // Apigee mode state
        this.apigeeMode = false;

        // Voice input/output state
        this.isListening = false;
        this.voiceMode = false;  // persistent voice mode state
        this.recognition = null;
        this.ttsAudio = null;

        this.init();
    }

    init() {
        this.setupNavigation();
        this.setupMobileMenu();
        this.setupSidebarToggle();
        this.setupChat();
        this.setupModelSelector();
        this.setupApigeeToggle();
        this.setupTasks();
        this.setupNotes();
        this.setupReminders();
        this.setupDocIQ();
        this.setupUploadSectionToggle();
        this.setupVizIQ();
        this.setupVoiceInput();
        this.setupClock();
        this.setupChatHistory();
        this.loadData();
        this.loadModels();
    }

    // ================================
    // NAVIGATION
    // ================================

    setupNavigation() {
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.addEventListener('click', () => {
                const view = item.dataset.view;
                this.switchView(view);
                // Close mobile menu when navigating
                this.closeMobileMenu();
            });
        });
    }

    switchView(viewName) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.view === viewName);
        });

        // Update views
        document.querySelectorAll('.view').forEach(view => {
            view.classList.toggle('active', view.id === `${viewName}-view`);
        });

        this.currentView = viewName;

        // Update mobile view indicator
        this.updateMobileViewIndicator(viewName);
    }

    // ================================
    // MOBILE MENU
    // ================================

    setupMobileMenu() {
        const menuBtn = document.getElementById('hamburger-menu');
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');

        if (menuBtn) {
            menuBtn.addEventListener('click', () => {
                this.toggleMobileMenu();
            });
        }

        if (overlay) {
            overlay.addEventListener('click', () => {
                this.closeMobileMenu();
            });
        }

        // Close menu on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeMobileMenu();
            }
        });

        // Handle resize - close menu when switching to desktop
        window.addEventListener('resize', () => {
            if (window.innerWidth > 768) {
                this.closeMobileMenu();
            }
        });

        // Update initial view indicator
        this.updateMobileViewIndicator(this.currentView);
    }

    toggleMobileMenu() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        const menuBtn = document.getElementById('hamburger-menu');

        if (sidebar && overlay) {
            sidebar.classList.toggle('active');
            overlay.classList.toggle('active');
            if (menuBtn) {
                menuBtn.classList.toggle('active');
            }
            document.body.style.overflow = sidebar.classList.contains('active') ? 'hidden' : '';
        }
    }

    closeMobileMenu() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        const menuBtn = document.getElementById('hamburger-menu');

        if (sidebar && overlay) {
            sidebar.classList.remove('active');
            overlay.classList.remove('active');
            if (menuBtn) {
                menuBtn.classList.remove('active');
            }
            document.body.style.overflow = '';
        }
    }

    updateMobileViewIndicator(viewName) {
        const indicator = document.getElementById('mobile-view-indicator');
        if (indicator) {
            const viewLabels = {
                'chat': 'Chat',
                'tasks': 'Tasks',
                'notes': 'Notes',
                'reminders': 'Reminders',
                'dociq': 'DocIQ',
                'viziq': 'VizIQ'
            };
            indicator.textContent = viewLabels[viewName] || viewName;
        }
    }

    // ================================
    // SIDEBAR TOGGLE
    // ================================

    setupSidebarToggle() {
        const toggleBtn = document.getElementById('sidebar-toggle');
        const showBtn = document.getElementById('sidebar-show-btn');
        const sidebar = document.getElementById('sidebar');

        // Load saved state from localStorage
        const isSidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        if (isSidebarCollapsed) {
            sidebar.classList.add('collapsed');
            showBtn.classList.add('visible');
        }

        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                this.toggleSidebar();
            });
        }

        if (showBtn) {
            showBtn.addEventListener('click', () => {
                this.showSidebar();
            });
        }
    }

    toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const showBtn = document.getElementById('sidebar-show-btn');

        if (sidebar) {
            sidebar.classList.add('collapsed');
            if (showBtn) {
                setTimeout(() => {
                    showBtn.classList.add('visible');
                }, 150);
            }
            localStorage.setItem('sidebarCollapsed', 'true');
        }
    }

    showSidebar() {
        const sidebar = document.getElementById('sidebar');
        const showBtn = document.getElementById('sidebar-show-btn');

        if (showBtn) {
            showBtn.classList.remove('visible');
        }
        if (sidebar) {
            setTimeout(() => {
                sidebar.classList.remove('collapsed');
            }, 50);
            localStorage.setItem('sidebarCollapsed', 'false');
        }
    }

    // ================================
    // UPLOAD SECTION TOGGLE
    // ================================

    setupUploadSectionToggle() {
        const closeBtn = document.getElementById('dociq-close-btn');
        const showBtn = document.getElementById('dociq-show-btn');
        const section = document.getElementById('dociq-upload-section');

        if (closeBtn && section) {
            closeBtn.addEventListener('click', () => {
                section.classList.add('collapsed');
            });
        }

        if (showBtn && section) {
            showBtn.addEventListener('click', () => {
                section.classList.remove('collapsed');
            });
        }
    }

    // ================================
    // CHAT FUNCTIONALITY
    // ================================

    setupChat() {
        const input = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-message');
        const resetBtn = document.getElementById('reset-chat');
        const searchBtn = document.getElementById('web-search');
        const voiceBtn = document.getElementById('voice-toggle');

        // Generation control buttons
        const pauseBtn = document.getElementById('pause-generation');
        const continueBtn = document.getElementById('continue-generation');
        const stopBtn = document.getElementById('stop-generation');

        sendBtn.addEventListener('click', () => this.sendMessage());
        searchBtn.addEventListener('click', () => this.webSearch());

        // Voice input buttons
        const mainVoiceBtn = document.getElementById('voice-toggle');
        if (mainVoiceBtn) {
            mainVoiceBtn.addEventListener('click', () => this.toggleVoiceInput());
        }

        // Generation control event listeners
        if (pauseBtn) {
            pauseBtn.addEventListener('click', () => this.pauseGeneration());
        }
        if (continueBtn) {
            continueBtn.addEventListener('click', () => this.continueGeneration());
        }
        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stopGeneration());
        }

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
            // Ctrl+Enter for web search
            if (e.key === 'Enter' && e.ctrlKey) {
                e.preventDefault();
                this.webSearch();
            }
        });

        // Auto-resize textarea
        input.addEventListener('input', () => {
            input.style.height = 'auto';
            input.style.height = input.scrollHeight + 'px';
        });

        resetBtn.addEventListener('click', () => this.resetChat());
    }

    // ================================
    // GENERATION CONTROL
    // ================================

    showGenerationControls() {
        const controls = document.getElementById('generation-controls');
        const pauseBtn = document.getElementById('pause-generation');
        const continueBtn = document.getElementById('continue-generation');

        if (controls) {
            controls.classList.add('visible');
            // Reset button states
            pauseBtn.style.display = 'flex';
            continueBtn.style.display = 'none';
        }
    }

    hideGenerationControls() {
        const controls = document.getElementById('generation-controls');
        if (controls) {
            controls.classList.remove('visible');
        }
    }

    pauseGeneration() {
        if (this.isGenerating && !this.isPaused) {
            this.isPaused = true;

            const pauseBtn = document.getElementById('pause-generation');
            const continueBtn = document.getElementById('continue-generation');

            pauseBtn.style.display = 'none';
            continueBtn.style.display = 'flex';

            // Show toast notification
            if (typeof toastManager !== 'undefined') {
                toastManager.info('Generation paused', 2000);
            }
        }
    }

    continueGeneration() {
        if (this.isGenerating && this.isPaused) {
            this.isPaused = false;

            const pauseBtn = document.getElementById('pause-generation');
            const continueBtn = document.getElementById('continue-generation');

            pauseBtn.style.display = 'flex';
            continueBtn.style.display = 'none';

            // Resume the paused generation
            if (this.pauseResolve) {
                this.pauseResolve();
                this.pauseResolve = null;
            }

            // Show toast notification
            if (typeof toastManager !== 'undefined') {
                toastManager.success('Generation resumed', 2000);
            }
        }
    }

    stopGeneration() {
        if (this.isGenerating) {
            this.isStopped = true;
            this.isPaused = false;

            // Clear pending suggestions so stopped responses show no chips
            this.pendingSuggestions = [];

            // If paused, resolve to let it exit
            if (this.pauseResolve) {
                this.pauseResolve();
                this.pauseResolve = null;
            }

            this.hideGenerationControls();

            // Show toast notification
            if (typeof toastManager !== 'undefined') {
                toastManager.warning('Generation stopped', 2000);
            }
        }
    }

    async waitIfPaused() {
        if (this.isPaused && !this.isStopped) {
            return new Promise(resolve => {
                this.pauseResolve = resolve;
            });
        }
    }

    // Show Coming Soon Popup
    showComingSoonPopup(featureName) {
        // Remove existing popup if any
        const existingPopup = document.querySelector('.coming-soon-popup');
        if (existingPopup) {
            existingPopup.remove();
        }

        // Create popup
        const popup = document.createElement('div');
        popup.className = 'coming-soon-popup';
        popup.innerHTML = `
            <div class="coming-soon-content">
                <div class="coming-soon-icon">🚀</div>
                <h3>Coming Soon!</h3>
                <p><strong>${featureName}</strong> feature is under development.</p>
                <p class="coming-soon-sub">Stay tuned for updates!</p>
                <button class="coming-soon-close">OK</button>
            </div>
        `;

        document.body.appendChild(popup);

        // Close button handler
        popup.querySelector('.coming-soon-close').addEventListener('click', () => {
            popup.classList.add('fade-out');
            setTimeout(() => popup.remove(), 300);
        });

        // Close on backdrop click
        popup.addEventListener('click', (e) => {
            if (e.target === popup) {
                popup.classList.add('fade-out');
                setTimeout(() => popup.remove(), 300);
            }
        });

        // Auto close after 3 seconds
        setTimeout(() => {
            if (popup.parentNode) {
                popup.classList.add('fade-out');
                setTimeout(() => popup.remove(), 300);
            }
        }, 3000);
    }

    // ================================
    // MODEL SELECTOR
    // ================================

    setupModelSelector() {
        const selectorBtn = document.getElementById('model-selector-btn');
        const selector = document.getElementById('model-selector');
        const dropdown = document.getElementById('model-dropdown');
        const modelOptions = document.querySelectorAll('.model-option');

        // Toggle dropdown
        selectorBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            selector.classList.toggle('active');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!selector.contains(e.target)) {
                selector.classList.remove('active');
            }
        });

        // Handle model selection
        modelOptions.forEach(option => {
            option.addEventListener('click', async () => {
                const modelId = option.dataset.model;
                if (option.classList.contains('unavailable')) {
                    return;
                }
                await this.selectModel(modelId);
                selector.classList.remove('active');
            });
        });
    }

    async loadModels() {
        try {
            const response = await fetch('/api/models');
            const data = await response.json();

            if (data.models) {
                this.updateModelUI(data.models, data.current);
            }
        } catch (error) {
            console.error('Failed to load models:', error);
        }
    }

    async selectModel(modelId) {
        try {
            const response = await fetch('/api/models/select', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ model: modelId })
            });

            const data = await response.json();

            if (data.success) {
                this.currentModel = modelId;
                this.updateModelUI(null, modelId);
                this.showModelSwitchNotification(data.name);
            } else {
                alert(data.error || 'Failed to switch model');
            }
        } catch (error) {
            console.error('Failed to select model:', error);
            alert('Failed to switch model. Please try again.');
        }
    }

    updateModelUI(models, currentModel) {
        // Update button text
        const modelNameSpan = document.getElementById('current-model-name');
        const modelOptions = document.querySelectorAll('.model-option');

        // Determine display name based on model ID
        let displayName = 'LAPLACIAN Core';
        if (currentModel === 'gemini') displayName = 'LAPLACIAN Lite';
        else if (currentModel === 'coder') displayName = 'LAPLACIAN Coder';
        else if (currentModel === 'max') displayName = 'LAPLACIAN Max';

        if (models) {
            const activeModel = models.find(m => m.id === currentModel);
            if (activeModel) {
                displayName = activeModel.name;
            }

            // Update availability and names from server
            models.forEach(model => {
                const option = document.querySelector(`.model-option[data-model="${model.id}"]`);
                if (option) {
                    // Update availability
                    if (!model.available) {
                        option.classList.add('unavailable');
                        // Add unavailable text
                        const descSpan = option.querySelector('.model-option-desc');
                        if (descSpan && !descSpan.textContent.includes('Unavailable')) {
                            descSpan.textContent = '(Unavailable)';
                        }
                    } else {
                        option.classList.remove('unavailable');
                    }
                }
            });
        }

        modelNameSpan.textContent = displayName;
        this.currentModel = currentModel;

        // Update active state
        modelOptions.forEach(option => {
            const isActive = option.dataset.model === currentModel;
            option.classList.toggle('active', isActive);
        });
    }

    showModelSwitchNotification(modelName) {
        // Add a system message to chat indicating model switch
        const messagesContainer = document.getElementById('chat-messages');
        const notificationDiv = document.createElement('div');
        notificationDiv.className = 'model-switch-notification';
        notificationDiv.innerHTML = `
            <span class="notification-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"></path>
                    <path d="M12 16v-4M12 8h.01"></path>
                </svg>
            </span>
            <span>Switched to <strong>${modelName}</strong></span>
        `;
        messagesContainer.appendChild(notificationDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Remove notification after 3 seconds
        setTimeout(() => {
            notificationDiv.classList.add('fade-out');
            setTimeout(() => notificationDiv.remove(), 300);
        }, 3000);
    }

    // ================================
    // APIGEE MODE
    // ================================

    setupApigeeToggle() {
        const toggleBtn = document.getElementById('apigee-toggle-btn');
        const toggle = document.getElementById('apigee-toggle');

        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                this.toggleApigeeMode();
            });
        }
    }

    toggleApigeeMode() {
        this.apigeeMode = !this.apigeeMode;

        const toggle = document.getElementById('apigee-toggle');
        const status = document.getElementById('apigee-status');
        const input = document.getElementById('chat-input');

        if (this.apigeeMode) {
            toggle.classList.add('active');
            status.textContent = 'ON';
            input.placeholder = 'Describe the API proxy you want to create...';
            this.showApigeeWelcome();

            // Show toast notification
            if (typeof toastManager !== 'undefined') {
                toastManager.success('Apigee Mode enabled', 2000);
            }
        } else {
            toggle.classList.remove('active');
            status.textContent = 'OFF';
            input.placeholder = 'Ask me anything...';

            // Remove the apigee welcome card if it exists
            const welcomeMsg = document.querySelector('.apigee-mode-message');
            if (welcomeMsg) {
                welcomeMsg.remove();
            }

            // Show toast notification
            if (typeof toastManager !== 'undefined') {
                toastManager.info('Apigee Mode disabled', 2000);
            }
        }
    }

    showApigeeWelcome() {
        const messagesContainer = document.getElementById('chat-messages');
        const welcomeDiv = document.createElement('div');
        welcomeDiv.className = 'message assistant apigee-mode-message';
        welcomeDiv.innerHTML = `
            <div class="message-avatar ai-avatar">
                <div class="ai-icon">
                    <div class="ai-core"></div>
                    <div class="ai-ring"></div>
                    <div class="ai-particles">
                        <span></span><span></span><span></span><span></span>
                    </div>
                </div>
            </div>
            <div class="message-content">
                <div class="apigee-welcome">
                    <h4>Apigee Proxy Generator Active</h4>
                    <p>Describe the API proxy you want to create and I'll generate a ready-to-deploy Apigee bundle.</p>
                    <ul>
                        <li>Specify a <strong>proxy name</strong> (e.g., <code>weather-api</code>)</li>
                        <li>Include the <strong>target domain</strong> (e.g., <code>api.weather.com</code>)</li>
                        <li>Optionally add <strong>endpoint path</strong> (e.g., <code>/v1/forecast</code>)</li>
                    </ul>
                    <p style="margin-top: 12px; color: var(--text-muted); font-size: 0.85rem;">
                        Example: "Create a proxy named weather-api for api.weather.com with /forecast endpoint"
                    </p>
                </div>
                <span class="message-time">${this.formatTime(new Date())}</span>
            </div>
        `;
        messagesContainer.appendChild(welcomeDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    async sendApigeeRequest(message) {
        // Add user message to UI
        this.addMessageToUI(message, 'user');

        const input = document.getElementById('chat-input');
        input.value = '';
        input.style.height = 'auto';

        // Show typing indicator
        this.showTypingIndicator('Generating Apigee bundle...');

        try {
            const response = await fetch('/api/apigee/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message })
            });

            this.removeTypingIndicator();

            if (response.ok) {
                // Get the blob
                const blob = await response.blob();
                const contentDisposition = response.headers.get('Content-Disposition');
                let filename = 'apigee-bundle.zip';

                if (contentDisposition) {
                    const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                    if (match && match[1]) {
                        filename = match[1].replace(/['"]/g, '');
                    }
                }

                // Trigger download
                this.downloadBlob(blob, filename);

                // Show success message
                this.showApigeeSuccessMessage(filename);
            } else {
                const data = await response.json();

                if (data.needs_confirmation) {
                    // Show partial extraction info
                    this.showApigeeConfirmation(data.extracted, data.error);
                } else {
                    // Show error with tips
                    this.showApigeeError(data.error, data.tips);
                }
            }
        } catch (error) {
            this.removeTypingIndicator();
            this.addMessageToUI('Connection error. Please make sure the server is running.', 'assistant');
        }
    }

    downloadBlob(blob, filename) {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    showApigeeSuccessMessage(filename) {
        const messagesContainer = document.getElementById('chat-messages');
        const successDiv = document.createElement('div');
        successDiv.className = 'message assistant';
        successDiv.innerHTML = `
            <div class="message-avatar ai-avatar">
                <div class="ai-icon">
                    <div class="ai-core"></div>
                    <div class="ai-ring"></div>
                    <div class="ai-particles">
                        <span></span><span></span><span></span><span></span>
                    </div>
                </div>
            </div>
            <div class="message-content">
                <div class="apigee-success">
                    <h4>Apigee Bundle Generated Successfully!</h4>
                    <p>Your proxy bundle has been downloaded.</p>
                    <div class="bundle-info">
                        <div class="label">Downloaded File</div>
                        <div class="value">${filename}</div>
                    </div>
                    <p style="margin-top: 12px; color: var(--text-muted); font-size: 0.85rem;">
                        Extract the ZIP and deploy to Apigee X or Edge using the management API or UI.
                    </p>
                </div>
                <span class="message-time">${this.formatTime(new Date())}</span>
            </div>
        `;
        messagesContainer.appendChild(successDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Show toast
        if (typeof toastManager !== 'undefined') {
            toastManager.success(`Downloaded ${filename}`, 3000);
        }
    }

    showApigeeConfirmation(extracted, error) {
        const messagesContainer = document.getElementById('chat-messages');
        const confirmDiv = document.createElement('div');
        confirmDiv.className = 'message assistant';

        let extractedInfo = '';
        if (extracted) {
            extractedInfo = `
                <div class="bundle-info" style="background: rgba(255, 152, 0, 0.1); border: 1px solid rgba(255, 152, 0, 0.3);">
                    <div class="label">Extracted Details</div>
                    <div class="value">
                        ${extracted.proxy_name ? `<strong>Name:</strong> ${extracted.proxy_name}<br>` : ''}
                        ${extracted.domain ? `<strong>Domain:</strong> ${extracted.domain}<br>` : ''}
                        ${extracted.proxy_endpoint ? `<strong>Endpoint:</strong> ${extracted.proxy_endpoint}<br>` : ''}
                    </div>
                </div>
            `;
        }

        confirmDiv.innerHTML = `
            <div class="message-avatar ai-avatar">
                <div class="ai-icon">
                    <div class="ai-core"></div>
                    <div class="ai-ring"></div>
                    <div class="ai-particles">
                        <span></span><span></span><span></span><span></span>
                    </div>
                </div>
            </div>
            <div class="message-content">
                <div class="apigee-welcome">
                    <h4>Need More Information</h4>
                    <p>${error}</p>
                    ${extractedInfo}
                    <p style="margin-top: 12px;">Please provide the missing details.</p>
                </div>
                <span class="message-time">${this.formatTime(new Date())}</span>
            </div>
        `;
        messagesContainer.appendChild(confirmDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    showApigeeError(error, tips) {
        const messagesContainer = document.getElementById('chat-messages');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'message assistant';

        let tipsHtml = '';
        if (tips && tips.length > 0) {
            tipsHtml = `
                <ul style="margin-top: 12px;">
                    ${tips.map(tip => `<li>${tip}</li>`).join('')}
                </ul>
            `;
        }

        errorDiv.innerHTML = `
            <div class="message-avatar ai-avatar">
                <div class="ai-icon">
                    <div class="ai-core"></div>
                    <div class="ai-ring"></div>
                    <div class="ai-particles">
                        <span></span><span></span><span></span><span></span>
                    </div>
                </div>
            </div>
            <div class="message-content">
                <div class="apigee-welcome" style="border-color: rgba(244, 67, 54, 0.3); background: linear-gradient(135deg, rgba(244, 67, 54, 0.1) 0%, rgba(255, 87, 34, 0.1) 100%);">
                    <h4 style="color: #f44336;">Could Not Generate Bundle</h4>
                    <p>${error}</p>
                    ${tipsHtml}
                </div>
                <span class="message-time">${this.formatTime(new Date())}</span>
            </div>
        `;
        messagesContainer.appendChild(errorDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    async sendMessage(forceSearch = false) {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();

        if (!message) return;

        // Check if Apigee mode is active
        if (this.apigeeMode) {
            return this.sendApigeeRequest(message);
        }

        // Remove existing follow-up suggestion chips
        document.querySelectorAll('.followup-suggestions').forEach(el => el.remove());

        // Add user message to UI
        this.addMessageToUI(message, 'user');
        input.value = '';
        input.style.height = 'auto';

        // Show typing indicator (with search indicator if force search)
        this.showTypingIndicator(forceSearch ? 'Searching the web...' : null);

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message, search: forceSearch })
            });

            const data = await response.json();

            // Remove typing indicator
            this.removeTypingIndicator();

            if (data.response) {
                // Store pending suggestions to render after typewriter finishes
                this.pendingSuggestions = data.suggestions || [];

                // Show response with typing effect
                this.addMessageToUI(data.response, 'assistant', data.ai_index, data.searched, true);

                // Update user message index if provided
                if (data.user_index !== undefined && data.user_index !== null) {
                    const messagesContainer = document.getElementById('chat-messages');
                    const messages = messagesContainer.querySelectorAll('.message.user');
                    const lastUserMsg = messages[messages.length - 1];

                    if (lastUserMsg) {
                        lastUserMsg.dataset.index = data.user_index;

                        // Add edit button now that we have the index
                        const content = lastUserMsg.querySelector('.message-content');
                        const textElem = lastUserMsg.querySelector('.message-text');
                        const text = textElem ? textElem.textContent : '';

                        // Remove existing actions if any
                        const existingActions = content.querySelector('.message-actions');
                        if (existingActions) existingActions.remove();

                        const actionsDiv = document.createElement('div');
                        actionsDiv.className = 'message-actions';

                        const editBtn = document.createElement('button');
                        editBtn.className = 'message-action-btn edit-btn';
                        editBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>';
                        editBtn.title = 'Edit message';
                        editBtn.onclick = () => this.startEditing(lastUserMsg, text, data.user_index);

                        actionsDiv.appendChild(editBtn);
                        content.appendChild(actionsDiv);
                    }
                }
            } else {
                this.addMessageToUI('Sorry, I encountered an error.', 'assistant');
            }

            // Refresh chat history sidebar if open
            const historyList = document.getElementById('chat-history-list');
            if (historyList && historyList.style.display !== 'none') {
                this.loadChatHistory();
            }

            // If voice mode is on, restart listening after AI responds
            if (this.voiceMode) {
                setTimeout(() => {
                    if (this.voiceMode) this.startListening();
                }, 1200);
            }
        } catch (error) {
            this.removeTypingIndicator();
            this.addMessageToUI('Connection error. Please make sure the server is running.', 'assistant');

            // Restart voice in error case too
            if (this.voiceMode) {
                setTimeout(() => {
                    if (this.voiceMode) this.startListening();
                }, 1500);
            }
        }
    }

    async webSearch() {
        // Force search mode - sends message with search flag
        await this.sendMessage(true);
    }

    // Handle suggestion chip clicks
    useSuggestion(text) {
        const input = document.getElementById('chat-input');
        input.value = text;
        input.focus();

        // Auto-resize textarea
        input.style.height = 'auto';
        input.style.height = input.scrollHeight + 'px';

        // Place cursor at end of text so user can edit or add more context
        input.setSelectionRange(input.value.length, input.value.length);
    }

    useFollowUpSuggestion(text) {
        // Remove existing follow-up chips
        document.querySelectorAll('.followup-suggestions').forEach(el => el.remove());

        const input = document.getElementById('chat-input');
        input.value = text;
        this.sendMessage();
    }

    renderFollowUpChips(messageDiv, suggestions) {
        if (!suggestions || suggestions.length === 0) return;

        const container = document.createElement('div');
        container.className = 'followup-suggestions';

        suggestions.forEach((text, i) => {
            const chip = document.createElement('button');
            chip.className = 'followup-chip';
            chip.textContent = text;
            chip.style.animationDelay = `${i * 0.1}s`;
            chip.addEventListener('click', () => this.useFollowUpSuggestion(text));
            container.appendChild(chip);
        });

        // Insert after the message div (not inside it)
        messageDiv.parentNode.insertBefore(container, messageDiv.nextSibling);

        // Scroll to show chips
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    addMessageToUI(text, role, index = null, searched = false, typeEffect = false) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}${searched ? ' searched' : ''}`;
        if (index !== null) {
            messageDiv.dataset.index = index;
        }

        const avatar = document.createElement('div');
        avatar.className = role === 'user' ? 'message-avatar' : 'message-avatar ai-avatar';

        if (role === 'user') {
            avatar.textContent = '👤';
        } else {
            // Create advanced AI icon
            avatar.innerHTML = `
                <div class="ai-icon">
                    <div class="ai-core"></div>
                    <div class="ai-ring"></div>
                    <div class="ai-particles">
                        <span></span><span></span><span></span><span></span>
                    </div>
                </div>
            `;
        }

        const content = document.createElement('div');
        content.className = 'message-content';

        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';

        // For assistant messages, parse markdown and highlight code
        if (role === 'assistant') {
            // Store raw text on the element for clean copy
            textDiv.dataset.rawText = text;

            if (typeEffect) {
                // Add typing effect for assistant messages
                this.typeWriterEffect(textDiv, text, messagesContainer);
            } else {
                this.renderMarkdown(textDiv, text);
            }

            // Add copy button for the full response
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'message-actions';

            const copyMsgBtn = document.createElement('button');
            copyMsgBtn.className = 'message-action-btn copy-msg-btn';
            copyMsgBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg> Copy';
            copyMsgBtn.title = 'Copy response as plain text';
            copyMsgBtn.onclick = () => this.copyMessageText(copyMsgBtn, textDiv);
            actionsDiv.appendChild(copyMsgBtn);

            content.appendChild(actionsDiv);
        } else {
            // For user messages, just escape HTML
            textDiv.textContent = text;

            // Only add edit button if we have a valid index
            if (index !== null && index !== undefined) {
                const actionsDiv = document.createElement('div');
                actionsDiv.className = 'message-actions';

                const editBtn = document.createElement('button');
                editBtn.className = 'message-action-btn edit-btn';
                editBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>';
                editBtn.title = 'Edit message';
                editBtn.onclick = () => this.startEditing(messageDiv, text, index);

                actionsDiv.appendChild(editBtn);
                content.appendChild(actionsDiv);
            }
        }

        const time = document.createElement('span');
        time.className = 'message-time';
        time.textContent = this.formatTime(new Date());

        content.appendChild(textDiv);
        content.appendChild(time);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    startEditing(messageDiv, currentText, index) {
        const textDiv = messageDiv.querySelector('.message-text');
        const actionsDiv = messageDiv.querySelector('.message-actions');

        // Get index from data attribute if not provided
        if (index === null || index === undefined) {
            index = messageDiv.dataset.index;
        }

        // Validate index exists
        if (index === null || index === undefined || index === 'null' || index === 'undefined') {
            alert('Cannot edit this message. Please try again after sending a new message.');
            return;
        }

        // Hide actions while editing
        if (actionsDiv) actionsDiv.style.display = 'none';

        // Create edit container
        const editContainer = document.createElement('div');
        editContainer.className = 'edit-container';

        const textarea = document.createElement('textarea');
        textarea.className = 'edit-textarea';
        textarea.value = currentText;

        // Auto-resize textarea
        textarea.style.height = 'auto';
        setTimeout(() => {
            textarea.style.height = textarea.scrollHeight + 'px';
            textarea.focus();
        }, 0);

        textarea.addEventListener('input', () => {
            textarea.style.height = 'auto';
            textarea.style.height = textarea.scrollHeight + 'px';
        });

        // Handle Enter key to submit (Shift+Enter for new line)
        textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.submitEdit(index, textarea.value, messageDiv);
            } else if (e.key === 'Escape') {
                this.cancelEdit(messageDiv, currentText);
            }
        });

        const btnGroup = document.createElement('div');
        btnGroup.className = 'edit-buttons';

        const saveBtn = document.createElement('button');
        saveBtn.className = 'btn-primary btn-sm';
        saveBtn.textContent = 'Save & Submit';
        saveBtn.onclick = () => this.submitEdit(index, textarea.value, messageDiv);

        const cancelBtn = document.createElement('button');
        cancelBtn.className = 'btn-secondary btn-sm';
        cancelBtn.textContent = 'Cancel';
        cancelBtn.onclick = () => this.cancelEdit(messageDiv, currentText);

        btnGroup.appendChild(saveBtn);
        btnGroup.appendChild(cancelBtn);

        editContainer.appendChild(textarea);
        editContainer.appendChild(btnGroup);

        // Replace text div with edit container
        textDiv.replaceWith(editContainer);
    }

    cancelEdit(messageDiv, originalText) {
        const editContainer = messageDiv.querySelector('.edit-container');
        const actionsDiv = messageDiv.querySelector('.message-actions');

        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.textContent = originalText;

        editContainer.replaceWith(textDiv);
        if (actionsDiv) actionsDiv.style.display = 'flex';
    }

    async submitEdit(index, newText, messageDiv) {
        if (!newText.trim()) return;

        // Ensure index is a valid integer
        const messageIndex = parseInt(index, 10);
        console.log('submitEdit called with index:', index, 'parsed as:', messageIndex);

        if (isNaN(messageIndex) || messageIndex < 1) {
            alert('Invalid message index. Cannot edit this message. Index: ' + index);
            return;
        }

        const editContainer = messageDiv.querySelector('.edit-container');

        // Show loading state
        editContainer.innerHTML = '<div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>';

        console.log('Sending edit request with index:', messageIndex, 'content:', newText.substring(0, 50));

        try {
            const response = await fetch('/api/chat/edit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ index: messageIndex, content: newText })
            });

            const data = await response.json();

            if (data.error) {
                alert('Error: ' + data.error);
                this.cancelEdit(messageDiv, newText); // Revert to text but keep new content
                return;
            }

            // Remove all subsequent messages from UI
            let nextSibling = messageDiv.nextElementSibling;
            while (nextSibling) {
                const toRemove = nextSibling;
                nextSibling = nextSibling.nextElementSibling;
                toRemove.remove();
            }

            // Update current message UI
            const actionsDiv = messageDiv.querySelector('.message-actions');
            const textDiv = document.createElement('div');
            textDiv.className = 'message-text';
            textDiv.textContent = newText;

            editContainer.replaceWith(textDiv);
            if (actionsDiv) {
                actionsDiv.style.display = 'flex';
                // Update onclick handler with new text
                const editBtn = actionsDiv.querySelector('.edit-btn');
                editBtn.onclick = () => this.startEditing(messageDiv, newText, index);
            }

            // Remove existing follow-up suggestion chips
            document.querySelectorAll('.followup-suggestions').forEach(el => el.remove());

            // Store pending suggestions to render after typewriter finishes
            this.pendingSuggestions = data.suggestions || [];

            // Add new AI response with typing effect
            this.addMessageToUI(data.response, 'assistant', data.ai_index, false, true);

        } catch (error) {
            console.error('Error submitting edit:', error);
            alert('Failed to submit edit. Please try again.');
            this.cancelEdit(messageDiv, newText);
        }
    }

    copyMessageText(button, textDiv) {
        // Copy the AI response as clean plain text (no HTML formatting artifacts)
        // Use the raw markdown stored on the element, which pastes cleanly everywhere
        const rawText = textDiv.dataset.rawText || textDiv.innerText || textDiv.textContent;
        const originalText = button.innerHTML;

        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(rawText).then(() => {
                this.showCopySuccess(button, originalText);
                toastManager?.success('Response copied!', 1500);
            }).catch(err => {
                console.error('Clipboard API failed:', err);
                this.fallbackCopy(button, rawText, originalText);
            });
        } else {
            this.fallbackCopy(button, rawText, originalText);
        }
    }

    copyCode(button, code) {
        const originalText = button.innerHTML;

        // Try modern clipboard API first
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(code).then(() => {
                this.showCopySuccess(button, originalText);
            }).catch(err => {
                console.error('Clipboard API failed:', err);
                this.fallbackCopy(button, code, originalText);
            });
        } else {
            // Fallback for non-secure contexts or older browsers
            this.fallbackCopy(button, code, originalText);
        }
    }

    fallbackCopy(button, code, originalText) {
        try {
            // Create temporary textarea
            const textArea = document.createElement('textarea');
            textArea.value = code;
            textArea.style.position = 'fixed';
            textArea.style.left = '-9999px';
            textArea.style.top = '-9999px';
            textArea.style.opacity = '0';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();

            // Execute copy command
            const successful = document.execCommand('copy');
            document.body.removeChild(textArea);

            if (successful) {
                this.showCopySuccess(button, originalText);
            } else {
                this.showCopyError(button, originalText);
            }
        } catch (err) {
            console.error('Fallback copy failed:', err);
            this.showCopyError(button, originalText);
        }
    }

    showCopySuccess(button, originalText) {
        button.innerHTML = '✓ Copied!';
        button.classList.add('copied');

        setTimeout(() => {
            button.innerHTML = originalText;
            button.classList.remove('copied');
        }, 2000);
    }

    showCopyError(button, originalText) {
        button.innerHTML = '✗ Failed';
        button.classList.add('copy-error');

        setTimeout(() => {
            button.innerHTML = originalText;
            button.classList.remove('copy-error');
        }, 2000);
    }

    showTypingIndicator(customMessage = null) {
        const messagesContainer = document.getElementById('chat-messages');
        const indicator = document.createElement('div');
        indicator.className = 'message assistant typing-indicator-message';
        indicator.id = 'typing-indicator';

        const statusText = customMessage ? `<span class="typing-status">${customMessage}</span>` : '<span class="typing-status">Thinking...</span>';

        indicator.innerHTML = `
            <div class="message-avatar ai-avatar loading">
                <div class="ai-icon">
                    <div class="ai-core"></div>
                    <div class="ai-ring"></div>
                    <div class="ai-particles">
                        <span></span><span></span><span></span><span></span>
                    </div>
                </div>
            </div>
            <div class="message-content">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
                ${statusText}
            </div>
        `;

        messagesContainer.appendChild(indicator);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    renderMarkdown(textDiv, text) {
        // Configure marked options
        marked.setOptions({
            breaks: true,
            gfm: true,
            headerIds: false,
            mangle: false
        });

        // Parse markdown
        const htmlContent = marked.parse(text);
        textDiv.innerHTML = htmlContent;

        // Apply syntax highlighting to code blocks
        this.highlightCodeBlocks(textDiv);
    }

    highlightCodeBlocks(container) {
        container.querySelectorAll('pre code').forEach((block) => {
            const pre = block.parentElement;
            // Skip if already wrapped
            if (pre.parentElement && (
                pre.parentElement.classList.contains('code-block-wrapper') ||
                pre.parentElement.classList.contains('diagram-block-wrapper') ||
                pre.parentElement.classList.contains('diagram-code-view')
            )) return;

            const language = block.className.replace('language-', '').replace('hljs', '').trim() || 'code';
            const codeContent = block.textContent;

            // Check if this is an architecture/design diagram
            const isDiagram = this.isArchitectureDiagram(language, codeContent);

            if (isDiagram) {
                this.createDiagramBlock(pre, block, language, codeContent);
            } else {
                // Regular code block
                hljs.highlightElement(block);
                this.createCodeBlock(pre, block, language, codeContent);
            }
        });
    }

    isArchitectureDiagram(language, content) {
        // Check if language explicitly indicates a diagram
        const diagramLanguages = ['mermaid', 'plantuml', 'diagram', 'flowchart', 'sequence', 'class', 'er', 'gantt', 'architecture'];
        if (diagramLanguages.includes(language.toLowerCase())) {
            return true;
        }

        // Check content for mermaid diagram patterns
        const mermaidPatterns = [
            /^(graph|flowchart)\s+(TB|TD|BT|RL|LR)/m,
            /^sequenceDiagram/m,
            /^classDiagram/m,
            /^stateDiagram/m,
            /^erDiagram/m,
            /^gantt/m,
            /^pie/m,
            /^gitGraph/m,
            /^journey/m,
            /^C4Context/m,
            /^C4Container/m,
            /^C4Component/m,
            /^mindmap/m,
            /^timeline/m,
            /^zenuml/m,
            /^sankey/m
        ];

        return mermaidPatterns.some(pattern => pattern.test(content));
    }

    createCodeBlock(pre, block, language, codeContent) {
        const wrapper = document.createElement('div');
        wrapper.className = 'code-block-wrapper';

        const header = document.createElement('div');
        header.className = 'code-header';

        const langLabel = document.createElement('span');
        langLabel.className = 'code-language';
        langLabel.textContent = language;

        const actionsContainer = document.createElement('div');
        actionsContainer.className = 'code-actions';

        const copyBtn = document.createElement('button');
        copyBtn.className = 'code-copy-btn';
        copyBtn.innerHTML = '📋 Copy';
        copyBtn.onclick = () => this.copyCode(copyBtn, codeContent);
        actionsContainer.appendChild(copyBtn);

        // Check if this is executable frontend code
        const isExecutable = this.isExecutableCode(language, codeContent);
        if (isExecutable) {
            const executeBtn = document.createElement('button');
            executeBtn.className = 'code-execute-btn';
            executeBtn.innerHTML = '▶ Run';
            executeBtn.title = 'Execute in preview';
            executeBtn.onclick = () => this.executeCodeInCanvas(language, codeContent);
            actionsContainer.appendChild(executeBtn);
        }

        header.appendChild(langLabel);
        header.appendChild(actionsContainer);

        pre.parentNode.insertBefore(wrapper, pre);
        wrapper.appendChild(header);
        wrapper.appendChild(pre);
    }

    isExecutableCode(language, content) {
        const frontendLanguages = ['html', 'css', 'javascript', 'js', 'jsx', 'tsx', 'vue', 'svelte'];
        const backendLanguages = ['python', 'py', 'java', 'cpp', 'c++', 'c', 'go', 'rust', 'ruby', 'php'];
        const langLower = language.toLowerCase();

        // Check if language is executable (frontend or backend)
        if (frontendLanguages.includes(langLower) || backendLanguages.includes(langLower)) {
            return true;
        }

        // Check if content looks like HTML
        if (content.includes('<!DOCTYPE') || content.includes('<html') ||
            content.includes('<div') || content.includes('<body') ||
            content.includes('<head') || content.includes('<style')) {
            return true;
        }

        return false;
    }

    isBackendCode(language) {
        const backendLanguages = ['python', 'py', 'java', 'cpp', 'c++', 'c', 'go', 'rust', 'ruby', 'php'];
        return backendLanguages.includes(language.toLowerCase());
    }

    async executeBackendCode(language, code) {
        // Create or get the code runner modal
        let runnerModal = document.getElementById('code-runner-modal');

        if (!runnerModal) {
            runnerModal = this.createCodeRunnerModal();
            document.body.appendChild(runnerModal);
        }

        const outputArea = runnerModal.querySelector('#runner-output');
        const inputArea = runnerModal.querySelector('#runner-input');
        const languageLabel = runnerModal.querySelector('#runner-language');
        const runBtn = runnerModal.querySelector('#runner-run-btn');
        const codeDisplay = runnerModal.querySelector('#runner-code');

        // Set language label
        const langNames = {
            'python': 'Python', 'py': 'Python',
            'java': 'Java',
            'cpp': 'C++', 'c++': 'C++',
            'c': 'C',
            'go': 'Go',
            'rust': 'Rust',
            'ruby': 'Ruby',
            'php': 'PHP'
        };
        languageLabel.textContent = langNames[language.toLowerCase()] || language;

        // Display code
        codeDisplay.textContent = code;
        if (typeof hljs !== 'undefined') {
            hljs.highlightElement(codeDisplay);
        }

        // Clear previous output
        outputArea.innerHTML = '<span class="output-placeholder">Click "Run Code" to execute...</span>';
        inputArea.value = '';

        // Show modal
        runnerModal.classList.add('active');
        document.body.style.overflow = 'hidden';

        // Store current code and language for run button
        runnerModal.dataset.code = code;
        runnerModal.dataset.language = language;

        // Run button handler
        runBtn.onclick = async () => {
            const stdin = inputArea.value;
            await this.runCodeOnServer(language, code, stdin, outputArea);
        };
    }

    async runCodeOnServer(language, code, stdin, outputArea) {
        outputArea.innerHTML = `
            <div class="runner-loading">
                <div class="runner-spinner"></div>
                <span>Executing code...</span>
            </div>
        `;

        try {
            const response = await fetch('/api/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ language, code, stdin })
            });

            const data = await response.json();

            if (data.success) {
                let output = '';

                if (data.output && data.output.trim()) {
                    output += `<div class="output-section">
                        <div class="output-label">📤 Output:</div>
                        <pre class="output-content">${this.escapeHtml(data.output)}</pre>
                    </div>`;
                }

                if (data.error && data.error.trim()) {
                    output += `<div class="output-section error">
                        <div class="output-label">⚠️ Errors:</div>
                        <pre class="output-content error">${this.escapeHtml(data.error)}</pre>
                    </div>`;
                }

                if (data.execution_time) {
                    output += `<div class="output-meta">⏱️ Execution time: ${data.execution_time}ms</div>`;
                }

                if (!output) {
                    output = '<span class="output-placeholder">Program executed with no output.</span>';
                }

                outputArea.innerHTML = output;
            } else {
                outputArea.innerHTML = `
                    <div class="output-section error">
                        <div class="output-label">❌ Error:</div>
                        <pre class="output-content error">${this.escapeHtml(data.error || 'Execution failed')}</pre>
                    </div>
                `;
            }
        } catch (error) {
            outputArea.innerHTML = `
                <div class="output-section error">
                    <div class="output-label">❌ Connection Error:</div>
                    <pre class="output-content error">${this.escapeHtml(error.message)}</pre>
                </div>
            `;
        }
    }

    createCodeRunnerModal() {
        const modal = document.createElement('div');
        modal.id = 'code-runner-modal';
        modal.className = 'code-runner-modal';

        modal.innerHTML = `
            <div class="runner-modal-container">
                <div class="runner-modal-header">
                    <div class="runner-header-left">
                        <span class="runner-icon">⚡</span>
                        <h3>Code Runner</h3>
                        <span class="runner-language-badge" id="runner-language">Python</span>
                    </div>
                    <div class="runner-header-actions">
                        <button class="runner-action-btn primary" id="runner-run-btn" title="Run Code">
                            <svg viewBox="0 0 24 24" fill="currentColor" width="16" height="16">
                                <polygon points="5 3 19 12 5 21 5 3"></polygon>
                            </svg>
                            Run Code
                        </button>
                        <button class="runner-action-btn close" id="runner-close" title="Close">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                        </button>
                    </div>
                </div>
                <div class="runner-modal-body">
                    <div class="runner-section code-section">
                        <div class="section-header">
                            <span class="section-icon">📝</span>
                            <span class="section-title">Code</span>
                        </div>
                        <pre class="runner-code-display"><code id="runner-code"></code></pre>
                    </div>
                    <div class="runner-section input-section">
                        <div class="section-header">
                            <span class="section-icon">📥</span>
                            <span class="section-title">Input (stdin)</span>
                            <span class="section-hint">Optional - for programs that need input</span>
                        </div>
                        <textarea id="runner-input" placeholder="Enter input here (one value per line)..."></textarea>
                    </div>
                    <div class="runner-section output-section">
                        <div class="section-header">
                            <span class="section-icon">📤</span>
                            <span class="section-title">Output</span>
                        </div>
                        <div class="runner-output" id="runner-output">
                            <span class="output-placeholder">Click "Run Code" to execute...</span>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Close handlers
        const closeBtn = modal.querySelector('#runner-close');
        closeBtn.onclick = () => this.closeCodeRunnerModal(modal);

        modal.onclick = (e) => {
            if (e.target === modal) this.closeCodeRunnerModal(modal);
        };

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal.classList.contains('active')) {
                this.closeCodeRunnerModal(modal);
            }
        });

        return modal;
    }

    closeCodeRunnerModal(modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }

    executeCodeInCanvas(language, code) {
        // Check if this is backend code
        if (this.isBackendCode(language)) {
            this.executeBackendCode(language, code);
            return;
        }

        // Create or get the preview modal
        let previewModal = document.getElementById('code-preview-modal');

        if (!previewModal) {
            previewModal = this.createPreviewModal();
            document.body.appendChild(previewModal);
        }

        const iframe = previewModal.querySelector('#preview-iframe');
        const langLower = language.toLowerCase();

        // Prepare the HTML content based on language
        let htmlContent = '';

        if (langLower === 'html' || code.includes('<!DOCTYPE') || code.includes('<html')) {
            // Full HTML document
            htmlContent = code;
        } else if (langLower === 'css') {
            // CSS only - wrap in HTML
            htmlContent = `
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            padding: 20px;
            background: #1a1b2e;
            color: #e0e0e0;
        }
        ${code}
    </style>
</head>
<body>
    <div class="preview-container">
        <h2>CSS Preview</h2>
        <p>Add HTML elements to see your CSS in action.</p>
        <div class="demo-box">Demo Box</div>
        <button class="demo-btn">Demo Button</button>
    </div>
</body>
</html>`;
        } else if (langLower === 'javascript' || langLower === 'js') {
            // JavaScript only - wrap in HTML
            htmlContent = `
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            padding: 20px;
            background: #1a1b2e;
            color: #e0e0e0;
        }
        #output {
            background: #0d0e1a;
            border: 1px solid #667eea;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
            min-height: 100px;
            font-family: 'JetBrains Mono', monospace;
            white-space: pre-wrap;
        }
        .log-entry { margin: 5px 0; padding: 5px; border-radius: 4px; }
        .log-info { background: rgba(102, 126, 234, 0.2); }
        .log-error { background: rgba(245, 87, 108, 0.2); color: #f5576c; }
        .log-warn { background: rgba(254, 225, 64, 0.2); color: #fee140; }
    </style>
</head>
<body>
    <h3>JavaScript Output</h3>
    <div id="output"></div>
    <script>
        // Override console methods to display in output
        const output = document.getElementById('output');
        const originalConsole = { ...console };

        function logToOutput(type, ...args) {
            const entry = document.createElement('div');
            entry.className = 'log-entry log-' + type;
            entry.textContent = args.map(a => typeof a === 'object' ? JSON.stringify(a, null, 2) : String(a)).join(' ');
            output.appendChild(entry);
            originalConsole[type](...args);
        }

        console.log = (...args) => logToOutput('info', ...args);
        console.error = (...args) => logToOutput('error', ...args);
        console.warn = (...args) => logToOutput('warn', ...args);
        console.info = (...args) => logToOutput('info', ...args);

        // Execute user code
        try {
            ${code}
        } catch(e) {
            console.error('Error: ' + e.message);
        }
    </script>
</body>
</html>`;
        } else {
            // Try to detect and wrap appropriately
            if (code.includes('<') && code.includes('>')) {
                // Looks like HTML fragment
                htmlContent = `
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            padding: 20px;
            background: #1a1b2e;
            color: #e0e0e0;
        }
        * { box-sizing: border-box; }
    </style>
</head>
<body>
    ${code}
</body>
</html>`;
            } else {
                htmlContent = code;
            }
        }

        // Write to iframe
        iframe.srcdoc = htmlContent;

        // Show the modal
        previewModal.classList.add('active');
        document.body.style.overflow = 'hidden';

        // Toast notification
        if (typeof toastManager !== 'undefined') {
            toastManager.success('Code executed in preview', 2000);
        }
    }

    createPreviewModal() {
        const modal = document.createElement('div');
        modal.id = 'code-preview-modal';
        modal.className = 'code-preview-modal';

        modal.innerHTML = `
            <div class="preview-modal-container">
                <div class="preview-modal-header">
                    <div class="preview-header-left">
                        <span class="preview-icon">▶</span>
                        <h3>Live Preview</h3>
                    </div>
                    <div class="preview-header-actions">
                        <button class="preview-action-btn" id="preview-refresh" title="Refresh">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"></path>
                                <path d="M21 3v5h-5"></path>
                                <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"></path>
                                <path d="M3 21v-5h5"></path>
                            </svg>
                        </button>
                        <button class="preview-action-btn" id="preview-new-tab" title="Open in New Tab">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                                <polyline points="15 3 21 3 21 9"></polyline>
                                <line x1="10" y1="14" x2="21" y2="3"></line>
                            </svg>
                        </button>
                        <button class="preview-action-btn" id="preview-fullscreen" title="Toggle Fullscreen">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="15 3 21 3 21 9"></polyline>
                                <polyline points="9 21 3 21 3 15"></polyline>
                                <line x1="21" y1="3" x2="14" y2="10"></line>
                                <line x1="3" y1="21" x2="10" y2="14"></line>
                            </svg>
                        </button>
                        <button class="preview-action-btn close" id="preview-close" title="Close">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                        </button>
                    </div>
                </div>
                <div class="preview-modal-body">
                    <div class="preview-device-frame">
                        <iframe id="preview-iframe" sandbox="allow-scripts allow-modals" title="Code Preview"></iframe>
                    </div>
                </div>
                <div class="preview-modal-footer">
                    <div class="preview-size-controls">
                        <button class="size-btn active" data-width="100%" title="Responsive">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
                                <line x1="8" y1="21" x2="16" y2="21"></line>
                                <line x1="12" y1="17" x2="12" y2="21"></line>
                            </svg>
                        </button>
                        <button class="size-btn" data-width="768px" title="Tablet">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="4" y="2" width="16" height="20" rx="2" ry="2"></rect>
                                <line x1="12" y1="18" x2="12.01" y2="18"></line>
                            </svg>
                        </button>
                        <button class="size-btn" data-width="375px" title="Mobile">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect>
                                <line x1="12" y1="18" x2="12.01" y2="18"></line>
                            </svg>
                        </button>
                    </div>
                    <span class="preview-hint">Sandbox mode: Scripts run in isolation</span>
                </div>
            </div>
        `;

        // Event listeners
        const closeBtn = modal.querySelector('#preview-close');
        const refreshBtn = modal.querySelector('#preview-refresh');
        const newTabBtn = modal.querySelector('#preview-new-tab');
        const fullscreenBtn = modal.querySelector('#preview-fullscreen');
        const sizeBtns = modal.querySelectorAll('.size-btn');
        const iframe = modal.querySelector('#preview-iframe');
        const deviceFrame = modal.querySelector('.preview-device-frame');

        closeBtn.onclick = () => this.closePreviewModal(modal);

        modal.onclick = (e) => {
            if (e.target === modal) this.closePreviewModal(modal);
        };

        refreshBtn.onclick = () => {
            const currentSrc = iframe.srcdoc;
            iframe.srcdoc = '';
            setTimeout(() => { iframe.srcdoc = currentSrc; }, 50);
        };

        newTabBtn.onclick = () => {
            const newWindow = window.open('', '_blank');
            newWindow.document.write(iframe.srcdoc);
            newWindow.document.close();
        };

        fullscreenBtn.onclick = () => {
            modal.classList.toggle('fullscreen');
        };

        sizeBtns.forEach(btn => {
            btn.onclick = () => {
                sizeBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                deviceFrame.style.maxWidth = btn.dataset.width;
            };
        });

        // Escape key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && modal.classList.contains('active')) {
                this.closePreviewModal(modal);
            }
        });

        return modal;
    }

    closePreviewModal(modal) {
        modal.classList.remove('active');
        modal.classList.remove('fullscreen');
        document.body.style.overflow = '';
    }

    createDiagramBlock(pre, block, language, codeContent) {
        const wrapper = document.createElement('div');
        wrapper.className = 'diagram-block-wrapper';

        // Create tabbed header
        const header = document.createElement('div');
        header.className = 'diagram-header';

        const tabsContainer = document.createElement('div');
        tabsContainer.className = 'diagram-tabs';

        const codeTab = document.createElement('button');
        codeTab.className = 'diagram-tab';
        codeTab.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="16 18 22 12 16 6"></polyline>
                <polyline points="8 6 2 12 8 18"></polyline>
            </svg>
            Code
        `;

        const visualTab = document.createElement('button');
        visualTab.className = 'diagram-tab active';
        visualTab.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="3" y1="9" x2="21" y2="9"></line>
                <line x1="9" y1="21" x2="9" y2="9"></line>
            </svg>
            Visual
        `;

        tabsContainer.appendChild(codeTab);
        tabsContainer.appendChild(visualTab);

        // Language label and actions
        const labelContainer = document.createElement('div');
        labelContainer.className = 'diagram-label-container';

        const langLabel = document.createElement('span');
        langLabel.className = 'diagram-language';
        langLabel.innerHTML = `<span class="diagram-badge">📐 Architecture</span> ${language || 'mermaid'}`;

        const actionsContainer = document.createElement('div');
        actionsContainer.className = 'diagram-actions';

        const copyBtn = document.createElement('button');
        copyBtn.className = 'diagram-action-btn';
        copyBtn.innerHTML = '📋 Copy';
        copyBtn.title = 'Copy code';
        copyBtn.onclick = () => this.copyCode(copyBtn, codeContent);

        const downloadBtn = document.createElement('button');
        downloadBtn.className = 'diagram-action-btn';
        downloadBtn.innerHTML = '⬇️ Export PDF';
        downloadBtn.title = 'Export as PDF';

        const fullscreenBtn = document.createElement('button');
        fullscreenBtn.className = 'diagram-action-btn';
        fullscreenBtn.innerHTML = '⛶ Expand';
        fullscreenBtn.title = 'View fullscreen';

        actionsContainer.appendChild(copyBtn);
        actionsContainer.appendChild(downloadBtn);
        actionsContainer.appendChild(fullscreenBtn);

        labelContainer.appendChild(langLabel);
        labelContainer.appendChild(actionsContainer);

        header.appendChild(tabsContainer);
        header.appendChild(labelContainer);

        // Create content containers
        const contentContainer = document.createElement('div');
        contentContainer.className = 'diagram-content';

        // Code view (hidden by default)
        const codeView = document.createElement('div');
        codeView.className = 'diagram-code-view';

        const codePre = document.createElement('pre');
        const codeBlock = document.createElement('code');
        codeBlock.className = `language-${language || 'mermaid'}`;
        codeBlock.textContent = codeContent;
        hljs.highlightElement(codeBlock);
        codePre.appendChild(codeBlock);
        codeView.appendChild(codePre);

        // Visual view (shown by default)
        const visualView = document.createElement('div');
        visualView.className = 'diagram-visual-view active';

        const diagramContainer = document.createElement('div');
        diagramContainer.className = 'mermaid-diagram';
        const diagramId = 'mermaid-' + Math.random().toString(36).substr(2, 9);
        diagramContainer.id = diagramId;
        visualView.appendChild(diagramContainer);

        contentContainer.appendChild(codeView);
        contentContainer.appendChild(visualView);

        // Tab switching logic
        codeTab.onclick = () => {
            codeTab.classList.add('active');
            visualTab.classList.remove('active');
            codeView.classList.add('active');
            visualView.classList.remove('active');
        };

        visualTab.onclick = () => {
            visualTab.classList.add('active');
            codeTab.classList.remove('active');
            visualView.classList.add('active');
            codeView.classList.remove('active');
        };

        // Export functionality
        downloadBtn.onclick = () => this.exportDiagram(diagramId, 'architecture-diagram');

        // Fullscreen functionality
        fullscreenBtn.onclick = () => this.showDiagramFullscreen(diagramContainer, codeContent);

        // Insert wrapper
        pre.parentNode.insertBefore(wrapper, pre);
        wrapper.appendChild(header);
        wrapper.appendChild(contentContainer);
        pre.remove();

        // Render mermaid diagram
        this.renderMermaidDiagram(diagramContainer, codeContent, diagramId);
    }

    async renderMermaidDiagram(container, code, id) {
        // Show loading state
        container.innerHTML = `
            <div class="diagram-loading">
                <div class="diagram-loading-spinner"></div>
                <div class="diagram-loading-text">Rendering diagram...</div>
            </div>
        `;

        // Wait for mermaid to be available
        const waitForMermaid = () => {
            return new Promise((resolve, reject) => {
                if (typeof mermaid !== 'undefined') {
                    resolve();
                } else {
                    let attempts = 0;
                    const checkInterval = setInterval(() => {
                        attempts++;
                        if (typeof mermaid !== 'undefined') {
                            clearInterval(checkInterval);
                            resolve();
                        } else if (attempts > 50) {
                            clearInterval(checkInterval);
                            reject(new Error('Mermaid library not loaded'));
                        }
                    }, 100);
                }
            });
        };

        try {
            await waitForMermaid();

            // Sanitize mermaid code to fix common syntax issues
            const cleanCode = this.sanitizeMermaidCode(code.trim());

            // Generate unique ID to avoid conflicts
            const uniqueId = 'mermaid-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);

            // Render using mermaid
            const { svg } = await mermaid.render(uniqueId, cleanCode);
            container.innerHTML = svg;

            // Style the SVG for better display
            const svgElement = container.querySelector('svg');
            if (svgElement) {
                svgElement.style.maxWidth = '100%';
                svgElement.style.height = 'auto';
                svgElement.style.display = 'block';
                svgElement.style.margin = '0 auto';
            }

            // Add zoom/pan functionality
            this.addDiagramInteractivity(container);
        } catch (error) {
            console.error('Mermaid rendering error:', error);
            container.innerHTML = `
                <div class="diagram-error">
                    <div class="error-icon">⚠️</div>
                    <div class="error-title">Diagram Rendering Error</div>
                    <div class="error-message">${this.escapeHtml(error.message || 'Failed to render diagram')}</div>
                    <div class="error-hint">Check the diagram syntax and try again</div>
                </div>
            `;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    sanitizeMermaidCode(code) {
        // Minimal sanitization for Mermaid 10.x - only fix what's truly broken
        let sanitized = code;

        // 1. Remove invisible/zero-width characters
        sanitized = sanitized.replace(/[\u200B-\u200D\uFEFF]/g, '');

        // 2. Normalize line endings
        sanitized = sanitized.replace(/\r\n/g, '\n').replace(/\r/g, '\n');

        // 3. Remove markdown code fence markers
        sanitized = sanitized.replace(/^```mermaid\s*\n?/im, '');
        sanitized = sanitized.replace(/\n?```\s*$/m, '');

        // 4. Normalize unicode characters that look like ASCII but aren't
        sanitized = sanitized.replace(/\u2011/g, '-');           // non-breaking hyphen
        sanitized = sanitized.replace(/[\u2013\u2014]/g, '--');  // en-dash, em-dash
        sanitized = sanitized.replace(/[\u2018\u2019\u0060\u00B4]/g, "'"); // smart quotes, backticks
        sanitized = sanitized.replace(/[\u201C\u201D]/g, '"');   // smart double quotes

        // 5. Trim each line but preserve structure
        sanitized = sanitized.split('\n').map(line => line.trim()).join('\n');

        // 6. Remove empty lines at start
        sanitized = sanitized.replace(/^\n+/, '');

        // 7. SAFETY NET: Auto-quote node content with special characters
        sanitized = this.autoQuoteNodeContent(sanitized);

        return sanitized.trim();
    }

    autoQuoteNodeContent(code) {
        // Safety net: Fix unquoted node content that contains special characters
        // This catches cases where the AI forgot to quote properly

        const lines = code.split('\n');
        const fixedLines = lines.map(line => {
            // Skip diagram declarations, comments, and directives
            if (/^\s*(graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|erDiagram|gantt|pie|gitGraph|mindmap|timeline|subgraph|end|%%|style|linkStyle|class\s)/i.test(line)) {
                return line;
            }

            // Fix square bracket nodes: A[text (with parens)] → A["text (with parens)"]
            // Pattern: word followed by [ then content with special chars then ]
            // But NOT already quoted content
            line = line.replace(/(\b[A-Za-z_][A-Za-z0-9_]*)\[([^\]"]+)\]/g, (match, nodeId, content) => {
                // Check if content has special chars that need quoting
                if (/[()<>{}\[\]"']/.test(content)) {
                    // Escape any internal quotes
                    const escaped = content.replace(/"/g, "'");
                    return `${nodeId}["${escaped}"]`;
                }
                return match;
            });

            // Fix curly brace nodes: A{text (with parens)} → A{"text (with parens)"}
            line = line.replace(/(\b[A-Za-z_][A-Za-z0-9_]*)\{([^}"]+)\}/g, (match, nodeId, content) => {
                if (/[()<>\[\]"']/.test(content)) {
                    const escaped = content.replace(/"/g, "'");
                    return `${nodeId}{"${escaped}"}`;
                }
                return match;
            });

            // Fix stadium nodes: A(text [with brackets]) → A("text [with brackets]")
            // Be careful not to match arrow syntax like -->
            line = line.replace(/(\b[A-Za-z_][A-Za-z0-9_]*)\(([^)"]+)\)(?![->])/g, (match, nodeId, content) => {
                if (/[<>{}\[\]"']/.test(content)) {
                    const escaped = content.replace(/"/g, "'");
                    return `${nodeId}("${escaped}")`;
                }
                return match;
            });

            return line;
        });

        return fixedLines.join('\n');
    }

    addDiagramInteractivity(container) {
        let scale = 1;
        let panning = false;
        let pointX = 0;
        let pointY = 0;
        let start = { x: 0, y: 0 };

        const svg = container.querySelector('svg');
        if (!svg) return;

        svg.style.cursor = 'grab';
        svg.style.transition = 'transform 0.1s ease-out';

        container.addEventListener('wheel', (e) => {
            e.preventDefault();
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            scale = Math.min(Math.max(0.5, scale * delta), 3);
            svg.style.transform = `scale(${scale}) translate(${pointX}px, ${pointY}px)`;
        });

        svg.addEventListener('mousedown', (e) => {
            panning = true;
            start = { x: e.clientX - pointX, y: e.clientY - pointY };
            svg.style.cursor = 'grabbing';
        });

        svg.addEventListener('mouseup', () => {
            panning = false;
            svg.style.cursor = 'grab';
        });

        svg.addEventListener('mousemove', (e) => {
            if (!panning) return;
            pointX = e.clientX - start.x;
            pointY = e.clientY - start.y;
            svg.style.transform = `scale(${scale}) translate(${pointX}px, ${pointY}px)`;
        });

        svg.addEventListener('mouseleave', () => {
            panning = false;
            svg.style.cursor = 'grab';
        });
    }

    exportDiagram(containerId, filename) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const svg = container.querySelector('svg');
        if (!svg) {
            toastManager?.error('No diagram to export') || alert('No diagram to export');
            return;
        }

        toastManager?.info('Generating PDF...', 2000);

        // Use html2canvas to screenshot the rendered diagram container directly.
        // This avoids all SVG-to-canvas foreignObject / CORS / taint issues.
        this._loadScript('https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js', 'html2canvas')
            .then(() => this._loadScript('https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.2/jspdf.umd.min.js', 'jspdf'))
            .then(() => {
                // Temporarily force white background on the container
                const prevBg = container.style.backgroundColor;
                container.style.backgroundColor = '#ffffff';

                // Reset any pan/zoom transforms on the SVG so we capture it cleanly
                const prevTransform = svg.style.transform;
                svg.style.transform = 'none';

                return html2canvas(container, {
                    backgroundColor: '#ffffff',
                    scale: 2,
                    useCORS: true,
                    logging: false,
                    allowTaint: true,
                }).then(canvas => {
                    // Restore original styles
                    container.style.backgroundColor = prevBg;
                    svg.style.transform = prevTransform;
                    return canvas;
                });
            })
            .then(canvas => {
                const { jsPDF } = window.jspdf;

                const imgW = canvas.width;
                const imgH = canvas.height;
                const padding = 40;
                const pdfW = imgW / 2 + padding * 2;   // /2 because scale:2
                const pdfH = imgH / 2 + padding * 2;

                const orientation = pdfW > pdfH ? 'landscape' : 'portrait';
                const pdf = new jsPDF({ orientation, unit: 'px', format: [pdfW, pdfH] });

                const imgData = canvas.toDataURL('image/png', 1.0);
                pdf.addImage(imgData, 'PNG', padding, padding, imgW / 2, imgH / 2);
                pdf.save(`${filename}-${Date.now()}.pdf`);

                toastManager?.success('Diagram exported as PDF!');
            })
            .catch(err => {
                console.error('PDF export failed:', err);
                toastManager?.error('PDF export failed — check console') || alert('PDF export failed');
            });
    }

    _loadScript(src, globalCheck) {
        // Load an external script once, return a promise
        return new Promise((resolve, reject) => {
            if (window[globalCheck]) { resolve(); return; }

            // Check if already loading
            const existing = document.querySelector(`script[src="${src}"]`);
            if (existing) {
                existing.addEventListener('load', () => resolve());
                existing.addEventListener('error', () => reject(new Error(`Failed to load ${src}`)));
                // If it already loaded between our check and listener
                if (window[globalCheck]) resolve();
                return;
            }

            const script = document.createElement('script');
            script.src = src;
            script.onload = () => resolve();
            script.onerror = () => reject(new Error(`Failed to load ${src}`));
            document.head.appendChild(script);
        });
    }

    showDiagramFullscreen(container, code) {
        // Create fullscreen overlay
        const overlay = document.createElement('div');
        overlay.className = 'diagram-fullscreen-overlay';

        overlay.innerHTML = `
            <div class="diagram-fullscreen-container">
                <div class="diagram-fullscreen-header">
                    <h3>📐 Architecture Diagram</h3>
                    <div class="diagram-fullscreen-actions">
                        <button class="diagram-fullscreen-btn" id="fs-zoom-in" title="Zoom In">➕</button>
                        <button class="diagram-fullscreen-btn" id="fs-zoom-out" title="Zoom Out">➖</button>
                        <button class="diagram-fullscreen-btn" id="fs-reset" title="Reset View">🔄</button>
                        <button class="diagram-fullscreen-btn" id="fs-export" title="Export PDF">⬇️</button>
                        <button class="diagram-fullscreen-btn close" id="fs-close" title="Close">✕</button>
                    </div>
                </div>
                <div class="diagram-fullscreen-content">
                    <div class="diagram-fullscreen-view" id="fs-diagram"></div>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);
        document.body.style.overflow = 'hidden';

        // Render diagram in fullscreen
        const fsDiagram = overlay.querySelector('#fs-diagram');
        const fsId = 'fs-mermaid-' + Date.now();
        fsDiagram.id = fsId;
        this.renderMermaidDiagram(fsDiagram, code, fsId);

        // Fullscreen controls
        let fsScale = 1;

        overlay.querySelector('#fs-zoom-in').onclick = () => {
            fsScale = Math.min(fsScale * 1.2, 3);
            const svg = fsDiagram.querySelector('svg');
            if (svg) svg.style.transform = `scale(${fsScale})`;
        };

        overlay.querySelector('#fs-zoom-out').onclick = () => {
            fsScale = Math.max(fsScale / 1.2, 0.5);
            const svg = fsDiagram.querySelector('svg');
            if (svg) svg.style.transform = `scale(${fsScale})`;
        };

        overlay.querySelector('#fs-reset').onclick = () => {
            fsScale = 1;
            const svg = fsDiagram.querySelector('svg');
            if (svg) svg.style.transform = 'scale(1)';
        };

        overlay.querySelector('#fs-export').onclick = () => {
            this.exportDiagram(fsId, 'architecture-diagram-fullscreen');
        };

        const closeFullscreen = () => {
            overlay.classList.add('closing');
            setTimeout(() => {
                overlay.remove();
                document.body.style.overflow = '';
            }, 300);
        };

        overlay.querySelector('#fs-close').onclick = closeFullscreen;
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) closeFullscreen();
        });

        document.addEventListener('keydown', function escHandler(e) {
            if (e.key === 'Escape') {
                closeFullscreen();
                document.removeEventListener('keydown', escHandler);
            }
        });

        // Animate in
        setTimeout(() => overlay.classList.add('active'), 10);
    }

    async typeWriterEffect(textDiv, fullText, messagesContainer) {
        // Initialize generation state
        this.isGenerating = true;
        this.isPaused = false;
        this.isStopped = false;
        this.currentGenerationText = fullText;
        this.currentGenerationIndex = 0;

        // Show generation controls
        this.showGenerationControls();

        // Add cursor element
        const cursor = document.createElement('span');
        cursor.className = 'typing-cursor';
        cursor.textContent = '▌';
        textDiv.appendChild(cursor);

        // Configure marked options
        marked.setOptions({
            breaks: true,
            gfm: true,
            headerIds: false,
            mangle: false
        });

        let currentText = '';
        let charIndex = 0;
        const speed = 5; // milliseconds per character (faster = lower number)
        const chunkSize = 3; // characters per update for smoother effect

        const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

        const typeNextChunk = async () => {
            while (charIndex < fullText.length) {
                // Check if stopped
                if (this.isStopped) {
                    // Remove cursor and show partial content
                    cursor.remove();
                    if (currentText.length > 0) {
                        this.renderMarkdown(textDiv, currentText + '\n\n*[Generation stopped]*');
                    }
                    this.finishGeneration();
                    return;
                }

                // Check if paused
                if (this.isPaused) {
                    // Add paused indicator to cursor
                    cursor.textContent = '⏸';
                    cursor.classList.add('paused');
                    await this.waitIfPaused();
                    cursor.textContent = '▌';
                    cursor.classList.remove('paused');

                    // Check if stopped while paused
                    if (this.isStopped) {
                        cursor.remove();
                        if (currentText.length > 0) {
                            this.renderMarkdown(textDiv, currentText + '\n\n*[Generation stopped]*');
                        }
                        this.finishGeneration();
                        return;
                    }
                }

                // Add next chunk of characters
                const endIndex = Math.min(charIndex + chunkSize, fullText.length);
                currentText = fullText.substring(0, endIndex);
                charIndex = endIndex;
                this.currentGenerationIndex = charIndex;

                // Parse and render current text
                const htmlContent = marked.parse(currentText);
                textDiv.innerHTML = htmlContent;

                // Add cursor back
                const lastElement = textDiv.lastElementChild || textDiv;
                if (lastElement.nodeType === Node.ELEMENT_NODE) {
                    lastElement.appendChild(cursor);
                } else {
                    textDiv.appendChild(cursor);
                }

                // Scroll to bottom
                messagesContainer.scrollTop = messagesContainer.scrollHeight;

                // Wait before next chunk
                await delay(speed);
            }

            // Typing complete - remove cursor and apply final formatting
            cursor.remove();
            this.renderMarkdown(textDiv, fullText);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            this.finishGeneration();
        };

        // Start typing
        await typeNextChunk();
    }

    finishGeneration() {
        this.isGenerating = false;
        this.isPaused = false;
        this.isStopped = false;
        this.pauseResolve = null;
        this.hideGenerationControls();

        // Render follow-up suggestion chips after typewriter finishes
        if (this.pendingSuggestions && this.pendingSuggestions.length > 0) {
            const messagesContainer = document.getElementById('chat-messages');
            const assistantMsgs = messagesContainer.querySelectorAll('.message.assistant');
            const lastAssistantMsg = assistantMsgs[assistantMsgs.length - 1];
            if (lastAssistantMsg) {
                this.renderFollowUpChips(lastAssistantMsg, this.pendingSuggestions);
            }
            this.pendingSuggestions = [];
        }
    }

    // ================================
    // CHAT HISTORY
    // ================================

    setupChatHistory() {
        const toggleBtn = document.getElementById('chat-history-toggle');
        const newChatBtn = document.getElementById('new-chat-btn');
        const list = document.getElementById('chat-history-list');
        const chevron = document.getElementById('chat-history-chevron');

        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                const isOpen = list.style.display !== 'none';
                list.style.display = isOpen ? 'none' : 'block';
                chevron.classList.toggle('open', !isOpen);
                if (!isOpen) this.loadChatHistory();
            });
        }

        if (newChatBtn) {
            newChatBtn.addEventListener('click', () => this.createNewChat());
        }
    }

    async loadChatHistory() {
        try {
            const response = await fetch('/api/chat/history');
            const data = await response.json();
            this.renderChatHistory(data.chats || []);
        } catch (error) {
            console.error('Error loading chat history:', error);
        }
    }

    renderChatHistory(chats) {
        const list = document.getElementById('chat-history-list');
        if (!list) return;

        if (chats.length === 0) {
            list.innerHTML = '<div class="chat-history-empty">No chats yet</div>';
            return;
        }

        list.innerHTML = chats.map(chat => `
            <div class="chat-history-item ${chat.is_active ? 'active' : ''}" data-chat-id="${chat.chat_id}">
                <svg class="chat-history-item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
                <div class="chat-history-item-content" onclick="laplacian.switchChat('${chat.chat_id}')">
                    <div class="chat-history-item-title">${this.escapeHtml(chat.title)}</div>
                    <div class="chat-history-item-meta">${chat.message_count} messages &middot; ${this.formatRelativeTime(chat.updated_at)}</div>
                </div>
                <button class="chat-history-item-delete" onclick="event.stopPropagation(); laplacian.deleteChatHistory('${chat.chat_id}')" title="Delete chat">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                </button>
            </div>
        `).join('');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatRelativeTime(isoString) {
        const date = new Date(isoString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    }

    async switchChat(chatId) {
        try {
            const response = await fetch('/api/chat/load', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ chat_id: chatId })
            });

            const data = await response.json();
            if (data.error) {
                console.error('Error loading chat:', data.error);
                return;
            }

            // Clear current messages and render loaded chat
            const messagesContainer = document.getElementById('chat-messages');
            messagesContainer.innerHTML = '';

            // Add welcome message
            const welcomeDiv = document.createElement('div');
            welcomeDiv.className = 'message assistant';
            welcomeDiv.innerHTML = `
                <div class="message-avatar ai-avatar">
                    <div class="ai-icon">
                        <div class="ai-core"></div>
                        <div class="ai-ring"></div>
                        <div class="ai-particles">
                            <span></span><span></span><span></span><span></span>
                        </div>
                    </div>
                </div>
                <div class="message-content">
                    <div class="message-text"><strong>Welcome to Laplacian</strong> — your private AI workspace by Perfionix AI.<br><br>I'm here to help you:<br>• <strong>Code</strong> — write, debug, and optimize with expert assistance<br>• <strong>Analyze</strong> — transform your data into actionable insights<br>• <strong>Research</strong> — extract knowledge from documents instantly<br>• <strong>Create</strong> — generate diagrams, visualizations, and more<br><br>How can I assist you today?</div>
                    <span class="message-time">${this.formatTime(new Date())}</span>
                </div>
            `;
            messagesContainer.appendChild(welcomeDiv);

            // Render loaded messages
            if (data.messages) {
                data.messages.forEach(msg => {
                    this.addMessageToUI(msg.content, msg.role, msg.index, false, false);
                });
            }

            // Refresh chat history to update active state
            this.loadChatHistory();

            // Switch to chat view if not already there
            this.switchView('chat');
        } catch (error) {
            console.error('Error switching chat:', error);
        }
    }

    async createNewChat() {
        try {
            await fetch('/api/chat/new', { method: 'POST' });
            // Reset the UI
            await this.resetChat();
            this.loadChatHistory();
        } catch (error) {
            console.error('Error creating new chat:', error);
        }
    }

    async deleteChatHistory(chatId) {
        try {
            const response = await fetch(`/api/chat/${chatId}`, { method: 'DELETE' });
            const data = await response.json();
            if (data.status === 'success') {
                this.loadChatHistory();
            }
        } catch (error) {
            console.error('Error deleting chat:', error);
        }
    }

    async resetChat() {
        try {
            await fetch('/api/chat/reset', { method: 'POST' });

            const messagesContainer = document.getElementById('chat-messages');
            messagesContainer.innerHTML = `
                <div class="message assistant">
                    <div class="message-avatar ai-avatar">
                        <div class="ai-icon">
                            <div class="ai-core"></div>
                            <div class="ai-ring"></div>
                            <div class="ai-particles">
                                <span></span><span></span><span></span><span></span>
                            </div>
                        </div>
                    </div>
                    <div class="message-content">
                        <div class="message-text"><strong>Welcome to Laplacian</strong> — your private AI workspace by Perfionix AI.<br><br>I'm here to help you:<br>• <strong>Code</strong> — write, debug, and optimize with expert assistance<br>• <strong>Analyze</strong> — transform your data into actionable insights<br>• <strong>Research</strong> — extract knowledge from documents instantly<br>• <strong>Create</strong> — generate diagrams, visualizations, and more<br><br>How can I assist you today?</div>
                        <span class="message-time">${this.formatTime(new Date())}</span>
                    </div>
                </div>
            `;
            // Refresh chat history sidebar
            const historyList = document.getElementById('chat-history-list');
            if (historyList && historyList.style.display !== 'none') {
                this.loadChatHistory();
            }
        } catch (error) {
            console.error('Error resetting chat:', error);
        }
    }

    // ================================
    // TASKS FUNCTIONALITY
    // ================================

    setupTasks() {
        const addBtn = document.getElementById('add-task');
        addBtn.addEventListener('click', () => this.showTaskModal());

        // Filter buttons
        const filterBtns = document.querySelectorAll('.filter-btn');
        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.filterTasks(btn.dataset.filter);
            });
        });
    }

    showTaskModal() {
        const modal = document.getElementById('modal');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');

        modalTitle.textContent = 'Add New Task';
        modalBody.innerHTML = `
            <div class="form-group">
                <label class="form-label">Task Title</label>
                <input type="text" class="form-input" id="task-title" placeholder="Enter task title...">
            </div>
            <div class="form-group">
                <label class="form-label">Priority</label>
                <select class="form-select" id="task-priority">
                    <option value="low">Low</option>
                    <option value="medium" selected>Medium</option>
                    <option value="high">High</option>
                </select>
            </div>
            <div class="form-actions">
                <button class="btn-secondary" onclick="laplacian.closeModal()">Cancel</button>
                <button class="btn-primary" onclick="laplacian.saveTask()">Add Task</button>
            </div>
        `;

        modal.classList.add('active');
    }

    async saveTask() {
        const title = document.getElementById('task-title').value.trim();
        const priority = document.getElementById('task-priority').value;

        if (!title) return;

        try {
            const response = await fetch('/api/tasks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, priority })
            });

            const task = await response.json();
            this.tasks.push(task);
            this.renderTasks();
            this.closeModal();
            this.updateStats();
        } catch (error) {
            console.error('Error saving task:', error);
        }
    }

    async toggleTask(taskId) {
        const task = this.tasks.find(t => t.id === taskId);
        if (!task) return;

        task.completed = !task.completed;

        try {
            await fetch('/api/tasks', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(task)
            });

            this.renderTasks();
            this.updateStats();
        } catch (error) {
            console.error('Error updating task:', error);
        }
    }

    async deleteTask(taskId) {
        try {
            await fetch('/api/tasks', {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: taskId })
            });

            this.tasks = this.tasks.filter(t => t.id !== taskId);
            this.renderTasks();
            this.updateStats();
        } catch (error) {
            console.error('Error deleting task:', error);
        }
    }

    renderTasks(filter = 'all') {
        const container = document.getElementById('tasks-list');
        let tasksToShow = this.tasks;

        if (filter === 'pending') {
            tasksToShow = this.tasks.filter(t => !t.completed);
        } else if (filter === 'completed') {
            tasksToShow = this.tasks.filter(t => t.completed);
        }

        if (tasksToShow.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📋</div>
                    <p>No tasks found.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = tasksToShow.map(task => `
            <div class="task-item ${task.completed ? 'completed' : ''}">
                <div class="task-checkbox" onclick="laplacian.toggleTask('${task.id}')"></div>
                <div class="task-content">
                    <div class="task-title">${this.escapeHtml(task.title)}</div>
                </div>
                <span class="task-priority ${task.priority}">${task.priority}</span>
                <button class="task-delete" onclick="laplacian.deleteTask('${task.id}')">×</button>
            </div>
        `).join('');
    }

    filterTasks(filter) {
        this.renderTasks(filter);
    }

    // ================================
    // NOTES FUNCTIONALITY
    // ================================

    setupNotes() {
        const addBtn = document.getElementById('add-note');
        addBtn.addEventListener('click', () => this.showNoteModal());
    }

    showNoteModal(note = null) {
        const modal = document.getElementById('modal');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');

        modalTitle.textContent = note ? 'Edit Note' : 'New Note';
        modalBody.innerHTML = `
            <div class="form-group">
                <label class="form-label">Title</label>
                <input type="text" class="form-input" id="note-title" placeholder="Note title..." value="${note ? this.escapeHtml(note.title) : ''}">
            </div>
            <div class="form-group">
                <label class="form-label">Content</label>
                <textarea class="form-textarea" id="note-content" placeholder="Write your note here...">${note ? this.escapeHtml(note.content) : ''}</textarea>
            </div>
            <div class="form-actions">
                <button class="btn-secondary" onclick="laplacian.closeModal()">Cancel</button>
                <button class="btn-primary" onclick="laplacian.saveNote()">Save Note</button>
            </div>
        `;

        modal.classList.add('active');
    }

    async saveNote() {
        const title = document.getElementById('note-title').value.trim();
        const content = document.getElementById('note-content').value.trim();

        if (!title || !content) return;

        try {
            const response = await fetch('/api/notes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, content })
            });

            const note = await response.json();
            this.notes.push(note);
            this.renderNotes();
            this.closeModal();
            this.updateStats();
        } catch (error) {
            console.error('Error saving note:', error);
        }
    }

    async deleteNote(noteId) {
        try {
            await fetch('/api/notes', {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: noteId })
            });

            this.notes = this.notes.filter(n => n.id !== noteId);
            this.renderNotes();
            this.updateStats();
        } catch (error) {
            console.error('Error deleting note:', error);
        }
    }

    renderNotes() {
        const container = document.getElementById('notes-grid');

        if (this.notes.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📝</div>
                    <p>No notes yet. Start writing!</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.notes.map(note => `
            <div class="note-card">
                <div class="note-header">
                    <h3 class="note-title">${this.escapeHtml(note.title)}</h3>
                    <button class="note-delete" onclick="laplacian.deleteNote('${note.id}')">×</button>
                </div>
                <p class="note-content">${this.escapeHtml(note.content)}</p>
                <div class="note-time">${this.formatTime(new Date(note.created))}</div>
            </div>
        `).join('');
    }

    // ================================
    // REMINDERS FUNCTIONALITY
    // ================================

    setupReminders() {
        const addBtn = document.getElementById('add-reminder');
        addBtn.addEventListener('click', () => this.showReminderModal());

        // Initialize reminder alarm system
        this.triggeredReminders = new Set();
        this.initReminderAlarm();

        // Start checking reminders every 10 seconds
        this.startReminderChecker();
    }

    initReminderAlarm() {
        // Create audio context for alarm sound
        this.audioContext = null;

        // Request notification permission
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }

    startReminderChecker() {
        // Check reminders every 10 seconds
        this.reminderInterval = setInterval(() => {
            this.checkReminders();
        }, 10000);

        // Also check immediately
        setTimeout(() => this.checkReminders(), 2000);
    }

    checkReminders() {
        const now = new Date();

        this.reminders.forEach(reminder => {
            const reminderTime = new Date(reminder.datetime);
            const timeDiff = reminderTime - now;

            // Check if reminder is due (within 30 seconds window) and not already triggered
            if (timeDiff <= 30000 && timeDiff > -60000 && !this.triggeredReminders.has(reminder.id)) {
                this.triggerReminder(reminder);
                this.triggeredReminders.add(reminder.id);
            }
        });
    }

    triggerReminder(reminder) {
        // Play alarm sound
        this.playAlarmSound();

        // Show notification popup
        this.showReminderNotification(reminder);

        // Show browser notification if permitted
        this.showBrowserNotification(reminder);
    }

    playAlarmSound() {
        try {
            // Create audio context if not exists
            if (!this.audioContext) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }

            const ctx = this.audioContext;
            const duration = 0.15;
            const frequency = 800;

            // Play a pleasant notification sound (3 beeps)
            for (let i = 0; i < 3; i++) {
                setTimeout(() => {
                    const oscillator = ctx.createOscillator();
                    const gainNode = ctx.createGain();

                    oscillator.connect(gainNode);
                    gainNode.connect(ctx.destination);

                    oscillator.frequency.value = frequency + (i * 100);
                    oscillator.type = 'sine';

                    gainNode.gain.setValueAtTime(0.3, ctx.currentTime);
                    gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + duration);

                    oscillator.start(ctx.currentTime);
                    oscillator.stop(ctx.currentTime + duration);
                }, i * 200);
            }
        } catch (error) {
            console.log('Audio not supported:', error);
        }
    }

    showReminderNotification(reminder) {
        // Create notification popup
        const notification = document.createElement('div');
        notification.className = 'reminder-notification';
        notification.innerHTML = `
            <div class="reminder-notification-content">
                <div class="reminder-notification-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                        <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                    </svg>
                </div>
                <div class="reminder-notification-text">
                    <div class="reminder-notification-title">Reminder!</div>
                    <div class="reminder-notification-message">${this.escapeHtml(reminder.title)}</div>
                    <div class="reminder-notification-time">${this.formatDateTime(new Date(reminder.datetime))}</div>
                </div>
                <button class="reminder-notification-close" onclick="this.parentElement.parentElement.remove()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
            <div class="reminder-notification-actions">
                <button class="btn-dismiss" onclick="laplacian.dismissReminderNotification(this, '${reminder.id}')">Dismiss</button>
                <button class="btn-snooze" onclick="laplacian.snoozeReminder('${reminder.id}', 5)">Snooze 5 min</button>
            </div>
        `;

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => notification.classList.add('active'), 10);

        // Auto remove after 30 seconds if not dismissed
        setTimeout(() => {
            if (notification.parentElement) {
                notification.classList.remove('active');
                setTimeout(() => notification.remove(), 300);
            }
        }, 30000);
    }

    showBrowserNotification(reminder) {
        if ('Notification' in window && Notification.permission === 'granted') {
            const notification = new Notification('Laplacian Reminder', {
                body: reminder.title,
                tag: reminder.id,
                requireInteraction: true
            });

            notification.onclick = () => {
                window.focus();
                this.switchView('reminders');
                notification.close();
            };
        }
    }

    dismissReminderNotification(button, reminderId) {
        const notification = button.closest('.reminder-notification');
        notification.classList.remove('active');
        setTimeout(() => notification.remove(), 300);
    }

    async snoozeReminder(reminderId, minutes) {
        // Find the reminder
        const reminder = this.reminders.find(r => r.id === reminderId);
        if (!reminder) return;

        // Calculate new time
        const newTime = new Date(Date.now() + minutes * 60 * 1000);

        // Remove from triggered set so it can trigger again
        this.triggeredReminders.delete(reminderId);

        // Update reminder time
        reminder.datetime = newTime.toISOString();

        // Close notification
        const notification = document.querySelector('.reminder-notification');
        if (notification) {
            notification.classList.remove('active');
            setTimeout(() => notification.remove(), 300);
        }

        // Show toast
        this.showToast(`Reminder snoozed for ${minutes} minutes`, 'success');

        // Re-render reminders
        this.renderReminders();
    }

    showReminderModal() {
        const modal = document.getElementById('modal');
        const modalTitle = document.getElementById('modal-title');
        const modalBody = document.getElementById('modal-body');

        const now = new Date();
        const dateStr = now.toISOString().slice(0, 16);

        modalTitle.textContent = 'Add Reminder';
        modalBody.innerHTML = `
            <div class="form-group">
                <label class="form-label">Reminder Title</label>
                <input type="text" class="form-input" id="reminder-title" placeholder="What do you want to be reminded about?">
            </div>
            <div class="form-group">
                <label class="form-label">Date & Time</label>
                <input type="datetime-local" class="form-input" id="reminder-datetime" value="${dateStr}">
            </div>
            <div class="form-actions">
                <button class="btn-secondary" onclick="laplacian.closeModal()">Cancel</button>
                <button class="btn-primary" onclick="laplacian.saveReminder()">Add Reminder</button>
            </div>
        `;

        modal.classList.add('active');
    }

    async saveReminder() {
        const title = document.getElementById('reminder-title').value.trim();
        const datetime = document.getElementById('reminder-datetime').value;

        if (!title || !datetime) return;

        try {
            const response = await fetch('/api/reminders', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, datetime })
            });

            const reminder = await response.json();
            this.reminders.push(reminder);
            this.renderReminders();
            this.closeModal();
            this.updateStats();
        } catch (error) {
            console.error('Error saving reminder:', error);
        }
    }

    async deleteReminder(reminderId) {
        try {
            await fetch('/api/reminders', {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: reminderId })
            });

            this.reminders = this.reminders.filter(r => r.id !== reminderId);
            this.renderReminders();
            this.updateStats();
        } catch (error) {
            console.error('Error deleting reminder:', error);
        }
    }

    renderReminders() {
        const container = document.getElementById('reminders-list');

        if (this.reminders.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">⏰</div>
                    <p>No reminders set. Add one to stay organized!</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.reminders.map(reminder => `
            <div class="reminder-item">
                <div class="reminder-icon">⏰</div>
                <div class="reminder-content">
                    <div class="reminder-title">${this.escapeHtml(reminder.title)}</div>
                    <div class="reminder-datetime">${this.formatDateTime(new Date(reminder.datetime))}</div>
                </div>
                <button class="reminder-delete" onclick="laplacian.deleteReminder('${reminder.id}')">×</button>
            </div>
        `).join('');
    }

    // ================================
    // DOCIQ - DOCUMENT INTELLIGENCE
    // ================================

    setupDocIQ() {
        const uploadArea = document.getElementById('upload-area');
        const fileInput = document.getElementById('doc-file-input');
        const browseBtn = document.getElementById('browse-files');
        const clearDocsBtn = document.getElementById('clear-docs');
        const dociqInput = document.getElementById('dociq-input');
        const dociqSend = document.getElementById('dociq-send');

        // Browse button click
        browseBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            fileInput.click();
        });

        // Upload area click
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });

        // File input change
        fileInput.addEventListener('change', (e) => {
            this.handleDocIQFiles(e.target.files);
            fileInput.value = ''; // Reset input
        });

        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            this.handleDocIQFiles(e.dataTransfer.files);
        });

        // Clear documents button
        clearDocsBtn.addEventListener('click', () => this.clearDocIQDocuments());

        // Chat input
        dociqSend.addEventListener('click', () => this.sendDocIQMessage());

        dociqInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendDocIQMessage();
            }
        });

        // Auto-resize textarea
        dociqInput.addEventListener('input', () => {
            dociqInput.style.height = 'auto';
            dociqInput.style.height = dociqInput.scrollHeight + 'px';
        });

        // Load existing documents
        this.loadDocIQDocuments();
    }

    async handleDocIQFiles(files) {
        for (const file of files) {
            await this.uploadDocIQFile(file);
        }
    }

    async uploadDocIQFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        // Add temporary document entry with processing status
        const tempId = 'temp-' + Date.now();
        this.addDocumentToList({
            id: tempId,
            name: file.name,
            extension: file.name.split('.').pop().toLowerCase(),
            size: file.size,
            status: 'processing'
        });

        try {
            const response = await fetch('/api/dociq/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            // Remove temporary entry
            this.removeDocumentFromList(tempId);

            if (data.success) {
                // Add the actual document
                this.dociqDocuments.push(data.document);
                this.addDocumentToList(data.document);
                this.updateDocIQChatState();

                // Add success message to chat
                this.addDocIQMessage(`Document "${data.document.name}" uploaded successfully! (${this.formatFileSize(data.document.size)}, ${data.document.chunk_count} sections extracted)`, 'system');
            } else {
                this.addDocIQMessage(`Failed to upload "${file.name}": ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.removeDocumentFromList(tempId);
            this.addDocIQMessage(`Error uploading "${file.name}": ${error.message}`, 'error');
        }
    }

    addDocumentToList(doc) {
        const docsList = document.getElementById('docs-list');

        // Remove "no documents" message if present
        const noDocsMsg = docsList.querySelector('.no-docs');
        if (noDocsMsg) noDocsMsg.remove();

        const docItem = document.createElement('div');
        docItem.className = `doc-item ${doc.status === 'processing' ? 'processing' : ''}`;
        docItem.id = `doc-${doc.id}`;

        const iconClass = doc.extension === 'pdf' ? 'pdf' : (doc.extension === 'doc' || doc.extension === 'docx') ? 'word' : '';

        docItem.innerHTML = `
            <div class="doc-icon ${iconClass}">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                </svg>
            </div>
            <div class="doc-info">
                <div class="doc-name" title="${doc.name}">${doc.name}</div>
                <div class="doc-size">${this.formatFileSize(doc.size)}</div>
            </div>
            <span class="doc-status ${doc.status}">${doc.status === 'processing' ? '⏳ Processing' : '✓ Ready'}</span>
            <button class="doc-remove" onclick="laplacian.removeDocIQDocument('${doc.id}')" title="Remove document">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
        `;

        docsList.appendChild(docItem);
    }

    removeDocumentFromList(docId) {
        const docItem = document.getElementById(`doc-${docId}`);
        if (docItem) {
            docItem.remove();
        }

        // Show "no documents" if list is empty
        const docsList = document.getElementById('docs-list');
        if (docsList.children.length === 0) {
            docsList.innerHTML = '<p class="no-docs">No documents uploaded yet</p>';
        }
    }

    async removeDocIQDocument(docId) {
        try {
            const response = await fetch(`/api/dociq/documents/${docId}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (data.success) {
                this.dociqDocuments = this.dociqDocuments.filter(d => d.id !== docId);
                this.removeDocumentFromList(docId);
                this.updateDocIQChatState();
            }
        } catch (error) {
            console.error('Error removing document:', error);
        }
    }

    async clearDocIQDocuments() {
        if (!confirm('Are you sure you want to clear all documents and chat history?')) return;

        try {
            const response = await fetch('/api/dociq/clear', {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                this.dociqDocuments = [];
                const docsList = document.getElementById('docs-list');
                docsList.innerHTML = '<p class="no-docs">No documents uploaded yet</p>';
                this.updateDocIQChatState();
                this.resetDocIQChat();
            }
        } catch (error) {
            console.error('Error clearing documents:', error);
        }
    }

    async loadDocIQDocuments() {
        try {
            const response = await fetch('/api/dociq/documents');
            const data = await response.json();

            if (data.documents && data.documents.length > 0) {
                this.dociqDocuments = data.documents;
                const docsList = document.getElementById('docs-list');
                docsList.innerHTML = '';

                for (const doc of data.documents) {
                    this.addDocumentToList(doc);
                }

                this.updateDocIQChatState();
            }
        } catch (error) {
            console.error('Error loading documents:', error);
        }
    }

    updateDocIQChatState() {
        const dociqInput = document.getElementById('dociq-input');
        const dociqSend = document.getElementById('dociq-send');
        const inputHint = document.querySelector('.dociq-input-container .input-hint');

        const hasDocuments = this.dociqDocuments.length > 0;

        dociqInput.disabled = !hasDocuments;
        dociqSend.disabled = !hasDocuments;

        if (hasDocuments) {
            dociqInput.placeholder = `Ask about your ${this.dociqDocuments.length} document(s)...`;
            inputHint.textContent = 'Press Enter to send your question';
        } else {
            dociqInput.placeholder = 'Ask a question about your documents...';
            inputHint.textContent = 'Upload documents first to enable chat';
        }

        // Update badge
        const dociqBadge = document.getElementById('dociq-badge');
        if (dociqBadge) {
            dociqBadge.textContent = hasDocuments ? this.dociqDocuments.length : 'AI';
        }
    }

    // Handle DocIQ suggestion chip clicks
    useDocIQSuggestion(text) {
        const input = document.getElementById('dociq-input');

        // Check if documents are uploaded
        if (this.dociqDocuments.length === 0) {
            this.addDocIQMessage('Please upload a document first to use this feature.', 'error');
            return;
        }

        input.value = text;
        input.focus();
        input.style.height = 'auto';
        input.style.height = input.scrollHeight + 'px';

        // Auto-send the message
        this.sendDocIQMessage();
    }

    async sendDocIQMessage() {
        const input = document.getElementById('dociq-input');
        const message = input.value.trim();

        if (!message || this.dociqDocuments.length === 0) return;

        // Add user message to UI
        this.addDocIQMessageToUI(message, 'user');
        input.value = '';
        input.style.height = 'auto';

        // Show typing indicator
        this.showDocIQTypingIndicator();

        try {
            const response = await fetch('/api/dociq/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });

            const data = await response.json();

            // Remove typing indicator
            this.removeDocIQTypingIndicator();

            if (data.response) {
                this.addDocIQMessageToUI(data.response, 'assistant', true);
            } else if (data.error) {
                this.addDocIQMessage(`Error: ${data.error}`, 'error');
            }
        } catch (error) {
            this.removeDocIQTypingIndicator();
            this.addDocIQMessage('Connection error. Please try again.', 'error');
        }
    }

    addDocIQMessage(message, type = 'system') {
        const messagesContainer = document.getElementById('dociq-messages');
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${type === 'error' ? 'error-message' : 'system-message'}`;

        msgDiv.innerHTML = `
            <div class="message-content">
                <div class="message-text" style="color: ${type === 'error' ? '#f5576c' : 'var(--text-secondary)'}; font-style: italic;">
                    ${type === 'error' ? '⚠️ ' : 'ℹ️ '}${message}
                </div>
                <span class="message-time">${this.formatTime(new Date())}</span>
            </div>
        `;

        messagesContainer.appendChild(msgDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    addDocIQMessageToUI(text, role, typeEffect = false) {
        const messagesContainer = document.getElementById('dociq-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const avatar = document.createElement('div');
        avatar.className = role === 'user' ? 'message-avatar' : 'message-avatar ai-avatar';

        if (role === 'user') {
            avatar.textContent = '👤';
        } else {
            avatar.innerHTML = `
                <div class="ai-icon">
                    <div class="ai-core"></div>
                    <div class="ai-ring"></div>
                    <div class="ai-particles">
                        <span></span><span></span><span></span><span></span>
                    </div>
                </div>
            `;
        }

        const content = document.createElement('div');
        content.className = 'message-content';

        // Add document context indicator for assistant messages
        if (role === 'assistant') {
            const contextIndicator = document.createElement('div');
            contextIndicator.className = 'dociq-context';
            contextIndicator.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                </svg>
                Based on ${this.dociqDocuments.length} document(s)
            `;
            content.appendChild(contextIndicator);
        }

        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';

        if (role === 'assistant' && typeEffect) {
            this.typeWriterEffect(textDiv, text, messagesContainer);
        } else if (role === 'assistant') {
            this.renderMarkdown(textDiv, text);
        } else {
            textDiv.textContent = text;
        }

        const time = document.createElement('span');
        time.className = 'message-time';
        time.textContent = this.formatTime(new Date());

        content.appendChild(textDiv);
        content.appendChild(time);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    showDocIQTypingIndicator() {
        const messagesContainer = document.getElementById('dociq-messages');
        const indicator = document.createElement('div');
        indicator.className = 'message assistant typing-indicator-message';
        indicator.id = 'dociq-typing-indicator';

        indicator.innerHTML = `
            <div class="message-avatar ai-avatar loading">
                <div class="ai-icon">
                    <div class="ai-core"></div>
                    <div class="ai-ring"></div>
                    <div class="ai-particles">
                        <span></span><span></span><span></span><span></span>
                    </div>
                </div>
            </div>
            <div class="message-content">
                <div class="dociq-context">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                    </svg>
                    Analyzing documents...
                </div>
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;

        messagesContainer.appendChild(indicator);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    removeDocIQTypingIndicator() {
        const indicator = document.getElementById('dociq-typing-indicator');
        if (indicator) indicator.remove();
    }

    resetDocIQChat() {
        const messagesContainer = document.getElementById('dociq-messages');
        messagesContainer.innerHTML = `
            <div class="message assistant">
                <div class="message-avatar ai-avatar">
                    <div class="ai-icon">
                        <div class="ai-core"></div>
                        <div class="ai-ring"></div>
                        <div class="ai-particles">
                            <span></span><span></span><span></span><span></span>
                        </div>
                    </div>
                </div>
                <div class="message-content">
                    <div class="message-text">
                        <strong>Welcome to DocIQ</strong> — Your Intelligent Document Assistant<br><br>
                        Upload your documents and unlock instant insights. I can read, analyze, and answer questions about your files in seconds.<br><br>
                        <strong>Supported formats:</strong> PDF, DOCX, TXT (up to 16MB)<br><br>
                        <strong>What I can do:</strong><br>
                        • <strong>Summarize</strong> — Get concise overviews of lengthy documents<br>
                        • <strong>Extract</strong> — Pull specific data, quotes, or key points<br>
                        • <strong>Analyze</strong> — Understand patterns and insights<br>
                        • <strong>Compare</strong> — Cross-reference multiple documents
                    </div>
                    <div class="suggestion-chips">
                        <button class="suggestion-chip" onclick="laplacian.useDocIQSuggestion('Summarize this document in 5 key points')">
                            <span class="chip-icon">📝</span> Summarize
                        </button>
                        <button class="suggestion-chip" onclick="laplacian.useDocIQSuggestion('What are the main topics covered?')">
                            <span class="chip-icon">🎯</span> Key Topics
                        </button>
                        <button class="suggestion-chip" onclick="laplacian.useDocIQSuggestion('Extract all important dates and numbers')">
                            <span class="chip-icon">📊</span> Extract Data
                        </button>
                    </div>
                    <span class="message-time">${this.formatTime(new Date())}</span>
                </div>
            </div>
        `;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // ================================
    // VIZIQ - DATA INTELLIGENCE
    // ================================

    setupVizIQ() {
        const uploadArea = document.getElementById('viziq-upload-area');
        const fileInput = document.getElementById('viziq-file-input');
        const browseBtn = document.getElementById('viziq-browse-files');
        const clearBtn = document.getElementById('clear-viziq');
        const refreshBtn = document.getElementById('refresh-viziq');

        // Browse button click
        browseBtn?.addEventListener('click', (e) => {
            e.stopPropagation();
            fileInput.click();
        });

        // Upload area click
        uploadArea?.addEventListener('click', () => {
            fileInput.click();
        });

        // File input change
        fileInput?.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.uploadVizIQFile(e.target.files[0]);
            }
            fileInput.value = '';
        });

        // Drag and drop
        uploadArea?.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('drag-over');
        });

        uploadArea?.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
        });

        uploadArea?.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('drag-over');
            if (e.dataTransfer.files.length > 0) {
                this.uploadVizIQFile(e.dataTransfer.files[0]);
            }
        });

        // Clear button
        clearBtn?.addEventListener('click', () => this.clearVizIQ());

        // Refresh button
        refreshBtn?.addEventListener('click', () => {
            if (this.viziqData) {
                this.renderVizIQDashboard(this.viziqData);
            }
        });
    }

    async uploadVizIQFile(file) {
        const uploadSection = document.getElementById('viziq-upload-section');
        const uploadArea = document.getElementById('viziq-upload-area');
        const processing = document.getElementById('viziq-processing');
        const dashboard = document.getElementById('viziq-dashboard');

        // Show processing
        uploadArea.style.display = 'none';
        processing.style.display = 'block';

        // Animate processing steps
        this.animateProcessingSteps();

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/viziq/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                this.viziqData = data;

                // Hide upload, show dashboard
                uploadSection.style.display = 'none';
                dashboard.style.display = 'flex';

                // Render dashboard
                this.renderVizIQDashboard(data);

                // Update badge
                document.getElementById('viziq-badge').textContent = data.rows;
            } else {
                alert('Error: ' + data.error);
                uploadArea.style.display = 'block';
                processing.style.display = 'none';
            }
        } catch (error) {
            console.error('VizIQ upload error:', error);
            alert('Failed to upload file. Please try again.');
            uploadArea.style.display = 'block';
            processing.style.display = 'none';
        }
    }

    animateProcessingSteps() {
        const steps = ['step-upload', 'step-preprocess', 'step-analyze', 'step-visualize'];
        const statusText = document.getElementById('processing-status');
        const messages = [
            'Uploading your data...',
            'Preprocessing and cleaning...',
            'Analyzing patterns and trends...',
            'Generating visualizations...'
        ];

        let currentStep = 0;

        const interval = setInterval(() => {
            if (currentStep > 0) {
                document.getElementById(steps[currentStep - 1])?.classList.remove('active');
                document.getElementById(steps[currentStep - 1])?.classList.add('completed');
            }

            if (currentStep < steps.length) {
                document.getElementById(steps[currentStep])?.classList.add('active');
                statusText.textContent = messages[currentStep];
                currentStep++;
            } else {
                clearInterval(interval);
            }
        }, 600);
    }

    renderVizIQDashboard(data) {
        // Update header
        document.getElementById('dashboard-name').textContent = data.dashboard_name;
        document.getElementById('dashboard-description').textContent = data.description;
        document.getElementById('data-rows').innerHTML = `<strong>${data.rows.toLocaleString()}</strong> Rows`;
        document.getElementById('data-cols').innerHTML = `<strong>${data.cols}</strong> Columns`;
        document.getElementById('data-updated').textContent = `Updated: ${new Date().toLocaleTimeString()}`;

        // Render KPIs
        this.renderKPIs(data.kpis);

        // Render Charts
        this.renderCharts(data.charts);

        // Render Insights
        this.renderInsights(data.insights);

        // Render Data Preview
        this.renderDataPreview(data.columns, data.preview, 1);
    }

    renderKPIs(kpis) {
        const grid = document.getElementById('kpi-grid');
        grid.innerHTML = '';

        const icons = {
            'database': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"></ellipse><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"></path><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"></path></svg>',
            'trending-up': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>',
            'bar-chart': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="20" x2="12" y2="10"></line><line x1="18" y1="20" x2="18" y2="4"></line><line x1="6" y1="20" x2="6" y2="16"></line></svg>',
            'layers': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>'
        };

        kpis.forEach(kpi => {
            const card = document.createElement('div');
            card.className = 'kpi-card';

            card.innerHTML = `
                <div class="kpi-header">
                    <span class="kpi-label">${kpi.label}</span>
                    <div class="kpi-icon">${icons[kpi.icon] || icons['bar-chart']}</div>
                </div>
                <div class="kpi-value">${this.formatKPIValue(kpi.value)}</div>
                <div class="kpi-description">${kpi.description}</div>
            `;

            grid.appendChild(card);
        });
    }

    formatKPIValue(value) {
        if (typeof value !== 'number') return value;
        if (value >= 1000000) return (value / 1000000).toFixed(1) + 'M';
        if (value >= 1000) return (value / 1000).toFixed(1) + 'K';
        return value.toLocaleString();
    }

    renderCharts(charts) {
        const grid = document.getElementById('charts-grid');
        grid.innerHTML = '';

        // Destroy existing charts
        this.viziqCharts.forEach(chart => chart.destroy());
        this.viziqCharts = [];

        const colors = this.getChartColors();

        charts.forEach((chartConfig, index) => {
            const card = document.createElement('div');
            card.className = 'chart-card' + (chartConfig.type === 'line' ? ' full-width' : '');

            const canvasId = `chart-${chartConfig.id}-${index}`;

            card.innerHTML = `
                <div class="chart-header">
                    <span class="chart-title">${chartConfig.title}</span>
                    <span class="chart-type-badge">${chartConfig.type}</span>
                </div>
                <div class="chart-container">
                    <canvas id="${canvasId}"></canvas>
                </div>
                <div class="chart-insight">
                    <p><strong>Insight:</strong> ${chartConfig.insight}</p>
                </div>
            `;

            grid.appendChild(card);

            // Create chart after DOM update
            setTimeout(() => {
                const ctx = document.getElementById(canvasId);
                if (ctx) {
                    const chart = this.createChart(ctx, chartConfig, colors);
                    this.viziqCharts.push(chart);
                }
            }, 100);
        });

        // Resize charts on window resize for mobile responsiveness
        window.addEventListener('resize', () => {
            this.viziqCharts.forEach(chart => {
                if (chart && chart.resize) {
                    chart.resize();
                }
            });
        });
    }

    getChartColors() {
        return {
            primary: 'rgba(102, 126, 234, 0.8)',
            secondary: 'rgba(118, 75, 162, 0.8)',
            success: 'rgba(0, 242, 254, 0.8)',
            danger: 'rgba(245, 87, 108, 0.8)',
            warning: 'rgba(254, 225, 64, 0.8)',
            gradient: [
                'rgba(102, 126, 234, 0.8)',
                'rgba(118, 75, 162, 0.8)',
                'rgba(0, 242, 254, 0.8)',
                'rgba(245, 87, 108, 0.8)',
                'rgba(254, 225, 64, 0.8)',
                'rgba(79, 172, 254, 0.8)',
                'rgba(240, 147, 251, 0.8)',
                'rgba(250, 112, 154, 0.8)'
            ]
        };
    }

    createChart(ctx, config, colors) {
        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: config.type === 'doughnut' || config.datasets,
                    position: 'bottom',
                    labels: {
                        color: 'rgba(255, 255, 255, 0.7)',
                        padding: 15,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(26, 27, 46, 0.95)',
                    titleColor: '#fff',
                    bodyColor: 'rgba(255, 255, 255, 0.8)',
                    borderColor: 'rgba(102, 126, 234, 0.3)',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        label: function (context) {
                            let label = context.dataset.label || context.label || '';
                            let value = context.parsed.y !== undefined ? context.parsed.y : context.parsed;
                            if (typeof value === 'number') {
                                value = value.toLocaleString();
                            }
                            return `${label}: ${value}`;
                        }
                    }
                }
            },
            scales: config.type !== 'doughnut' ? {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.6)',
                        maxRotation: 45
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.6)'
                    }
                }
            } : undefined
        };

        let chartData;

        if (config.datasets) {
            // Multi-dataset chart
            chartData = {
                labels: config.labels,
                datasets: config.datasets.map((ds, i) => ({
                    label: ds.label,
                    data: ds.data,
                    backgroundColor: colors.gradient[i % colors.gradient.length],
                    borderColor: colors.gradient[i % colors.gradient.length],
                    borderWidth: 2
                }))
            };
        } else {
            // Single dataset chart
            chartData = {
                labels: config.labels,
                datasets: [{
                    data: config.data,
                    backgroundColor: config.type === 'doughnut'
                        ? colors.gradient.slice(0, config.data.length)
                        : colors.primary,
                    borderColor: config.type === 'line' ? colors.primary : 'transparent',
                    borderWidth: config.type === 'line' ? 3 : 1,
                    fill: config.type === 'line' ? {
                        target: 'origin',
                        above: 'rgba(102, 126, 234, 0.1)'
                    } : false,
                    tension: 0.4,
                    pointBackgroundColor: colors.primary,
                    pointBorderColor: '#fff',
                    pointHoverRadius: 8
                }]
            };
        }

        return new Chart(ctx, {
            type: config.type,
            data: chartData,
            options: chartOptions
        });
    }

    renderInsights(insights) {
        const list = document.getElementById('insights-list');
        list.innerHTML = '';

        insights.forEach(insight => {
            const card = document.createElement('div');
            card.className = 'insight-card';

            card.innerHTML = `
                <div class="insight-icon ${insight.type}">${insight.icon}</div>
                <div class="insight-content">
                    <h5>${insight.title}</h5>
                    <p>${insight.description}</p>
                </div>
            `;

            list.appendChild(card);
        });
    }

    renderDataPreview(columns, data, page = 1) {
        const thead = document.getElementById('table-header');
        const tbody = document.getElementById('table-body');
        const pagination = document.getElementById('pagination-controls');

        // Render header
        thead.innerHTML = `<tr>${columns.map(col => `<th>${col}</th>`).join('')}</tr>`;

        // Pagination setup
        const rowsPerPage = 10;
        const totalRows = data.length;
        const totalPages = Math.ceil(totalRows / rowsPerPage);

        // Ensure valid page
        page = Math.max(1, Math.min(page, Math.max(1, totalPages)));

        const startIdx = (page - 1) * rowsPerPage;
        const endIdx = startIdx + rowsPerPage;
        const pageData = data.slice(startIdx, endIdx);

        // Render body
        tbody.innerHTML = pageData.map(row =>
            `<tr>${columns.map(col => `<td>${row[col] !== null && row[col] !== undefined ? row[col] : '-'}</td>`).join('')}</tr>`
        ).join('');

        // Render pagination controls
        if (totalPages > 1) {
            pagination.style.display = 'flex';
            let buttonsHtml = '';

            // Previous button
            buttonsHtml += `<button class="page-btn ${page === 1 ? 'disabled' : ''}" data-page="${page - 1}">«</button>`;

            // Calculate page range to show (max 5 buttons)
            let startPage = Math.max(1, page - 2);
            let endPage = Math.min(totalPages, startPage + 4);
            if (endPage - startPage < 4) {
                startPage = Math.max(1, endPage - 4);
            }

            for (let i = startPage; i <= endPage; i++) {
                buttonsHtml += `<button class="page-btn ${i === page ? 'active' : ''}" data-page="${i}">${i}</button>`;
            }

            // Next button
            buttonsHtml += `<button class="page-btn ${page === totalPages ? 'disabled' : ''}" data-page="${page + 1}">»</button>`;

            pagination.innerHTML = buttonsHtml;

            // Add event listeners to buttons
            pagination.querySelectorAll('.page-btn').forEach(btn => {
                if (!btn.classList.contains('disabled')) {
                    btn.addEventListener('click', (e) => {
                        const targetPage = parseInt(e.target.dataset.page);
                        this.renderDataPreview(columns, data, targetPage);
                    });
                }
            });
        } else {
            pagination.style.display = 'none';
        }
    }

    async clearVizIQ() {
        if (!confirm('Are you sure you want to clear all data?')) return;

        try {
            await fetch('/api/viziq/clear', { method: 'POST' });

            // Destroy charts
            this.viziqCharts.forEach(chart => chart.destroy());
            this.viziqCharts = [];
            this.viziqData = null;

            // Reset UI
            const uploadSection = document.getElementById('viziq-upload-section');
            const uploadArea = document.getElementById('viziq-upload-area');
            const processing = document.getElementById('viziq-processing');
            const dashboard = document.getElementById('viziq-dashboard');

            uploadSection.style.display = 'flex';
            uploadArea.style.display = 'block';
            processing.style.display = 'none';
            dashboard.style.display = 'none';

            // Reset processing steps
            ['step-upload', 'step-preprocess', 'step-analyze', 'step-visualize'].forEach(id => {
                const el = document.getElementById(id);
                el?.classList.remove('active', 'completed');
            });

            // Update badge
            document.getElementById('viziq-badge').textContent = 'AI';

        } catch (error) {
            console.error('Error clearing VizIQ:', error);
        }
    }

    // ================================
    // MODAL MANAGEMENT
    // ================================

    closeModal() {
        const modal = document.getElementById('modal');
        modal.classList.remove('active');
    }

    // ================================
    // DATA LOADING
    // ================================

    async loadData() {
        try {
            // Load tasks
            const tasksRes = await fetch('/api/tasks');
            this.tasks = await tasksRes.json();
            this.renderTasks();

            // Load notes
            const notesRes = await fetch('/api/notes');
            this.notes = await notesRes.json();
            this.renderNotes();

            // Load reminders
            const remindersRes = await fetch('/api/reminders');
            this.reminders = await remindersRes.json();
            this.renderReminders();

            // Update stats
            this.updateStats();
        } catch (error) {
            console.error('Error loading data:', error);
        }
    }

    async updateStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();

            document.getElementById('stat-tasks').textContent = stats.completed_tasks;
            document.getElementById('stat-notes').textContent = stats.total_notes;

            document.getElementById('tasks-badge').textContent = stats.pending_tasks;
            document.getElementById('notes-badge').textContent = stats.total_notes;
            document.getElementById('reminders-badge').textContent = stats.total_reminders;
        } catch (error) {
            console.error('Error updating stats:', error);
        }
    }

    // ================================
    // UTILITY FUNCTIONS
    // ================================

    setupClock() {
        const updateClock = () => {
            const now = new Date();
            const timeStr = now.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit'
            });
            const dateStr = now.toLocaleDateString('en-US', {
                weekday: 'short',
                month: 'short',
                day: 'numeric'
            });

            const timeDisplay = document.getElementById('time-display');
            if (timeDisplay) {
                timeDisplay.textContent = `${dateStr} • ${timeStr}`;
            }
        };

        updateClock();
        setInterval(updateClock, 1000);
    }

    formatTime(date) {
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    formatDateTime(date) {
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ================================
    // VOICE INPUT/OUTPUT
    // ================================

    setupVoiceInput() {
        // Check for Web Speech API support
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            console.warn('[Voice] Web Speech API not supported in this browser');
            const voiceBtn = document.getElementById('voice-toggle');
            if (voiceBtn) {
                voiceBtn.title = 'Voice input not supported in this browser';
                voiceBtn.style.opacity = '0.4';
                voiceBtn.style.cursor = 'not-allowed';
            }
            return;
        }

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-IN';

        this.recognition.onstart = () => {
            this.isListening = true;
            document.querySelectorAll('#voice-toggle').forEach(btn => btn.classList.add('listening'));
            if (typeof toastManager !== 'undefined') {
                toastManager.info('🎙️ Listening...', 2000);
            }
        };

        this.recognition.onresult = (event) => {
            const input = document.getElementById('chat-input');
            let interimTranscript = '';
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                } else {
                    interimTranscript += transcript;
                }
            }

            if (finalTranscript) {
                input.value = finalTranscript;
                input.style.height = 'auto';
                input.style.height = input.scrollHeight + 'px';
            } else if (interimTranscript) {
                input.value = interimTranscript;
                input.style.height = 'auto';
                input.style.height = input.scrollHeight + 'px';
            }
        };

        this.recognition.onend = () => {
            this.isListening = false;
            document.querySelectorAll('#voice-toggle').forEach(btn => btn.classList.remove('listening'));

            // Auto-send if there's text
            const input = document.getElementById('chat-input');
            if (input.value.trim()) {
                if (typeof toastManager !== 'undefined') {
                    toastManager.success('🎙️ Sending voice message...', 1500);
                }
                setTimeout(() => this.sendMessage(), 500);
            } else if (this.voiceMode) {
                // Voice Mode: no text captured (silence), restart listening automatically
                setTimeout(() => {
                    if (this.voiceMode) this.startListening();
                }, 600);
            }
        };

        this.recognition.onerror = (event) => {
            this.isListening = false;
            document.querySelectorAll('#voice-toggle').forEach(btn => btn.classList.remove('listening'));

            if (event.error === 'no-speech') {
                // Silence timeout — normal in voice mode, just restart
                if (this.voiceMode) {
                    setTimeout(() => {
                        if (this.voiceMode) this.startListening();
                    }, 500);
                }
                // No toast — this is expected behaviour
                return;
            }

            if (event.error === 'not-allowed') {
                this.voiceMode = false;
                document.querySelectorAll('#voice-toggle').forEach(btn => btn.classList.remove('voice-mode-active'));
                if (typeof toastManager !== 'undefined') {
                    toastManager.error('Microphone access denied. Please allow microphone access.', 3000);
                }
            } else if (event.error !== 'aborted') {
                // In voice mode, try to recover from transient errors silently
                if (this.voiceMode) {
                    setTimeout(() => {
                        if (this.voiceMode) this.startListening();
                    }, 800);
                } else {
                    if (typeof toastManager !== 'undefined') {
                        toastManager.warning(`Voice input error: ${event.error}`, 3000);
                    }
                }
            }
        };
    }

    toggleVoiceInput() {
        if (!this.recognition) {
            if (typeof toastManager !== 'undefined') {
                toastManager.warning('Voice input is not supported in this browser. Use Chrome or Edge.', 3000);
            }
            return;
        }

        if (this.voiceMode) {
            // Turn off voice mode
            this.voiceMode = false;
            this.stopListening();
            document.querySelectorAll('#voice-toggle').forEach(btn => {
                btn.classList.remove('voice-mode-active');
                btn.title = 'Voice Mode';
            });
            if (typeof toastManager !== 'undefined') {
                toastManager.info('🔇 Voice Mode off', 2000);
            }
        } else {
            // Turn on voice mode
            this.voiceMode = true;
            document.querySelectorAll('#voice-toggle').forEach(btn => {
                btn.classList.add('voice-mode-active');
                btn.title = 'Voice Mode active — click to turn off';
            });
            if (typeof toastManager !== 'undefined') {
                toastManager.success('🎙️ Voice Mode on — speak freely!', 2500);
            }
            this.startListening();
        }
    }

    async startListening() {
        if (this.recognition && !this.isListening) {
            try {
                // Request mic with noise cancellation constraints first.
                // This primes the browser to use noiseSuppression + echoCancellation
                // before Web Speech API captures audio.
                if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                    const stream = await navigator.mediaDevices.getUserMedia({
                        audio: {
                            noiseSuppression: true,
                            echoCancellation: true,
                            autoGainControl: true,
                            sampleRate: 48000
                        }
                    });
                    // Release the stream immediately; SpeechRecognition manages its own capture
                    stream.getTracks().forEach(track => track.stop());
                }
                this.recognition.start();
            } catch (e) {
                if (e.name === 'NotAllowedError') {
                    if (typeof toastManager !== 'undefined') {
                        toastManager.error('Microphone access denied. Please allow microphone access.', 3000);
                    }
                } else {
                    console.error('[Voice] Failed to start recognition:', e);
                }
            }
        }
    }

    stopListening() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
        // If voice mode, also disable it when explicitly stopped
        if (this.voiceMode) {
            this.voiceMode = false;
            document.querySelectorAll('#voice-toggle').forEach(btn => {
                btn.classList.remove('voice-mode-active');
                btn.title = 'Voice Mode';
            });
        }
    }
}

// ================================
// INITIALIZE APP
// ================================

let laplacian;

document.addEventListener('DOMContentLoaded', () => {
    laplacian = new LaplacianAssistant();

    // Setup modal close button
    document.getElementById('modal-close').addEventListener('click', () => {
        laplacian.closeModal();
    });

    // Close modal on background click
    document.getElementById('modal').addEventListener('click', (e) => {
        if (e.target.id === 'modal') {
            laplacian.closeModal();
        }
    });
});
