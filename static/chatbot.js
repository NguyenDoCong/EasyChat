// Chat Tối Giản - Hiển thị Array HTML từ Server
(function() {
    // Cấu hình
    const CONFIG = {
        apiUrl: 'YOUR_API_ENDPOINT_HERE', // Thay đổi URL này
        containerWidth: '600px',
        containerHeight: '2200vh'
    };

    // Tạo styles
    const styles = `
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #f5f5f5;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .chat-container {
            width: 100%;
            max-width: ${CONFIG.containerWidth};
            height: ${CONFIG.containerHeight};
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .chat-header {
            padding: 16px 20px;
            background: #2563eb;
            color: white;
            font-weight: 600;
            font-size: 18px;
            border-bottom: 1px solid #1d4ed8;
        }

        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .chat-messages::-webkit-scrollbar {
            width: 6px;
        }

        .chat-messages::-webkit-scrollbar-thumb {
            background: #d1d5db;
            border-radius: 3px;
        }

        .message {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 16px;
            line-height: 1.4;
            word-wrap: break-word;
        }

        .message.user {
            align-self: flex-end;
            background: #2563eb;
            color: white;
            border-bottom-right-radius: 4px;
        }

        .message.bot {
            align-self: flex-start;
            background: #f3f4f6;
            color: #1f2937;
            border-bottom-left-radius: 4px;
            max-width: 85%;
        }

        .message.system {
            align-self: center;
            background: #fef3c7;
            color: #92400e;
            font-size: 13px;
            font-style: italic;
            max-width: 80%;
            text-align: center;
        }

        /* Styles cho HTML content */
        .message.bot h1, 
        .message.bot h2, 
        .message.bot h3 {
            color: #1f2937;
            margin-top: 1em;
            margin-bottom: 0.5em;
        }

        .message.bot h1:first-child, 
        .message.bot h2:first-child, 
        .message.bot h3:first-child {
            margin-top: 0;
        }

        .message.bot code {
            background-color: #e5e7eb;
            border-radius: 4px;
            padding: 0.2em 0.4em;
            font-size: 85%;
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
        }

        .message.bot pre {
            padding: 12px;
            overflow: auto;
            font-size: 85%;
            line-height: 1.45;
            background-color: #1f2937;
            border-radius: 8px;
            border: 1px solid #374151;
            margin: 8px 0;
        }

        .message.bot pre code {
            padding: 0;
            margin: 0;
            background-color: transparent;
            border: none;
            color: #f9fafb;
        }

        .message.bot p {
            margin: 0.5em 0;
        }

        .message.bot ul,
        .message.bot ol {
            margin: 0.5em 0;
            padding-left: 1.5em;
        }

        .message.bot li {
            margin: 0.3em 0;
        }

        .message.bot a {
            color: #2563eb;
            text-decoration: none;
        }

        .message.bot a:hover {
            text-decoration: underline;
        }

        .message.bot blockquote {
            border-left: 4px solid #d1d5db;
            padding-left: 1em;
            margin: 0.5em 0;
            color: #6b7280;
        }

        .message.bot table {
            border-collapse: collapse;
            width: 100%;
            margin: 0.5em 0;
        }

        .message.bot th,
        .message.bot td {
            border: 1px solid #e5e7eb;
            padding: 8px;
            text-align: left;
        }

        .message.bot th {
            background: #f9fafb;
            font-weight: 600;
        }

        .message.bot img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
        }

        .message.bot strong {
            font-weight: 600;
        }

        .message.bot em {
            font-style: italic;
        }

        .message.bot hr {
            border: none;
            border-top: 1px solid #e5e7eb;
            margin: 1em 0;
        }

        /* HTML item separator */
        .html-item {
            margin: 8px 0;
            padding: 8px 0;
        }

        .html-item:not(:last-child) {
            border-bottom: 1px solid #e5e7eb;
        }

        .html-item:first-child {
            padding-top: 0;
        }

        .html-item:last-child {
            padding-bottom: 0;
            border-bottom: none;
        }

        .typing-indicator {
            align-self: flex-start;
            display: none;
            padding: 12px 16px;
            background: #f3f4f6;
            border-radius: 16px;
            border-bottom-left-radius: 4px;
        }

        .typing-indicator.active {
            display: flex;
            gap: 4px;
            align-items: center;
        }

        .typing-dot {
            width: 8px;
            height: 8px;
            background: #6b7280;
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }

        .typing-dot:nth-child(2) {
            animation-delay: 0.2s;
        }

        .typing-dot:nth-child(3) {
            animation-delay: 0.4s;
        }

        @keyframes typing {
            0%, 60%, 100% {
                opacity: 0.3;
            }
            30% {
                opacity: 1;
            }
        }

        .chat-input-area {
            padding: 16px 20px;
            background: white;
            border-top: 1px solid #e5e7eb;
            display: flex;
            gap: 12px;
            align-items: flex-end;
        }

        .chat-input {
            flex: 1;
            padding: 12px 16px;
            border: 1px solid #d1d5db;
            border-radius: 24px;
            font-size: 14px;
            resize: none;
            font-family: inherit;
            max-height: 120px;
            overflow-y: auto;
        }

        .chat-input:focus {
            outline: none;
            border-color: #2563eb;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }

        .send-button {
            width: 44px;
            height: 44px;
            background: #2563eb;
            color: white;
            border: none;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
            flex-shrink: 0;
        }

        .send-button:hover:not(:disabled) {
            background: #1d4ed8;
        }

        .send-button:disabled {
            background: #9ca3af;
            cursor: not-allowed;
        }

        .send-button svg {
            width: 20px;
            height: 20px;
        }

        .welcome-message {
            text-align: center;
            color: #6b7280;
            font-size: 14px;
            margin-top: 40px;
        }
    `;

    // Inject styles
    const styleElement = document.createElement('style');
    styleElement.textContent = styles;
    document.head.appendChild(styleElement);

    // Tạo HTML structure
    function createChatInterface() {
        const container = document.createElement('div');
        container.className = 'chat-container';

        const header = document.createElement('div');
        header.className = 'chat-header';
        header.textContent = '💬 Chat Assistant';

        const messagesArea = document.createElement('div');
        messagesArea.className = 'chat-messages';
        messagesArea.id = 'chatMessages';

        const welcomeMsg = document.createElement('div');
        welcomeMsg.className = 'welcome-message';
        welcomeMsg.textContent = 'Xin chào! Hãy gửi tin nhắn để bắt đầu trò chuyện.';
        messagesArea.appendChild(welcomeMsg);

        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        typingIndicator.id = 'typingIndicator';
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = 'typing-dot';
            typingIndicator.appendChild(dot);
        }

        const inputArea = document.createElement('div');
        inputArea.className = 'chat-input-area';

        const textarea = document.createElement('textarea');
        textarea.className = 'chat-input';
        textarea.id = 'chatInput';
        textarea.placeholder = 'Nhập tin nhắn...';
        textarea.rows = 1;

        const sendButton = document.createElement('button');
        sendButton.className = 'send-button';
        sendButton.id = 'sendButton';
        sendButton.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
        `;

        inputArea.appendChild(textarea);
        inputArea.appendChild(sendButton);

        container.appendChild(header);
        container.appendChild(messagesArea);
        container.appendChild(typingIndicator);
        container.appendChild(inputArea);

        document.body.appendChild(container);

        return {
            messagesArea,
            textarea,
            sendButton,
            typingIndicator
        };
    }

    // Chat functionality
    class ChatApp {
        constructor(elements) {
            this.messagesArea = elements.messagesArea;
            this.textarea = elements.textarea;
            this.sendButton = elements.sendButton;
            this.typingIndicator = elements.typingIndicator;

            this.init();
        }

        init() {
            // Event listeners
            this.textarea.addEventListener('input', () => this.handleInput());
            this.textarea.addEventListener('keypress', (e) => this.handleKeyPress(e));
            this.sendButton.addEventListener('click', () => this.sendMessage());

            // Initial state
            this.sendButton.disabled = true;
            this.textarea.focus();
        }

        handleInput() {
            this.textarea.style.height = 'auto';
            this.textarea.style.height = Math.min(this.textarea.scrollHeight, 120) + 'px';
            this.sendButton.disabled = !this.textarea.value.trim();
        }

        handleKeyPress(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        }

        addMessage(content, type = 'bot') {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            
            if (type === 'bot') {
                // Check if content is array
                if (Array.isArray(content)) {
                    // Render each HTML item
                    content.forEach((htmlString, index) => {
                        const itemDiv = document.createElement('div');
                        itemDiv.className = 'html-item';
                        itemDiv.innerHTML = htmlString;
                        messageDiv.appendChild(itemDiv);
                    });
                } else if (typeof content === 'string') {
                    // Single HTML string
                    messageDiv.innerHTML = content;
                } else {
                    // Fallback
                    messageDiv.textContent = 'Invalid content format';
                }
            } else {
                // Plain text for user and system messages
                messageDiv.textContent = content;
            }
            
            this.messagesArea.appendChild(messageDiv);
            this.scrollToBottom();
        }

        showTyping() {
            this.typingIndicator.classList.add('active');
            this.scrollToBottom();
        }

        hideTyping() {
            this.typingIndicator.classList.remove('active');
        }

        scrollToBottom() {
            this.messagesArea.scrollTop = this.messagesArea.scrollHeight;
        }

        async sendMessage() {
            const message = this.textarea.value.trim();

            if (!message) return;

            // Add user message
            this.addMessage(message, 'user');

            // Clear input
            this.textarea.value = '';
            this.textarea.style.height = 'auto';

            // Disable input
            this.textarea.disabled = true;
            this.sendButton.disabled = true;

            // Show typing
            this.showTyping();

            try {
                // Send request to server
                const response = await fetch(CONFIG.apiUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        timestamp: new Date().toISOString()
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                // Hide typing
                this.hideTyping();

                // Add bot response
                // Server trả về: {"message": ["<p>HTML 1</p>", "<p>HTML 2</p>"]}
                // hoặc: {"message": "<p>Single HTML</p>"}
                if (data.message) {
                    this.addMessage(data.message, 'bot');
                } else {
                    this.addMessage('Không có phản hồi từ server', 'system');
                }

            } catch (error) {
                console.error('Error:', error);
                this.hideTyping();
                this.addMessage('❌ Lỗi kết nối đến server. Vui lòng thử lại.', 'system');
            } finally {
                // Enable input
                this.textarea.disabled = false;
                this.sendButton.disabled = false;
                this.textarea.focus();
            }
        }

        // Demo mode - Uncomment để test với array HTML
        /*
        async sendMessage() {
            const message = this.textarea.value.trim();

            if (!message) return;

            this.addMessage(message, 'user');
            this.textarea.value = '';
            this.textarea.style.height = 'auto';
            this.textarea.disabled = true;
            this.sendButton.disabled = true;

            this.showTyping();

            setTimeout(() => {
                this.hideTyping();
                
                // Demo với array HTML
                const demoHtmlArray = [
                    '<h3>Kết quả tìm kiếm 1</h3><p>Đây là nội dung của kết quả đầu tiên với <strong>text in đậm</strong>.</p>',
                    '<h3>Kết quả tìm kiếm 2</h3><p>Kết quả thứ hai có <em>chữ nghiêng</em> và <code>code inline</code>.</p>',
                    '<h3>Kết quả tìm kiếm 3</h3><ul><li>Item 1</li><li>Item 2</li><li>Item 3</li></ul>',
                    '<blockquote>Đây là một quote từ kết quả thứ 4</blockquote><p>Với thêm nội dung bên dưới.</p>'
                ];

                // Hoặc test với single HTML
                // const singleHtml = '<h2>Single Response</h2><p>This is a single HTML response.</p>';
                
                this.addMessage(demoHtmlArray, 'bot');
                // this.addMessage(singleHtml, 'bot');
                
                this.textarea.disabled = false;
                this.sendButton.disabled = false;
                this.textarea.focus();
            }, 1500);
        }
        */
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            const elements = createChatInterface();
            new ChatApp(elements);
        });
    } else {
        const elements = createChatInterface();
        new ChatApp(elements);
    }

    // Export to window
    window.ChatConfig = CONFIG;

})();