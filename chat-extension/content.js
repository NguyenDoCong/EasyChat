(function() {
    const chatButton = document.createElement('div');
    chatButton.id = 'chat-assistant-button';
    chatButton.innerHTML = '💬';
    chatButton.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 56px;
        height: 56px;
        background: #2563eb;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 999999;
        transition: transform 0.2s;
    `;

    chatButton.addEventListener('mouseenter', () => {
        chatButton.style.transform = 'scale(1.1)';
    });

    chatButton.addEventListener('mouseleave', () => {
        chatButton.style.transform = 'scale(1)';
    });

    chatButton.addEventListener('click', () => {
        // Open extension popup
        chrome.runtime.sendMessage({action: 'openPopup'});
    });

    document.body.appendChild(chatButton);
})();
