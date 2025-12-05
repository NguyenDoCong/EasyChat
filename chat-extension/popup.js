class ChatApp {
    constructor() {
        this.messagesArea = document.getElementById('chatMessages');
        this.textarea = document.getElementById('chatInput');
        this.sendButton = document.getElementById('sendButton');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.apiUrl = 'http://127.0.0.1:8000/crawl';
        
        this.init();
    }

    init() {
        this.textarea.addEventListener('input', () => this.handleInput());
        this.textarea.addEventListener('keypress', (e) => this.handleKeyPress(e));
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        this.sendButton.disabled = true;
        this.textarea.focus();

        // Get current tab URL
        chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
            if (tabs[0]) {
                this.currentUrl = tabs[0].url;
                console.log('Current URL:', this.currentUrl);
            }
        });
    }

    handleInput() {
        this.textarea.style.height = 'auto';
        this.textarea.style.height = Math.min(this.textarea.scrollHeight, 100) + 'px';
        this.sendButton.disabled = !this.textarea.value.trim();
    }

    handleKeyPress(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
        }
    }

    async renderMarkdown(text) {
        if (!window.marked) {
            return text.replace(/\n/g, '<br>');
        }

        try {
            return await marked.parse(text);
        } catch (error) {
            console.error('Markdown rendering error:', error);
            return text.replace(/\n/g, '<br>');
        }
    }

    async addMessage(content, type = 'bot') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        if (type === 'bot') {
            // Check if content is products object
            if (typeof content === 'object' && content.type === 'products') {
                const html = this.renderProducts(content.data);
                messageDiv.innerHTML = html;
                messageDiv.style.maxWidth = '95%';
            } else if (Array.isArray(content)) {
                // Array of HTML/markdown
                for (const item of content) {
                    const itemDiv = document.createElement('div');
                    itemDiv.className = 'html-item';
                    const html = await this.renderMarkdown(item);
                    itemDiv.innerHTML = html;
                    messageDiv.appendChild(itemDiv);
                }
            } else if (typeof content === 'string') {
                // Single string - render markdown
                const html = await this.renderMarkdown(content);
                messageDiv.innerHTML = html;
            } else {
                messageDiv.textContent = 'Invalid content format';
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

        // Render table
        let table = `
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

        products.forEach(product => {
            const name = String(product.name || 'N/A');
            const price = String(product.price || 'Liên hệ');
            const specs = String(product.specs || 'Không có thông tin');
            const link = String(product.link || '#');

            table += `
                <tr>
                    <td><a href="${this.escapeHtml(link)}" target="_blank">${this.escapeHtml(name)}</a></td>
                    <td>${this.escapeHtml(price)}</td>
                    <td>${this.escapeHtml(specs)}</td>
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
            const name = String(product.name || 'N/A');
            const link = String(product.link || '#');
            const image = String(product.image || '');
            const price = String(product.price || 'Liên hệ');
            const specs = String(product.specs || 'Không có thông tin');

            grid += `
                <div class="product-card">
                    <a href="${this.escapeHtml(link)}" target="_blank" class="product-image-wrapper">
                        <img src="${this.escapeHtml(image)}" alt="${this.escapeHtml(name)}" class="product-image" onerror="this.src='https://via.placeholder.com/200x200?text=No+Image'">
                    </a>
                    <div class="product-content">
                        <a href="${this.escapeHtml(link)}" target="_blank" class="product-name">${this.escapeHtml(name)}</a>
                        <div class="product-specs">${this.escapeHtml(specs)}</div>
                        <div class="price-wrapper">
                            <div class="price">${this.escapeHtml(price)}</div>
                        </div>
                        <button class="add-to-cart-btn" onclick="window.open('${this.escapeHtml(link)}', '_blank')">
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

        await this.addMessage(message, 'user');

        this.textarea.value = '';
        this.textarea.style.height = 'auto';
        this.textarea.disabled = true;
        this.sendButton.disabled = true;

        this.showTyping();

        try {
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    url: this.currentUrl,
                    timestamp: new Date().toISOString()
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.hideTyping();

            // Xử lý response theo format server
            if (data.status === 'success') {
                if (data.type === 'products' && data.data) {
                    // Products response
                    await this.addMessage(data, 'bot');
                } else if (data.message) {
                    // Text/markdown response
                    await this.addMessage(data.message, 'bot');
                } else {
                    await this.addMessage('Không có dữ liệu phản hồi', 'system');
                }
            } else if (data.message) {
                // Fallback: có message field
                await this.addMessage(data.message, 'bot');
            } else {
                await this.addMessage('Không có phản hồi từ server', 'system');
            }

        } catch (error) {
            console.error('Error:', error);
            this.hideTyping();
            await this.addMessage('❌ Lỗi kết nối đến server. Vui lòng thử lại.', 'system');
        } finally {
            this.textarea.disabled = false;
            this.sendButton.disabled = false;
            this.textarea.focus();
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});
