/**
 * Chat Widget for KRX Sector Rotation Dashboard
 *
 * Features:
 * - Floating chat button (bottom-right)
 * - Expandable chat panel
 * - Conversation history persistence
 * - i18n support (Korean/English)
 * - Dark theme matching dashboard
 */

(function() {
    'use strict';

    // Configuration
    const API_BASE = window.location.origin;
    const STORAGE_KEY = 'krx-chat-conversation-id';

    // State
    let isOpen = false;
    // Clear old conversation ID to fix stale data issues
    let storedId = localStorage.getItem(STORAGE_KEY);
    let conversationId = null; // Start fresh each session
    if (storedId) {
        console.log('Clearing old conversation ID:', storedId);
        localStorage.removeItem(STORAGE_KEY);
    }
    let isLoading = false;

    // Translations
    const translations = {
        ko: {
            title: 'AI 투자 어시스턴트',
            subtitle: '섹터 로테이션 Q&A',
            placeholder: '질문을 입력하세요...',
            send: '전송',
            newChat: '새 대화',
            thinking: '답변 생성 중...',
            error: '오류가 발생했습니다. 다시 시도해주세요.',
            welcome: '안녕하세요! KRX 섹터 로테이션 분석에 대해 질문해주세요.\n\n예시 질문:\n• 오늘 모멘텀 상위 종목은?\n• TIER 1 테마는 무엇인가요?\n• 군집성이 가장 강한 테마는?',
            connectionError: 'API 연결에 실패했습니다.',
        },
        en: {
            title: 'AI Investment Assistant',
            subtitle: 'Sector Rotation Q&A',
            placeholder: 'Type your question...',
            send: 'Send',
            newChat: 'New Chat',
            thinking: 'Generating response...',
            error: 'An error occurred. Please try again.',
            welcome: 'Hello! Ask me about KRX Sector Rotation analysis.\n\nExample questions:\n• Which stocks have highest momentum today?\n• What are the TIER 1 themes?\n• Which themes have strongest cohesion?',
            connectionError: 'Failed to connect to API.',
        }
    };

    // Get current language from page (if available) or localStorage
    function getCurrentLang() {
        // Check if page has language state
        if (typeof currentLang !== 'undefined') {
            return currentLang;
        }
        // Fallback to localStorage
        return localStorage.getItem('krx-dashboard-lang') || 'ko';
    }

    function t(key) {
        const lang = getCurrentLang();
        return translations[lang]?.[key] || translations.ko[key] || key;
    }

    // Inject styles
    const styles = `
        .chat-widget-btn {
            position: fixed;
            bottom: 24px;
            right: 24px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .chat-widget-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 6px 25px rgba(59, 130, 246, 0.5);
        }

        .chat-widget-btn svg {
            width: 28px;
            height: 28px;
            fill: white;
        }

        .chat-widget-panel {
            position: fixed;
            bottom: 96px;
            right: 24px;
            width: 380px;
            height: 520px;
            background: #1e293b;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            z-index: 9998;
            display: none;
            flex-direction: column;
            overflow: hidden;
            border: 1px solid #334155;
        }

        .chat-widget-panel.open {
            display: flex;
            animation: slideUp 0.3s ease-out;
        }

        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .chat-header {
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            padding: 16px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .chat-header-title {
            color: white;
        }

        .chat-header-title h3 {
            margin: 0;
            font-size: 16px;
            font-weight: 600;
        }

        .chat-header-title span {
            font-size: 12px;
            opacity: 0.8;
        }

        .chat-header-actions {
            display: flex;
            gap: 8px;
        }

        .chat-header-btn {
            background: rgba(255,255,255,0.1);
            border: none;
            color: white;
            padding: 6px 10px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            transition: background 0.2s;
        }

        .chat-header-btn:hover {
            background: rgba(255,255,255,0.2);
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .chat-message {
            max-width: 85%;
            padding: 12px 16px;
            border-radius: 12px;
            font-size: 14px;
            line-height: 1.5;
            white-space: pre-wrap;
            word-wrap: break-word;
        }

        .chat-message.user {
            align-self: flex-end;
            background: #3b82f6;
            color: white;
            border-bottom-right-radius: 4px;
        }

        .chat-message.assistant {
            align-self: flex-start;
            background: #334155;
            color: #e2e8f0;
            border-bottom-left-radius: 4px;
        }

        .chat-message.system {
            align-self: center;
            background: #1e293b;
            color: #94a3b8;
            font-size: 13px;
            text-align: center;
            border: 1px dashed #475569;
        }

        .chat-link {
            color: #60a5fa;
            text-decoration: underline;
            cursor: pointer;
            transition: color 0.2s;
        }

        .chat-link:hover {
            color: #93c5fd;
        }

        .chat-message.loading {
            display: flex;
            gap: 4px;
            align-items: center;
        }

        .chat-message.loading .dot {
            width: 8px;
            height: 8px;
            background: #64748b;
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out;
        }

        .chat-message.loading .dot:nth-child(1) { animation-delay: -0.32s; }
        .chat-message.loading .dot:nth-child(2) { animation-delay: -0.16s; }

        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }

        .chat-input-container {
            padding: 16px;
            background: #0f172a;
            border-top: 1px solid #334155;
            display: flex;
            gap: 8px;
        }

        .chat-input {
            flex: 1;
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 12px 16px;
            color: #e2e8f0;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }

        .chat-input:focus {
            border-color: #3b82f6;
        }

        .chat-input::placeholder {
            color: #64748b;
        }

        .chat-send-btn {
            background: #3b82f6;
            border: none;
            border-radius: 8px;
            padding: 12px 20px;
            color: white;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: background 0.2s;
        }

        .chat-send-btn:hover:not(:disabled) {
            background: #2563eb;
        }

        .chat-send-btn:disabled {
            background: #475569;
            cursor: not-allowed;
        }

        /* Scrollbar styling */
        .chat-messages::-webkit-scrollbar {
            width: 6px;
        }

        .chat-messages::-webkit-scrollbar-track {
            background: transparent;
        }

        .chat-messages::-webkit-scrollbar-thumb {
            background: #475569;
            border-radius: 3px;
        }

        .chat-messages::-webkit-scrollbar-thumb:hover {
            background: #64748b;
        }

        /* Mobile responsive */
        @media (max-width: 480px) {
            .chat-widget-panel {
                width: calc(100vw - 32px);
                height: calc(100vh - 120px);
                bottom: 80px;
                right: 16px;
            }

            .chat-widget-btn {
                bottom: 16px;
                right: 16px;
                width: 56px;
                height: 56px;
            }
        }
    `;

    // Create style element
    const styleEl = document.createElement('style');
    styleEl.textContent = styles;
    document.head.appendChild(styleEl);

    // Create widget HTML
    function createWidget() {
        // Chat button
        const btn = document.createElement('button');
        btn.className = 'chat-widget-btn';
        btn.innerHTML = `
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
                <path d="M7 9h10v2H7zm0-3h10v2H7zm0 6h7v2H7z"/>
            </svg>
        `;
        btn.onclick = togglePanel;
        document.body.appendChild(btn);

        // Chat panel
        const panel = document.createElement('div');
        panel.className = 'chat-widget-panel';
        panel.id = 'chat-widget-panel';
        panel.innerHTML = `
            <div class="chat-header">
                <div class="chat-header-title">
                    <h3>${t('title')}</h3>
                    <span>${t('subtitle')}</span>
                </div>
                <div class="chat-header-actions">
                    <button class="chat-header-btn" onclick="chatWidget.newConversation()">${t('newChat')}</button>
                </div>
            </div>
            <div class="chat-messages" id="chat-messages">
                <div class="chat-message system">${t('welcome')}</div>
            </div>
            <div class="chat-input-container">
                <input type="text" class="chat-input" id="chat-input" placeholder="${t('placeholder')}" />
                <button class="chat-send-btn" id="chat-send-btn" onclick="chatWidget.sendMessage()">${t('send')}</button>
            </div>
        `;
        document.body.appendChild(panel);

        // Enter key handler
        document.getElementById('chat-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !isLoading) {
                sendMessage();
            }
        });

        // Load existing conversation
        if (conversationId) {
            loadConversation(conversationId);
        }
    }

    function togglePanel() {
        isOpen = !isOpen;
        const panel = document.getElementById('chat-widget-panel');
        if (isOpen) {
            panel.classList.add('open');
            updateTexts();
            document.getElementById('chat-input').focus();
        } else {
            panel.classList.remove('open');
        }
    }

    function updateTexts() {
        // Update all translatable elements
        const panel = document.getElementById('chat-widget-panel');
        if (!panel) return;

        panel.querySelector('.chat-header-title h3').textContent = t('title');
        panel.querySelector('.chat-header-title span').textContent = t('subtitle');
        panel.querySelector('.chat-header-btn').textContent = t('newChat');
        document.getElementById('chat-input').placeholder = t('placeholder');
        document.getElementById('chat-send-btn').textContent = t('send');
    }

    function formatMessageContent(content) {
        // Escape HTML first for security
        let formatted = content
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        // Convert dashboard page paths to clickable links
        // Match patterns like /breakout.html, /signals.html, etc.
        formatted = formatted.replace(
            /\/([\w-]+\.html)/g,
            '<a href="/$1" class="chat-link" target="_blank">/$1</a>'
        );

        // Convert http://localhost:8000 URLs
        formatted = formatted.replace(
            /http:\/\/localhost:8000(\/[\w-]*\.?[\w]*)?/g,
            (match, path) => {
                const displayPath = path || '/';
                return `<a href="${displayPath}" class="chat-link" target="_blank">${match}</a>`;
            }
        );

        // Convert full URLs (http/https)
        formatted = formatted.replace(
            /(https?:\/\/[^\s<]+)/g,
            '<a href="$1" class="chat-link" target="_blank">$1</a>'
        );

        return formatted;
    }

    function addMessage(role, content) {
        const messagesEl = document.getElementById('chat-messages');
        const msgEl = document.createElement('div');
        msgEl.className = `chat-message ${role}`;

        // Format assistant messages with clickable links
        if (role === 'assistant') {
            msgEl.innerHTML = formatMessageContent(content);
        } else {
            msgEl.textContent = content;
        }

        messagesEl.appendChild(msgEl);
        messagesEl.scrollTop = messagesEl.scrollHeight;
        return msgEl;
    }

    function addLoadingMessage() {
        const messagesEl = document.getElementById('chat-messages');
        const msgEl = document.createElement('div');
        msgEl.className = 'chat-message assistant loading';
        msgEl.id = 'loading-message';
        msgEl.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
        messagesEl.appendChild(msgEl);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function removeLoadingMessage() {
        const loadingEl = document.getElementById('loading-message');
        if (loadingEl) {
            loadingEl.remove();
        }
    }

    async function sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();

        if (!message || isLoading) return;

        isLoading = true;
        const sendBtn = document.getElementById('chat-send-btn');
        sendBtn.disabled = true;

        // Add user message
        addMessage('user', message);
        input.value = '';

        // Show loading
        addLoadingMessage();

        try {
            console.log('Sending chat request to:', `${API_BASE}/api/chat/message`);
            console.log('Payload:', { message, conversation_id: conversationId, language: getCurrentLang() });

            // Create abort controller for timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s timeout

            const response = await fetch(`${API_BASE}/api/chat/message`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    conversation_id: conversationId,
                    language: getCurrentLang()
                }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);
            console.log('Response status:', response.status);

            removeLoadingMessage();

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || t('error'));
            }

            const data = await response.json();

            // Save conversation ID
            if (data.conversation_id) {
                conversationId = data.conversation_id;
                localStorage.setItem(STORAGE_KEY, conversationId);
            }

            // Add assistant message
            addMessage('assistant', data.response);

        } catch (error) {
            removeLoadingMessage();
            console.error('Chat error:', error);
            // Show more detailed error
            let errorMsg = t('error');
            if (error.message) {
                errorMsg += '\n' + error.message;
            }
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                errorMsg += '\n[Network error - check connection]';
            }
            addMessage('system', errorMsg);
        } finally {
            isLoading = false;
            sendBtn.disabled = false;
            input.focus();
        }
    }

    async function loadConversation(convId) {
        try {
            const response = await fetch(`${API_BASE}/api/chat/history/${convId}`);

            if (!response.ok) {
                // Conversation not found, clear stored ID
                localStorage.removeItem(STORAGE_KEY);
                conversationId = null;
                return;
            }

            const data = await response.json();
            const messagesEl = document.getElementById('chat-messages');

            // Clear current messages
            messagesEl.innerHTML = '';

            // Add welcome message
            const welcomeEl = document.createElement('div');
            welcomeEl.className = 'chat-message system';
            welcomeEl.textContent = t('welcome');
            messagesEl.appendChild(welcomeEl);

            // Add conversation messages
            for (const msg of data.messages) {
                addMessage(msg.role, msg.content);
            }

        } catch (error) {
            console.error('Failed to load conversation:', error);
            localStorage.removeItem(STORAGE_KEY);
            conversationId = null;
        }
    }

    async function newConversation() {
        // Clear local state
        conversationId = null;
        localStorage.removeItem(STORAGE_KEY);

        // Clear messages
        const messagesEl = document.getElementById('chat-messages');
        messagesEl.innerHTML = '';

        // Add welcome message
        const welcomeEl = document.createElement('div');
        welcomeEl.className = 'chat-message system';
        welcomeEl.textContent = t('welcome');
        messagesEl.appendChild(welcomeEl);

        // Focus input
        document.getElementById('chat-input').focus();
    }

    // Initialize widget when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createWidget);
    } else {
        createWidget();
    }

    // Expose functions globally
    window.chatWidget = {
        toggle: togglePanel,
        sendMessage: sendMessage,
        newConversation: newConversation,
        updateTexts: updateTexts
    };

    // Listen for language changes (if page supports it)
    window.addEventListener('languageChanged', updateTexts);

})();
