// ============================================
// background.js (Optional - for handling messages)
// ============================================
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'openPopup') {
        chrome.action.openPopup();
    }
});