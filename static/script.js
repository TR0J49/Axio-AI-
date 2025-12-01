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
        this.init();
    }

    init() {
        this.setupNavigation();
        this.setupChat();
        this.setupTasks();
        this.setupNotes();
        this.setupReminders();
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
