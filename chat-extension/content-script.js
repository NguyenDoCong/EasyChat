// ============================================
// content-script.js - Inject chat vào trang web
// ============================================
(function () {
    'use strict';

    // Cấu hình
    const CONFIG = {
        apiUrl: 'http://127.0.0.1:8000/crawl',
        position: 'bottom-right' // bottom-right, bottom-left, top-right, top-left
    };

    // Inject styles
    const styles = `
        #chat-widget-container * {
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }

        #chat-widget-button {
            position: fixed;
            top: 24px;
            left: 24px;
            width: 60px;
            height: 60px;
            background: #2563eb;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 999998;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        #chat-widget-button:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
        }

        #chat-widget-button svg {
            width: 28px;
            height: 28px;
            fill: white;
        }

        #chat-widget-window {
            position: fixed;
            bottom: 100px;
            left: 24px;
            width: 400px;
            height: 600px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            display: none;
            flex-direction: column;
            z-index: 999999;
            opacity: 0;
            transform: translateY(20px) scale(0.95);
            transition: opacity 0.3s, transform 0.3s;
        }

        #chat-widget-window.open {
            display: flex;
            opacity: 1;
            transform: translateY(0) scale(1);
        }

        .chat-header {
            padding: 16px 20px;
            background: #2563eb;
            color: white;
            font-weight: 600;
            font-size: 18px;
            border-radius: 16px 16px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .chat-header-title {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .chat-close-btn {
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            padding: 4px;
            display: flex;
            align-items: center;
            opacity: 0.8;
            transition: opacity 0.2s;
        }

        .chat-close-btn:hover {
            opacity: 1;
        }

        .chat-close-btn svg {
            width: 20px;
            height: 20px;
            fill: white;
        }

        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 12px;
            background: #f9fafb;
        }

        .chat-messages::-webkit-scrollbar {
            width: 6px;
        }

        .chat-messages::-webkit-scrollbar-thumb {
            background: #d1d5db;
            border-radius: 3px;
        }

        .message {
            max-width: 85%;
            padding: 12px 16px;
            border-radius: 16px;
            line-height: 1.4;
            word-wrap: break-word;
            font-size: 14px;
        }

        .message.user {
            align-self: flex-end;
            background: #2563eb;
            color: white;
            border-bottom-right-radius: 4px;
        }

        .message.bot {
            align-self: flex-start;
            background: white;
            color: #1f2937;
            border-bottom-left-radius: 4px;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        }

        .message.system {
            align-self: center;
            background: #fef3c7;
            color: #92400e;
            font-size: 13px;
            font-style: italic;
            max-width: 90%;
            text-align: center;
        }

        /* Markdown styles */
        .message.bot h1, 
        .message.bot h2, 
        .message.bot h3 {
            color: #1f2937;
            margin-top: 0.8em;
            margin-bottom: 0.4em;
            font-size: 1.1em;
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
            font-family: "SFMono-Regular", Consolas, monospace;
        }

        .message.bot pre {
            padding: 10px;
            overflow: auto;
            font-size: 85%;
            background-color: #1f2937;
            border-radius: 6px;
            margin: 8px 0;
        }

        .message.bot pre code {
            padding: 0;
            background-color: transparent;
            color: #f9fafb;
        }

        .message.bot p {
            margin: 0.4em 0;
        }

        .message.bot ul,
        .message.bot ol {
            margin: 0.4em 0;
            padding-left: 1.5em;
        }

        .message.bot a {
            color: #2563eb;
            text-decoration: none;
        }

        .message.bot a:hover {
            text-decoration: underline;
        }

        .html-item:not(:last-child) {
            border-bottom: 1px solid #e5e7eb;
            padding-bottom: 8px;
            margin-bottom: 8px;
        }

        /* Products Display */
        .products-container {
            width: 100%;
        }

        .products-container h3 {
            margin-bottom: 12px;
            color: #1f2937;
            font-size: 16px;
        }

        .products-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 16px;
            font-size: 13px;
        }

        .products-table th,
        .products-table td {
            border: 1px solid #e5e7eb;
            padding: 8px;
            text-align: left;
        }

        .products-table th {
            background: #f9fafb;
            font-weight: 600;
        }

        .products-table a {
            color: #2563eb;
            text-decoration: none;
        }

        .product-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
            margin-top: 12px;
        }

        .product-card {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 8px;
            background: white;
            display: flex;
            flex-direction: column;
        }

        .product-image-wrapper {
            display: block;
            border-radius: 6px;
            overflow: hidden;
            aspect-ratio: 1 / 1;
            background: #f9fafb;
            text-decoration: none;
            margin-bottom: 8px;
        }

        .product-image {
            width: 100%;
            height: 100%;
            object-fit: contain;
            display: block;
        }

        .product-content {
            display: flex;
            flex-direction: column;
            flex: 1;
        }

        .product-name {
            font-size: 12px;
            font-weight: 500;
            color: #111827;
            text-decoration: none;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            line-height: 1.3;
            margin-bottom: 6px;
        }

        .product-name:hover {
            color: #2563eb;
        }

        .product-specs {
            font-size: 11px;
            color: #6b7280;
            margin-bottom: 6px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .price-wrapper {
            margin-top: auto;
            margin-bottom: 8px;
        }

        .price {
            color: #ef4444;
            font-weight: 600;
            font-size: 13px;
        }

        .add-to-cart-btn {
            padding: 6px 10px;
            width: 100%;
            font-size: 12px;
            background: white;
            border-radius: 6px;
            border: 1px solid #e5e7eb;
            color: #4b5563;
            cursor: pointer;
            transition: all 0.2s;
            text-align: center;
        }

        .add-to-cart-btn:hover {
            background: #2563eb;
            color: white;
            border-color: #2563eb;
        }

        .typing-indicator {
            align-self: flex-start;
            display: none;
            padding: 12px 16px;
            background: white;
            border-radius: 16px;
            border-bottom-left-radius: 4px;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
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
            padding: 16px;
            background: white;
            border-top: 1px solid #e5e7eb;
            border-radius: 0 0 16px 16px;
            display: flex;
            gap: 8px;
            align-items: flex-end;
        }

        .chat-input {
            flex: 1;
            padding: 10px 14px;
            border: 1px solid #d1d5db;
            border-radius: 20px;
            font-size: 14px;
            resize: none;
            font-family: inherit;
            max-height: 100px;
            overflow-y: auto;
        }

        .chat-input:focus {
            outline: none;
            border-color: #2563eb;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }

        .send-button {
            width: 40px;
            height: 40px;
            background: #2563eb;
            color: white;
            border: none;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            transition: background 0.2s;
        }

        .send-button:hover:not(:disabled) {
            background: #1d4ed8;
        }

        .send-button:disabled {
            background: #9ca3af;
            cursor: not-allowed;
        }

        .send-button svg {
            width: 18px;
            height: 18px;
            fill: white;
        }

        .welcome-message {
            text-align: center;
            color: #6b7280;
            font-size: 13px;
            padding: 20px;
        }

        /* Responsive */
        @media (max-width: 480px) {
            #chat-widget-window {
                width: calc(100vw - 32px);
                height: calc(100vh - 140px);
                right: 16px;
                bottom: 90px;
            }

            #chat-widget-button {
                bottom: 16px;
                right: 16px;
            }
        }
    `;

    // Simple Markdown Parser (no external dependencies)
    const MarkdownParser = {
        parse(text) {
            if (!text) return '';

            let html = text;

            // Escape HTML
            html = html.replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');

            // Code blocks (must process first)
            html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
                return `<pre><code>${code.trim()}</code></pre>`;
            });

            // Inline code
            html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

            // Bold
            html = html.replace(/\*\*([^\*]+)\*\*/g, '<strong>$1</strong>')
                .replace(/__([^_]+)__/g, '<strong>$1</strong>');

            // Italic
            html = html.replace(/\*([^\*]+)\*/g, '<em>$1</em>')
                .replace(/_([^_]+)_/g, '<em>$1</em>');

            // Headers
            html = html.replace(/^#### (.*?)$/gm, '<h4>$1</h4>');
            html = html.replace(/^### (.*?)$/gm, '<h3>$1</h3>');
            html = html.replace(/^## (.*?)$/gm, '<h2>$1</h2>');
            html = html.replace(/^# (.*?)$/gm, '<h1>$1</h1>');

            // Links
            html = html.replace(/\[([^\]]+)\]\(([^\)]+)\)/g, '<a href="$2" target="_blank">$1</a>');

            // Horizontal rule
            html = html.replace(/^---$/gm, '<hr>');

            // Lists
            html = html.replace(/^\* (.+)$/gm, '<li>$1</li>');
            html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
            html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
            html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

            // Blockquotes
            html = html.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');

            // Paragraphs
            html = html.split('\n\n').map(para => {
                para = para.trim();
                if (!para) return '';
                if (para.startsWith('<') && (
                    para.includes('<h') ||
                    para.includes('<ul') ||
                    para.includes('<pre') ||
                    para.includes('<blockquote') ||
                    para.includes('<hr')
                )) {
                    return para;
                }
                return '<p>' + para + '</p>';
            }).join('\n');

            // Line breaks
            html = html.replace(/\n/g, '<br>');

            return html;
        }
    };

    // Inject stylesheet
    const styleSheet = document.createElement('style');
    styleSheet.textContent = styles;
    document.head.appendChild(styleSheet);

    // Create HTML structure
    function createChatWidget() {
        const container = document.createElement('div');
        container.id = 'chat-widget-container';

        // Chat button
        const button = document.createElement('div');
        button.id = 'chat-widget-button';
        button.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                <path d="m3 21 1.9-5.7a8.5 8.5 0 1 1 3.8 3.8z"/>
            </svg>
        `;

        // Chat window
        const window = document.createElement('div');
        window.id = 'chat-widget-window';
        window.innerHTML = `
            <div class="chat-header">
                <div class="chat-header-title">
                    <span>💬</span>
                    <span>Chat Assistant</span>
                </div>
                <button class="chat-close-btn">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                        <path d="M18 6L6 18M6 6l12 12"/>
                    </svg>
                </button>
            </div>
            
            <div class="chat-messages" id="chatWidgetMessages">
                <div class="welcome-message">
                    Xin chào! Tôi có thể giúp gì cho bạn?
                </div>
            </div>
            
            <div class="typing-indicator" id="chatWidgetTyping">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
            
            <div class="chat-input-area">
                <textarea 
                    id="chatWidgetInput" 
                    class="chat-input" 
                    placeholder="Nhập tin nhắn..."
                    rows="1"
                ></textarea>
                <button id="chatWidgetSend" class="send-button">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                    </svg>
                </button>
            </div>
        `;

        container.appendChild(button);
        container.appendChild(window);
        document.body.appendChild(container);

        return {
            button,
            window,
            messagesArea: document.getElementById('chatWidgetMessages'),
            input: document.getElementById('chatWidgetInput'),
            sendButton: document.getElementById('chatWidgetSend'),
            typingIndicator: document.getElementById('chatWidgetTyping'),
            closeButton: window.querySelector('.chat-close-btn')
        };
    }

    // Chat App Class
    class ChatWidget {
        constructor(elements) {
            this.button = elements.button;
            this.window = elements.window;
            this.messagesArea = elements.messagesArea;
            this.input = elements.input;
            this.sendButton = elements.sendButton;
            this.typingIndicator = elements.typingIndicator;
            this.closeButton = elements.closeButton;

            this.init();
        }

        init() {
            // Event listeners
            this.button.addEventListener('click', () => this.toggleChat(true));
            this.closeButton.addEventListener('click', () => this.toggleChat(false));
            this.input.addEventListener('input', () => this.handleInput());
            this.input.addEventListener('keypress', (e) => this.handleKeyPress(e));
            this.sendButton.addEventListener('click', () => this.sendMessage());

            // Initial state
            this.sendButton.disabled = true;
        }

        toggleChat(open) {
            if (open) {
                this.window.classList.add('open');
                this.input.focus();
            } else {
                this.window.classList.remove('open');
            }
        }

        handleInput() {
            this.input.style.height = 'auto';
            this.input.style.height = Math.min(this.input.scrollHeight, 100) + 'px';
            this.sendButton.disabled = !this.input.value.trim();
        }

        handleKeyPress(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        }

        async renderMarkdown(text) {
            return MarkdownParser.parse(text);
        }

        async addMessage(content, type = 'bot') {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;

            if (type === 'bot') {
                if (typeof content === 'object' && content.type === 'products') {
                    messageDiv.innerHTML = this.renderProducts(content.data);
                    messageDiv.style.maxWidth = '95%';
                } else if (Array.isArray(content)) {
                    for (const item of content) {
                        const itemDiv = document.createElement('div');
                        itemDiv.className = 'html-item';
                        itemDiv.innerHTML = await this.renderMarkdown(item);
                        messageDiv.appendChild(itemDiv);
                    }
                } else if (typeof content === 'string') {
                    messageDiv.innerHTML = await this.renderMarkdown(content);
                } else {
                    messageDiv.textContent = 'Invalid content';
                }
            } else {
                messageDiv.textContent = content;
            }

            this.messagesArea.appendChild(messageDiv);
            this.scrollToBottom();
        }

        renderProducts(products) {
            if (!Array.isArray(products) || products.length === 0) {
                return '<p>Không tìm thấy sản phẩm</p>';
            }

            let html = `
                <div class="products-container">
                    <h3>Kết quả tìm kiếm (${products.length} sản phẩm)</h3>
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

            products.forEach(p => {
                html += `
                    <tr>
                        <td><a href="${this.escape(p.link)}" target="_blank">${this.escape(p.name)}</a></td>
                        <td>${this.escape(p.price)}</td>
                        <td>${this.escape(p.specs)}</td>
                    </tr>
                `;
            });

            html += `</tbody></table><div class="product-grid">`;

            products.forEach(p => {
                html += `
                    <div class="product-card">
                        <a href="${this.escape(p.link)}" target="_blank" class="product-image-wrapper">
                            <img src="${this.escape(p.image)}" alt="${this.escape(p.name)}" class="product-image" onerror="this.src='https://via.placeholder.com/200'">
                        </a>
                        <div class="product-content">
                            <a href="${this.escape(p.link)}" target="_blank" class="product-name">${this.escape(p.name)}</a>
                            <div class="product-specs">${this.escape(p.specs)}</div>
                            <div class="price-wrapper">
                                <div class="price">${this.escape(p.price)}</div>
                            </div>
                            <button class="add-to-cart-btn" onclick="window.open('${this.escape(p.link)}', '_blank')">
                                Xem chi tiết
                            </button>
                        </div>
                    </div>
                `;
            });

            html += '</div></div>';
            return html;
        }

        escape(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
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
            const message = this.input.value.trim();
            if (!message) return;

            await this.addMessage(message, 'user');

            this.input.value = '';
            this.input.style.height = 'auto';
            this.input.disabled = true;
            this.sendButton.disabled = true;

            this.showTyping();

            try {
                const response = await fetch(CONFIG.apiUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: message,
                        url: window.location.href,
                        root: window.location.origin,
                        timestamp: new Date().toISOString()
                    })
                });

                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

                const data = await response.json();
                this.hideTyping();

                if (data.status === 'success') {
                    if (data.type === 'products' && data.data) {
                        await this.addMessage(data, 'bot');
                    } else if (data.message) {
                        await this.addMessage(data.message, 'bot');
                    }
                } else if (data.message) {
                    await this.addMessage(data.message, 'bot');
                } else {
                    await this.addMessage('Không có phản hồi từ server', 'system');
                }

            } catch (error) {
                console.log('Error:', error);
                this.hideTyping();
                await this.addMessage('❌ Lỗi kết nối. Vui lòng thử lại.', 'system');
            } finally {
                this.input.disabled = false;
                this.sendButton.disabled = false;
                this.input.focus();
            }
        }
    }

    // Initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            const elements = createChatWidget();
            new ChatWidget(elements);
        });
    } else {
        const elements = createChatWidget();
        new ChatWidget(elements);
    }

    // Kiểm tra nếu đã inject rồi thì không inject lại
    if (document.getElementById('overlay-styles')) {
        console.log('Styles already injected, reinitializing overlays...');
        initOverlays();
        return;
    }

    // Tạo và thêm CSS vào document
    function injectStyles() {
        const style = document.createElement('style');
        style.id = 'overlay-styles';
        style.textContent = `
            .block.relative.mb-5 {
                position: relative;
                display: block;
            }

            .overlay {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                color: black;
                border-radius: 8px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                opacity: 0;
                visibility: hidden;
                transition: all 0.3s ease;
                padding: 20px;
                z-index: 10;
            }

            .overlay.show {
                opacity: 1;
                visibility: visible;
            }

            .overlay-title {
                font-size: 16px;
                font-weight: 500;
                text-align: center;
                line-height: 1.5;
                rgba(0, 0, 0, 0.1);
            }

            .overlay-loading {
                font-size: 16px;
                -webkit-text-stroke: 1 white;
            }
        `;
        document.head.appendChild(style);
    }

    // Tạo overlay cho mỗi ảnh
    function createOverlay(text = '') {
        const overlay = document.createElement('div');
        overlay.className = 'overlay';
        overlay.innerHTML = `
            <div class="overlay-title">${text || '<div class="overlay-loading">Đang tải...</div>'}</div>
        `;
        return overlay;
    }

    // Fetch data từ API
    async function fetchOverlayData(url, overlay) {
        try {
            url = url.includes("https") ? url : window.location.origin + url
            console.log('Fetching data for:', url);

            const response = await fetch("http://127.0.0.1:8000/hover", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ href: url })
            });

            if (response.ok) {
                const result = await response.json();
                overlay.style.color= "white";

                overlay.style.background =
                    "linear-gradient(135deg, rgba(30,30,60,0.95), rgba(50,50,80,0.95))";

                overlay.querySelector('.overlay-title').innerHTML = result.result.substring(0,100) || 'Không có thông tin';
                console.log('✅ Loaded content for:', url);
            } else {
                console.log('API returned status:', response.status);
                // overlay.querySelector('.overlay-title').innerHTML = 'Lỗi tải dữ liệu';
            }
        } catch (err) {
            console.error("Error fetching data for", url, err);
            overlay.querySelector('.overlay-title').innerHTML = 'Lỗi kết nối';
        }
    }

    // Khởi tạo overlay cho tất cả ảnh
    function initOverlays() {
        // Xóa overlay cũ nếu có
        document.querySelectorAll('.overlay').forEach(el => el.remove());

        const containers = document.querySelectorAll('a:has(img)[href]:not([href="#"]):not([href=""])')

        console.log(`Found ${containers.length} products`);

        containers.forEach(container => {
            // Lấy href từ thẻ <a>
            const productUrl = container.getAttribute('href');

            if (!productUrl) {
                console.log('No href found for container:', container);
                return;
            }

            // Tạo overlay
            const overlay = createOverlay();
            container.appendChild(overlay);

            // Biến để track trạng thái đã load
            let isLoaded = false;

            // Xử lý hover - CHỈ GỌI API KHI HOVER
            container.addEventListener('mouseenter', () => {
                overlay.classList.add('show');

                // Chỉ gọi API lần đầu tiên hover
                if (!isLoaded) {
                    isLoaded = true;
                    fetchOverlayData(productUrl, overlay);
                }
            });

            container.addEventListener('mouseleave', () => {
                overlay.classList.remove('show');
            });
        });

        console.log('✅ Image overlay initialized successfully!');
    }

    // Chạy ngay lập tức
    injectStyles();
    initOverlays();

})();