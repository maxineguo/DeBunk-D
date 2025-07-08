document.addEventListener('DOMContentLoaded', () => {
    // --- Tab Switching Logic ---
    const learnTabButtons = document.querySelectorAll('.learn-tab-btn');
    const learnTabContents = document.querySelectorAll('.learn-tab-content');

    function showTab(tabId) {
        learnTabContents.forEach(content => {
            content.style.display = 'none';
        });
        learnTabButtons.forEach(button => {
            button.classList.remove('active');
        });

        document.getElementById(`${tabId}-section`).style.display = 'block';
        document.querySelector(`[data-tab="${tabId}"]`).classList.add('active');
    }

    learnTabButtons.forEach(button => {
        button.addEventListener('click', () => {
            showTab(button.dataset.tab);
        });
    });

    // --- Chatbot Logic ---
    const chatDisplay = document.getElementById('chat-display');
    const chatInput = document.getElementById('chat-input');
    const sendChatBtn = document.getElementById('send-chat-btn');

    let chatHistory = JSON.parse(localStorage.getItem('chatHistory') || '[]');

    function appendMessage(role, text) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('chat-message', `${role}-message`);
        messageDiv.innerHTML = `<p>${text}</p>`;
        chatDisplay.appendChild(messageDiv);
        chatDisplay.scrollTop = chatDisplay.scrollHeight; // Scroll to bottom
    }

    // Load initial chat history from localStorage
    if (chatHistory.length > 1) { // Skip the initial "Hello" bot message in the HTML
        chatDisplay.innerHTML = ''; // Clear default message if history exists
        chatHistory.forEach(msg => {
            if (msg.role === 'user' || msg.role === 'model') {
                appendMessage(msg.role, msg.parts[0].text);
            }
        });
    } else {
        // If no history, ensure the initial bot message is in the history array
        // This is important because the backend expects the full context for Gemini
        const initialBotMessage = chatDisplay.querySelector('.bot-message p').textContent;
        chatHistory.unshift({"role": "model", "parts": [{"text": initialBotMessage}]});
        localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
    }


    async function sendChatMessage() {
        const message = chatInput.value.trim();
        if (!message) return;

        appendMessage('user', message);
        chatInput.value = ''; // Clear input

        // Show a "typing" indicator or similar
        const typingIndicator = document.createElement('div');
        typingIndicator.classList.add('chat-message', 'bot-message', 'typing-indicator');
        typingIndicator.innerHTML = '<p>Bot is typing...</p>';
        chatDisplay.appendChild(typingIndicator);
        chatDisplay.scrollTop = chatDisplay.scrollHeight;

        try {
            // Append current user message to history before sending
            // The Flask backend will also add the user message and then the model's response to the history it returns.
            // So we send the current `chatHistory`, and update it with the returned `updated_history`.
            const response = await fetch('/api/chatbot_message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message, history: chatHistory })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`HTTP error! status: ${response.status} - ${errorData.message || response.statusText}`);
            }

            const data = await response.json();
            
            // Remove typing indicator
            chatDisplay.removeChild(typingIndicator);

            if (data.response) {
                appendMessage('bot', data.response);
                // The backend now sends back the full updated history, including the latest user and bot messages
                chatHistory = data.history;
                localStorage.setItem('chatHistory', JSON.stringify(chatHistory)); // Save updated history
            } else {
                appendMessage('bot', 'Sorry, I could not get a response. Please try again.');
            }
        } catch (error) {
            console.error('Error sending chatbot message:', error);
            // Remove typing indicator
            chatDisplay.removeChild(typingIndicator);
            appendMessage('bot', `An error occurred: ${error.message}. Please check console.`);
        }
    }

    if (sendChatBtn) {
        sendChatBtn.addEventListener('click', sendChatMessage);
    }
    if (chatInput) {
        chatInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                sendChatMessage();
            }
        });
    }

    // --- Quiz Logic (Placeholder) ---
    // For now, let's just simulate quiz completion
    document.querySelectorAll('.view-article-btn').forEach(button => {
        button.addEventListener('click', () => {
            const articleId = button.dataset.articleId;
            // In a real scenario, you'd load article content and quizzes here
            // For now, just simulate quiz completion
            alert(`Viewing article ${articleId} and taking quiz.`);

            let quizProgress = JSON.parse(localStorage.getItem('quizProgress') || '{}');
            quizProgress[articleId] = true; // Mark as completed
            localStorage.setItem('quizProgress', JSON.stringify(quizProgress));

            // Optional: Send to backend for validation/logging (already a placeholder route)
            fetch('/api/quiz_submit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ articleId: articleId, status: 'completed' })
            }).then(response => response.json())
              .then(data => console.log('Quiz submit response:', data))
              .catch(error => console.error('Error submitting quiz:', error));

            // After quiz, user might go back to home to see updated progress
        });
    });

    // Optional: Modal for full article/quiz display
    const learnArticleModal = document.getElementById('learn-article-modal');
    const learnArticleModalCloseBtn = learnArticleModal ? learnArticleModal.querySelector('.close-button') : null;

    // Example of how to open/close this modal (you'd integrate it with the 'Read Article' buttons)
    if (learnArticleModalCloseBtn) {
        learnArticleModalCloseBtn.addEventListener('click', () => {
            learnArticleModal.style.display = 'none';
        });
    }
    window.addEventListener('click', (event) => {
        if (event.target === learnArticleModal) {
            learnArticleModal.style.display = 'none';
        }
    });

    // This ensures the correct tab is shown if the user navigates directly to /learn
    showTab('chatbot'); // Default to chatbot tab
});