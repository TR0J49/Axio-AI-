// ================================
// AXIO - AI CODE ASSISTANT
// by Perfionix AI
// Interactive JavaScript
// ================================

class AxioAssistant {
    constructor() {
        this.currentView = 'chat';
        this.notes = [];
        this.tasks = [];
        this.reminders = [];
        this.dociqDocuments = [];
        this.viziqCharts = [];
        this.viziqData = null;
        this.init();
    }

    init() {
        this.setupNavigation();
        this.setupChat();
        this.setupTasks();
        this.setupNotes();
        this.setupReminders();
        this.setupDocIQ();
        this.setupVizIQ();
        this.setupClock();
        this.loadData();
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
    }

    // ================================
    // CHAT FUNCTIONALITY
    // ================================

    setupChat() {
        const input = document.getElementById('chat-input');
        const sendBtn = document.getElementById('send-message');
        const resetBtn = document.getElementById('reset-chat');
        const searchBtn = document.getElementById('web-search');

        sendBtn.addEventListener('click', () => this.sendMessage());
        searchBtn.addEventListener('click', () => this.webSearch());

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

    async sendMessage(forceSearch = false) {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();

        if (!message) return;

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
        } catch (error) {
            this.removeTypingIndicator();
            this.addMessageToUI('Connection error. Please make sure the server is running.', 'assistant');
        }
    }

    async webSearch() {
        // Force search mode - sends message with search flag
        await this.sendMessage(true);
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
            if (typeEffect) {
                // Add typing effect for assistant messages
                this.typeWriterEffect(textDiv, text, messagesContainer);
            } else {
                this.renderMarkdown(textDiv, text);
            }
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

            // Add new AI response with typing effect
            this.addMessageToUI(data.response, 'assistant', data.ai_index, false, true);

        } catch (error) {
            console.error('Error submitting edit:', error);
            alert('Failed to submit edit. Please try again.');
            this.cancelEdit(messageDiv, newText);
        }
    }

    copyCode(button, code) {
        navigator.clipboard.writeText(code).then(() => {
            const originalText = button.innerHTML;
            button.innerHTML = '✓ Copied!';
            button.classList.add('copied');

            setTimeout(() => {
                button.innerHTML = originalText;
                button.classList.remove('copied');
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy code:', err);
        });
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
            hljs.highlightElement(block);

            // Add copy button to code blocks
            const pre = block.parentElement;
            if (pre.parentElement.classList.contains('code-block-wrapper')) return; // Already wrapped

            const wrapper = document.createElement('div');
            wrapper.className = 'code-block-wrapper';

            const header = document.createElement('div');
            header.className = 'code-header';

            const language = block.className.replace('language-', '').replace('hljs', '').trim() || 'code';
            const langLabel = document.createElement('span');
            langLabel.className = 'code-language';
            langLabel.textContent = language;

            const copyBtn = document.createElement('button');
            copyBtn.className = 'code-copy-btn';
            copyBtn.innerHTML = '📋 Copy';
            copyBtn.onclick = () => this.copyCode(copyBtn, block.textContent);

            header.appendChild(langLabel);
            header.appendChild(copyBtn);

            pre.parentNode.insertBefore(wrapper, pre);
            wrapper.appendChild(header);
            wrapper.appendChild(pre);
        });
    }

    async typeWriterEffect(textDiv, fullText, messagesContainer) {
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

        const typeNextChunk = () => {
            if (charIndex < fullText.length) {
                // Add next chunk of characters
                const endIndex = Math.min(charIndex + chunkSize, fullText.length);
                currentText = fullText.substring(0, endIndex);
                charIndex = endIndex;

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

                // Continue typing
                setTimeout(typeNextChunk, speed);
            } else {
                // Typing complete - remove cursor and apply final formatting
                cursor.remove();
                this.renderMarkdown(textDiv, fullText);
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }
        };

        // Start typing
        typeNextChunk();
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
                        <div class="message-text">Hello! I'm Axio, your AI coding assistant by Perfionix AI. I can help you with code, debugging, algorithms, and programming questions. What would you like to work on?</div>
                        <span class="message-time">${this.formatTime(new Date())}</span>
                    </div>
                </div>
            `;
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
                <button class="btn-secondary" onclick="axio.closeModal()">Cancel</button>
                <button class="btn-primary" onclick="axio.saveTask()">Add Task</button>
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
                <div class="task-checkbox" onclick="axio.toggleTask('${task.id}')"></div>
                <div class="task-content">
                    <div class="task-title">${this.escapeHtml(task.title)}</div>
                </div>
                <span class="task-priority ${task.priority}">${task.priority}</span>
                <button class="task-delete" onclick="axio.deleteTask('${task.id}')">×</button>
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
                <button class="btn-secondary" onclick="axio.closeModal()">Cancel</button>
                <button class="btn-primary" onclick="axio.saveNote()">Save Note</button>
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
                    <button class="note-delete" onclick="axio.deleteNote('${note.id}')">×</button>
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
                <button class="btn-secondary" onclick="axio.closeModal()">Cancel</button>
                <button class="btn-primary" onclick="axio.saveReminder()">Add Reminder</button>
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
                <button class="reminder-delete" onclick="axio.deleteReminder('${reminder.id}')">×</button>
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
            <button class="doc-remove" onclick="axio.removeDocIQDocument('${doc.id}')" title="Remove document">
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
                        <strong>Welcome to DocIQ!</strong><br><br>
                        I'm your intelligent document assistant. Upload PDF, Word, or text files and ask me anything about their content.<br><br>
                        <em>Features:</em>
                        <ul>
                            <li>Extract key information</li>
                            <li>Summarize documents</li>
                            <li>Answer specific questions</li>
                            <li>Compare multiple documents</li>
                        </ul>
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
        this.renderDataPreview(data.columns, data.preview);
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
                        label: function(context) {
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

    renderDataPreview(columns, data) {
        const thead = document.getElementById('table-header');
        const tbody = document.getElementById('table-body');

        // Render header
        thead.innerHTML = `<tr>${columns.map(col => `<th>${col}</th>`).join('')}</tr>`;

        // Render body (limit to 50 rows)
        tbody.innerHTML = data.slice(0, 50).map(row =>
            `<tr>${columns.map(col => `<td>${row[col] !== null && row[col] !== undefined ? row[col] : '-'}</td>`).join('')}</tr>`
        ).join('');
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
}

// ================================
// INITIALIZE APP
// ================================

let axio;

document.addEventListener('DOMContentLoaded', () => {
    axio = new AxioAssistant();

    // Setup modal close button
    document.getElementById('modal-close').addEventListener('click', () => {
        axio.closeModal();
    });

    // Close modal on background click
    document.getElementById('modal').addEventListener('click', (e) => {
        if (e.target.id === 'modal') {
            axio.closeModal();
        }
    });
});
