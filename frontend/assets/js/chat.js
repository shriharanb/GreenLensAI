const chatContainer = document.getElementById('chatContainer');
const welcomeScreen = document.getElementById('welcomeScreen');
const messagesList = document.getElementById('messagesList');
const historyList = document.getElementById('historyList');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const attachBtn = document.getElementById('attachBtn');
const attachDropdown = document.getElementById('attachDropdown');
const sidebar = document.querySelector('.sidebar');
const sidebarToggle = document.getElementById('sidebarToggle');
const logoutBtn = document.getElementById('logoutBtn');
const newChatBtn = document.getElementById('newChatBtn');
const mobileNewChatBtn = document.getElementById('mobileNewChatBtn');

let currentConversationId = localStorage.getItem('current_conversation_id') || null;

// --- NEW CHAT LOGIC ---
function startNewChat() {
    currentConversationId = null;
    localStorage.removeItem('current_conversation_id');
    messagesList.innerHTML = '';
    welcomeScreen.style.display = 'flex';
    userInput.value = '';
    userInput.focus();
}

if (newChatBtn) {
    newChatBtn.addEventListener('click', startNewChat);
}

if (mobileNewChatBtn) {
    mobileNewChatBtn.addEventListener('click', startNewChat);
}

// --- LOGOUT LOGIC ---
if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem("farmer_id");
        window.location.href = "./Pages/login.html";
    });
}

// --- ATTACHMENT LOGIC ---
attachBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    // Toggle using a simple check
    if (attachDropdown.style.display === 'block') {
        attachDropdown.style.display = 'none';
    } else {
        attachDropdown.style.display = 'block';
    }
});

// Close dropdown if user clicks anywhere else on the screen
document.addEventListener('click', () => {
    attachDropdown.style.display = 'none';
});

// --- SIDEBAR LOGIC ---
sidebarToggle.addEventListener('click', (e) => {
    e.stopPropagation();
    sidebar.classList.toggle('closed');

    const icon = sidebarToggle.querySelector('i');
    if (sidebar.classList.contains('closed')) {
        icon.className = 'fa-solid fa-chevron-right';
    } else {
        icon.className = 'fa-solid fa-bars';
    }
});

// --- CHAT LOGIC ---
function setInput(text) {
    userInput.value = text;
    userInput.focus();
}

const API_BASE = "http://localhost:8000/api";
let currentFarmerId = localStorage.getItem("farmer_id") || "guest_farmer";

async function createMessageElement(content, type, imagePath = null) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', type);
    const iconClass = type === 'user' ? 'fa-user' : 'fa-leaf';
    const avatarClass = type === 'user' ? 'user-av' : 'bot-av';

    let messageContent = `<p>${content}</p>`;
    if (imagePath) {
        // Django media handling: imagePath might be a relative path like 'uploads/...'
        const imageUrl = imagePath.startsWith('http') ? imagePath : `http://localhost:8000/media/${imagePath}`;
        messageContent = `<img src="${imageUrl}" style="max-width: 200px; border-radius: 8px; margin-bottom: 8px;"><p>${content}</p>`;
    }

    msgDiv.innerHTML = `
        <div class="avatar ${avatarClass}">
            <i class="fa-solid ${iconClass}" style="color: white; font-size: 14px;"></i>
        </div>
        <div class="message-content">
            ${messageContent}
        </div>`;
    return msgDiv;
}

async function loadChatHistory() {
    try {
        // 1. Fetch Conversations for Sidebar
        const convResponse = await fetch(`${API_BASE}/chat/conversations/${currentFarmerId}/`);
        if (convResponse.ok) {
            const conversations = await convResponse.json();
            historyList.innerHTML = '';
            for (const conv of conversations) {
                addConversationToSidebar(conv.title, conv.id);
            }
        }

        // 2. If we have a current conversation, load its messages
        if (currentConversationId) {
            const msgResponse = await fetch(`${API_BASE}/chat/history/${currentFarmerId}/?conversation_id=${currentConversationId}`);
            if (msgResponse.ok) {
                const messages = await msgResponse.json();

                welcomeScreen.style.display = 'none';
                messagesList.innerHTML = '';

                if (messages.length > 0) {
                    for (const msg of messages) {
                        const msgEl = await createMessageElement(msg.content, msg.message_type, msg.image_path);
                        messagesList.appendChild(msgEl);
                    }
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            }
        } else {
            welcomeScreen.style.display = 'flex';
            messagesList.innerHTML = '';
        }
    } catch (error) {
        console.error("Failed to load history:", error);
    }
}

function addConversationToSidebar(title, id) {
    if (!historyList) return;

    const div = document.createElement('div');
    div.className = 'history-item';
    if (String(id) === String(currentConversationId)) {
        div.classList.add('active');
    }

    // Title area (clickable)
    const titleSpan = document.createElement('span');
    titleSpan.className = 'history-item-title';
    titleSpan.innerHTML = `<i class="fa-regular fa-message"></i> ${title}`;
    titleSpan.title = title;
    titleSpan.onclick = () => {
        currentConversationId = id;
        localStorage.setItem('current_conversation_id', id);
        loadChatHistory();
        if (window.innerWidth <= 768) {
            sidebar.classList.add('closed');
        }
    };

    // Delete button
    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'history-delete-btn';
    deleteBtn.innerHTML = '<i class="fa-solid fa-trash-can"></i>';
    deleteBtn.title = 'Delete conversation';
    deleteBtn.onclick = (e) => {
        e.stopPropagation();
        deleteConversation(id);
    };

    div.appendChild(titleSpan);
    div.appendChild(deleteBtn);
    historyList.appendChild(div);
}

async function deleteConversation(conversationId) {
    if (!confirm('Delete this conversation? This cannot be undone.')) return;

    try {
        const response = await fetch(
            `${API_BASE}/chat/conversations/${conversationId}/delete/?farmer_id=${currentFarmerId}`,
            { method: 'DELETE' }
        );

        if (!response.ok) {
            const data = await response.json();
            alert(data.error || 'Failed to delete conversation.');
            return;
        }

        // If we deleted the active conversation, reset to welcome screen
        if (String(conversationId) === String(currentConversationId)) {
            startNewChat();
        }

        // Refresh sidebar
        loadChatHistory();
    } catch (error) {
        console.error('Delete error:', error);
        alert('Failed to delete conversation.');
    }
}

function addHistoryItem(text) {
    // Deprecated: Sidebar is updated when a new conversation id is returned
}

// Load history on start
loadChatHistory();

async function handleSend() {
    const text = userInput.value.trim();
    if (!text) return;

    welcomeScreen.style.display = 'none';
    const userMsgEl = await createMessageElement(text, 'user');
    messagesList.appendChild(userMsgEl);
    userInput.value = '';
    chatContainer.scrollTop = chatContainer.scrollHeight;

    try {
        // Get selected language

        // Get selected language
        const languageSelect = document.getElementById('languageSelect');
        const language = languageSelect ? languageSelect.value : 'en';

        // Get bot response from real API
        const response = await fetch(`${API_BASE}/chat/ask/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                farmer_id: currentFarmerId,
                conversation_id: currentConversationId,
                message: text,
                language: language || 'en'
            })
        });

        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }

        const data = await response.json();

        // If it was a new conversation, save the ID
        if (!currentConversationId && data.conversation_id) {
            currentConversationId = data.conversation_id;
            localStorage.setItem('current_conversation_id', currentConversationId);
            // Refresh sidebar to show new conversation title
            loadChatHistory();
        }

        const responseText = data.response;

        const botMsgEl = await createMessageElement(responseText, 'bot');
        messagesList.appendChild(botMsgEl);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    } catch (error) {
        console.error("Chat error:", error);
        const errorEl = await createMessageElement("Sorry, I encountered an error processing your request.", 'bot');
        messagesList.appendChild(errorEl);
    }
}

sendBtn.addEventListener('click', handleSend);
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleSend();
});
// Select the hidden file input
const fileInput = document.querySelector('input[type="file"]');

// When user selects a file
fileInput.addEventListener('change', function (e) {
    const file = e.target.files[0];

    // If no file selected (user cancelled)
    if (!file) return;

    // Allowed extensions (lowercase)
    const allowedExtensions = ['jpg', 'jpeg', 'png'];

    // Get file extension
    const fileName = file.name.toLowerCase();
    const extension = fileName.split('.').pop();   // gets the part after last dot

    // Also check MIME type (more secure)
    const allowedMimeTypes = ['image/jpeg', 'image/png'];

    const isValidExtension = allowedExtensions.includes(extension);
    const isValidMime = allowedMimeTypes.includes(file.type);

    // Final validation
    if (!isValidExtension || !isValidMime || !file.type.startsWith('image/')) {
        alert('Only (.jpg,.jpeg and .png) files are allowed!');
        e.target.value = '';
        return;
    }

    // If we reach here → file is valid!
    console.log('Valid file selected:', file.name);
    uploadImage(file);
});
