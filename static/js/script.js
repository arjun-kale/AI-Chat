class ChatApp {
    constructor() {
        this.sessionId = null;
        this.uploadedFiles = [];
        this.initializeEventListeners();
        this.loadSessionFromStorage();
    }

    initializeEventListeners() {
        // Send message
        document.getElementById('sendBtn').addEventListener('click', () => this.sendMessage());
        document.getElementById('messageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Auto-resize textarea
        document.getElementById('messageInput').addEventListener('input', (e) => {
            e.target.style.height = 'auto';
            e.target.style.height = e.target.scrollHeight + 'px';
        });

        // New chat
        document.getElementById('newChatBtn').addEventListener('click', () => this.startNewChat());

        // File upload
        document.getElementById('uploadBtn').addEventListener('click', () => {
            document.getElementById('hiddenFileInput').click();
        });

        document.getElementById('hiddenFileInput').addEventListener('change', (e) => {
            this.handleFileUpload(e.target.files);
        });

        // Drag and drop
        const uploadZone = document.getElementById('uploadZone');
        uploadZone.addEventListener('click', () => {
            document.getElementById('hiddenFileInput').click();
        });

        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.style.borderColor = '#764ba2';
            uploadZone.style.background = '#f8f9ff';
        });

        uploadZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadZone.style.borderColor = '#667eea';
            uploadZone.style.background = 'white';
        });

        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.style.borderColor = '#667eea';
            uploadZone.style.background = 'white';
            this.handleFileUpload(e.dataTransfer.files);
        });
    }

    async startNewChat() {
        try {
            const response = await fetch('/api/conversations/start/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (response.ok) {
                const data = await response.json();
                this.sessionId = data.session_id;
                this.saveSessionToStorage();
                this.clearChat();
                this.showWelcomeMessage();
            } else {
                this.showError('Failed to start new conversation');
            }
        } catch (error) {
            console.error('Error starting new chat:', error);
            this.showError('Failed to start new conversation');
        }
    }

    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();

        if (!message) return;

        // Clear input and reset height
        messageInput.value = '';
        messageInput.style.height = 'auto';

        // Hide welcome message if visible
        this.hideWelcomeMessage();

        // Add user message to chat
        this.addMessageToChat('user', message);

        // Show loading
        this.showLoading();

        try {
            const response = await fetch('/api/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId
                }),
            });

            if (response.ok) {
                const data = await response.json();
                this.sessionId = data.session_id;
                this.saveSessionToStorage();
                
                // Add AI response to chat
                this.addMessageToChat('assistant', data.ai_message.content);
            } else {
                const errorData = await response.json();
                this.showError(errorData.error || 'Failed to send message');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.showError('Failed to send message');
        } finally {
            this.hideLoading();
        }
    }

    async handleFileUpload(files) {
        if (!files || files.length === 0) return;

        // Validate files
        const validFiles = Array.from(files).filter(file => {
            const validTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/gif', 'image/bmp'];
            return validTypes.includes(file.type);
        });

        if (validFiles.length === 0) {
            this.showError('Please upload only PDF or image files');
            return;
        }

        // Show loading
        this.showLoading();

        try {
            for (const file of validFiles) {
                const formData = new FormData();
                formData.append('file', file);
                if (this.sessionId) {
                    formData.append('session_id', this.sessionId);
                }

                const response = await fetch('/api/upload/', {
                    method: 'POST',
                    body: formData,
                });

                if (response.ok) {
                    const data = await response.json();
                    this.sessionId = data.session_id;
                    this.saveSessionToStorage();
                    
                    // Add file to uploaded files list
                    this.uploadedFiles.push({
                        name: file.name,
                        type: file.type,
                        size: file.size
                    });

                    // Show success message
                    this.addMessageToChat('assistant', `File "${file.name}" uploaded and processed successfully! You can now ask questions about it.`);
                } else {
                    const errorData = await response.json();
                    this.showError(`Failed to upload ${file.name}: ${errorData.error}`);
                }
            }
        } catch (error) {
            console.error('Error uploading files:', error);
            this.showError('Failed to upload files');
        } finally {
            this.hideLoading();
        }
    }

    addMessageToChat(type, content) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = type === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = content;

        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = new Date().toLocaleTimeString();

        messageContent.appendChild(messageTime);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);

        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    clearChat() {
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = '';
        this.uploadedFiles = [];
    }

    showWelcomeMessage() {
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-content">
                    <i class="fas fa-robot welcome-icon"></i>
                    <h2>Welcome to AI Chat Assistant</h2>
                    <p>Start a conversation or upload a PDF/image to get AI-powered responses!</p>
                    <div class="upload-zone" id="uploadZone">
                        <i class="fas fa-cloud-upload-alt"></i>
                        <p>Drag & drop files here or click to upload</p>
                        <small>Supports PDF and image files</small>
                    </div>
                </div>
            </div>
        `;

        // Re-attach event listeners to upload zone
        const uploadZone = document.getElementById('uploadZone');
        uploadZone.addEventListener('click', () => {
            document.getElementById('hiddenFileInput').click();
        });

        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.style.borderColor = '#764ba2';
            uploadZone.style.background = '#f8f9ff';
        });

        uploadZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadZone.style.borderColor = '#667eea';
            uploadZone.style.background = 'white';
        });

        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.style.borderColor = '#667eea';
            uploadZone.style.background = 'white';
            this.handleFileUpload(e.dataTransfer.files);
        });
    }

    hideWelcomeMessage() {
        const welcomeMessage = document.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
    }

    showLoading() {
        document.getElementById('loadingOverlay').style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loadingOverlay').style.display = 'none';
    }

    showError(message) {
        this.addMessageToChat('assistant', `Error: ${message}`);
    }

    saveSessionToStorage() {
        if (this.sessionId) {
            localStorage.setItem('chatSessionId', this.sessionId);
        }
    }

    loadSessionFromStorage() {
        this.sessionId = localStorage.getItem('chatSessionId');
        if (this.sessionId) {
            this.loadConversation();
        } else {
            this.showWelcomeMessage();
        }
    }

    async loadConversation() {
        if (!this.sessionId) return;

        try {
            const response = await fetch(`/api/conversations/${this.sessionId}/`);
            if (response.ok) {
                const data = await response.json();
                this.clearChat();
                
                if (data.messages && data.messages.length > 0) {
                    data.messages.forEach(msg => {
                        this.addMessageToChat(msg.message_type, msg.content);
                    });
                } else {
                    this.showWelcomeMessage();
                }
            } else {
                this.sessionId = null;
                this.showWelcomeMessage();
            }
        } catch (error) {
            console.error('Error loading conversation:', error);
            this.sessionId = null;
            this.showWelcomeMessage();
        }
    }
}

// Initialize the chat app when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});
