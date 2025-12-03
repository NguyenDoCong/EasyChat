// Chat Tối Giản - Markdown với Marked.js
(function () {
    // Cấu hình
    const CONFIG = {
        apiUrl: 'http://127.0.0.1:8000/crawl', // Thay đổi URL này
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

        /* Markdown styles cho bot messages */
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

    // Load external libraries
    function loadScript(url) {
        return new Promise((resolve, reject) => {
            if (document.querySelector(`script[src="${url}"]`)) {
                resolve();
                return;
            }

            const script = document.createElement('script');
            script.src = url;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

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
            this.markedReady = false;

            this.init();
        }

        async init() {
            // Load Marked.js
            async function fetchOverlayData(url = window.location.href) {
                try {
                    console.log('Fetching data for:', url);

                    const response = await fetch("http://127.0.0.1:8000/init", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({ href: url })
                    });

                    if (response.ok) {
                        const result = await response.json();
                        console.log('✅ Loaded content for:', url);
                    } else {
                        console.error('API returned status:', response.status);
                    }
                } catch (err) {
                    console.error("Error fetching data for", url, err);
                }
            }

            // fetchOverlayData();

            try {
                await loadScript('https://cdn.jsdelivr.net/npm/marked@9.1.6/marked.min.js');
                console.log('Marked.js loaded successfully');
                this.markedReady = true;
            } catch (error) {
                console.warn('Failed to load Marked.js, using plain text:', error);
            }

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

        async renderMarkdown(text) {
            if (!this.markedReady || !window.marked) {
                return text.replace(/\n/g, '<br>');
            }

            try {
                const html = await marked.parse(text);
                return html;
            } catch (error) {
                console.error('Markdown rendering error:', error);
                return text.replace(/\n/g, '<br>');
            }
        }

        async addMessage(content, type = 'bot') {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;

            if (type === 'bot') {
                // Check if content is JSON object (products)
                if (typeof content === 'object' && content.type === 'products') {
                    const html = this.renderProducts(content.data);
                    messageDiv.innerHTML = html;
                } else {
                    // Parse markdown for text content
                    const html = await this.renderMarkdown(content);
                    messageDiv.innerHTML = html;
                }
            } else {
                // Plain text for user and system messages
                messageDiv.textContent = content;
            }

            this.messagesArea.appendChild(messageDiv);
            this.scrollToBottom();
        }

        renderProducts(products) {
            if (!Array.isArray(products) || products.length === 0) {
                return '<p>Không tìm thấy sản phẩm</p>';
            }

            // Render table
            let table = `
                <div class="products-container">
                    <h3>Kết quả tìm kiếm</h3>
                    <table class="products-table">
                        <thead>
                            <tr>
                                <th>Tên sản phẩm</th>
                                <th>Giá</th>
                                <th>Đặc điểm</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            products.forEach(product => {
                table += `
                    <tr>
                        <td><a href="${this.escapeHtml(product.link)}" target="_blank">${this.escapeHtml(product.name)}</a></td>
                        <td>${this.escapeHtml(product.price)}</td>
                        <td>${this.escapeHtml(product.specs)}</td>
                    </tr>
                `;
            });

            table += `
                        </tbody>
                    </table>
                </div>
            `;

            // Render grid
            let grid = '<div class="product-grid">';

            products.forEach(product => {
                grid += `
                    <div class="product-card">
                        <a href="${this.escapeHtml(product.link)}" target="_blank" class="product-image-wrapper">
                            <img src="${this.escapeHtml(product.image)}" alt="${this.escapeHtml(product.name)}" class="product-image" onerror="this.src='https://via.placeholder.com/200'">
                        </a>
                        <div class="product-content">
                            <a href="${this.escapeHtml(product.link)}" target="_blank" class="product-name">${this.escapeHtml(product.name)}</a>
                            <div class="product-specs">${this.escapeHtml(product.specs)}</div>
                            <div class="price-wrapper">
                                <div class="price">${this.escapeHtml(product.price)}</div>
                            </div>
                            <button class="add-to-cart-btn" onclick="window.open('${this.escapeHtml(product.link)}', '_blank')">
                                Xem chi tiết
                            </button>
                        </div>
                    </div>
                `;
            });

            grid += '</div>';

            return table + grid;
        }

        escapeHtml(text) {
            const map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            };
            return text.replace(/[&<>"']/g, m => map[m]);
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
            await this.addMessage(message, 'user');

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

                // Add bot response (with markdown support)
                // await this.addMessage(data.message || data.response || 'Không có phản hồi từ server', 'bot');

                // Xử lý response - có thể là products hoặc text
                if (data.type === 'products') {
                    await this.addMessage(data, 'bot');
                } else {
                    await this.addMessage(data.message || data.response || 'Không có phản hồi từ server', 'bot');
                }

            } catch (error) {
                console.error('Error:', error);
                this.hideTyping();
                await this.addMessage('❌ Lỗi kết nối đến server. Vui lòng thử lại.', 'system');
            } finally {
                // Enable input
                this.textarea.disabled = false;
                this.sendButton.disabled = false;
                this.textarea.focus();
            }
        }

        // Demo mode - Uncomment để test markdown
        /*
        async sendMessage() {
            const message = this.textarea.value.trim();

            if (!message) return;

            await this.addMessage(message, 'user');
            this.textarea.value = '';
            this.textarea.style.height = 'auto';
            this.textarea.disabled = true;
            this.sendButton.disabled = true;

            this.showTyping();

            setTimeout(async () => {
                this.hideTyping();
                
                // Demo markdown response
                const demoResponse = `# Xin chào! 👋

Đây là **demo markdown** với thư viện Marked.js

## Code Example
Inline code: \`const x = 10;\`

Code block:
\`\`\`javascript
function hello() {
    console.log("Hello World!");
    return true;
}
\`\`\`

## Lists
- Item 1
- Item 2 with **bold**
- Item 3 with *italic*

1. First item
2. Second item
3. Third item

## Links & Images
Visit [Google](https://google.com) to search.

## Blockquote
> This is a blockquote
> It can span multiple lines

---

## Table
| Name | Age | City |
|------|-----|------|
| John | 25  | NYC  |
| Jane | 30  | LA   |

**Bold text** and *italic text* work perfectly!`;

                await this.addMessage(demoResponse, 'bot');
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