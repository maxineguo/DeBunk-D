// learn.js - Updated for new knowledge_hub_data structure

document.addEventListener('DOMContentLoaded', () => {
    // Chatbot functionality
    const chatWindow = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendChatBtn = document.getElementById('send-chat-btn');
    const clearChatBtn = document.getElementById('clear-chat-btn');
    const suggestionButtonsContainer = document.querySelector('.suggestion-buttons');

    // Tab functionality
    const chatbotTabBtn = document.getElementById('media-mentor-tab');
    const articlesTabBtn = document.getElementById('knowledge-hub-tab');
    const quizTabBtn = document.getElementById('quiz-tab-btn');

    const chatbotSection = document.getElementById('media-mentor-section');
    const learnArticlesSection = document.getElementById('knowledge-hub-section');
    const quizSection = document.getElementById('quiz-section');

    // Knowledge Hub Elements
    const learnUnitsContainer = document.getElementById('learn-units-container');
    const totalArticlesCountDisplay = document.getElementById('total-articles-count');

    // Initialize chat history
    let chatHistory = JSON.parse(sessionStorage.getItem('learnChatHistory') || '[]');

    // Updated Learning Units Data matching knowledge_hub_data.py structure
    const learningUnitsData = [
        {
            id: 'Unit 1: What is Media Literacy?',
            title: 'Unit 1: What is Media Literacy?',
            subtitle: 'Understanding media forms, functions, and critical thinking',
            color: '#e3f2fd',
            icon: 'bbook.png',
            lessons: [
                { id: '1.1', title: '1.1 What is Media? Forms, Functions, Evolution' },
                { id: '1.2', title: '1.2 Why Media Literacy Matters' },
                { id: '1.3', title: '1.3 How Media Shapes Us' },
                { id: '1.4', title: '1.4 Thinking Critically About Media' }
            ]
        },
        {
            id: 'Unit 2: How Media Messages Work',
            title: 'Unit 2: How Media Messages Work',
            subtitle: 'Breaking down media messages and understanding persuasion',
            color: '#e8f5e9',
            icon: 'gtarget.png',
            lessons: [
                { id: '2.1', title: '2.1 Breaking Down Media Messages: Purpose and Audience' },
                { id: '2.2', title: '2.2 The Power of Words and Framing' },
                { id: '2.3', title: '2.3 Understanding Pictures, Videos, and Infographics' },
                { id: '2.4', title: '2.4 Finding the Main Point: Arguments and Persuasion' }
            ]
        },
        {
            id: 'Unit 3: Spotting Fake News & Bias',
            title: 'Unit 3: Spotting Fake News & Bias',
            subtitle: 'Recognizing misinformation and breaking out of echo chambers',
            color: '#fff3e0',
            icon: 'yeye.png',
            lessons: [
                { id: '3.1', title: '3.1 What\'s the Difference? Misinformation, Disinformation, Malinformation' },
                { id: '3.2', title: '3.2 Uncovering Different Kinds of Bias' },
                { id: '3.3', title: '3.3 Watch Out! Propaganda and Tricky Tactics' },
                { id: '3.4', title: '3.4 Breaking Out of Your Bubble' }
            ]
        },
        {
            id: 'Unit 4: Finding Reliable Information',
            title: 'Unit 4: Finding Reliable Information',
            subtitle: 'Identifying credible sources and expert content',
            color: '#ede7f6',
            icon: 'pmagnify.png',
            lessons: [
                { id: '4.1', title: '4.1 Who Made This? Authorship and Expertise' },
                { id: '4.2', title: '4.2 Where Did This Come From? Publishers, Platforms, URLs' },
                { id: '4.3', title: '4.3 Following the Money: Funding and Bias' },
                { id: '4.4', title: '4.4 Trusting Experts: Peer Review and Research' },
                { id: '4.5', title: '4.5 News vs. Opinion' }
            ]
        },
        {
            id: 'Unit 5: Becoming a Fact-Checking Pro',
            title: 'Unit 5: Becoming a Fact-Checking Pro',
            subtitle: 'Advanced research techniques and verification skills',
            color: '#ffebee',
            icon: 'rlightning.png',
            lessons: [
                { id: '5.1', title: '5.1 Smart Searching: How to Research Effectively' },
                { id: '5.2', title: '5.2 Digging Deeper: Lateral Reading and Reverse Image Search' },
                { id: '5.3', title: '5.3 Checking the Numbers: Verifying Data and Statistics' },
                { id: '5.4', title: '5.4 Is it Real? Spotting Deepfakes and AI-Generated Content' }
            ]
        },
        {
            id: 'Unit 6: Being Smart Online & on Social Media',
            title: 'Unit 6: Being Smart Online & on Social Media',
            subtitle: 'Digital citizenship and online safety',
            color: '#e0f2f7',
            icon: 'bpeople.png',
            lessons: [
                { id: '6.1', title: '6.1 Being a Good Digital Citizen: Rights and Responsibilities' },
                { id: '6.2', title: '6.2 Keeping Your Info Safe: Privacy and Data Security' },
                { id: '6.3', title: '6.3 Understanding Social Media: Algorithms and Their Effects' },
                { id: '6.4', title: '6.4 Spotting Online Scams and Tricky Ads' },
                { id: '6.5', title: '6.5 Standing Up to Cyberbullying & Being Kind Online' },
                { id: '6.6', title: '6.6 Your Digital Footprint: What You Leave Behind' }
            ]
        },
        {
            id: 'Unit 7: Creating Media & Future Trends',
            title: 'Unit 7: Creating Media & Future Trends',
            subtitle: 'Media creation ethics and future technologies',
            color: '#fce4ec',
            icon: 'plightning.png',
            lessons: [
                { id: '7.1', title: '7.1 Making Media Responsibly: Ethics and Best Practices' },
                { id: '7.2', title: '7.2 Using Other People\'s Work: Copyright and Fair Use' },
                { id: '7.3', title: '7.3 AI in Media: Friend or Foe?' },
                { id: '7.4', title: '7.4 The Future is Now: VR, AR, and New Ways to Get Info' }
            ]
        }
    ];

    function renderMarkdown(text) {
        if (!text) return '';

        let html = text.replace(/\n/g, '<br>');
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
        html = html.replace(/<br>\s*-\s*(.*?)(<br>|$)/g, '<li>$1</li>');
        html = html.replace(/(<li.*?<\/li>)+/g, '<ul class="list-disc pl-5 my-2">$&</ul>');
        html = html.replace(/(\*|\-)\s/g, '');

        return html;
    }

    function addMessageToChat(message, sender) {
        const messageWrapper = document.createElement('div');
        messageWrapper.classList.add('message-bubble', `${sender}-message`);

        const avatar = document.createElement('img');
        avatar.classList.add('message-profile-pic');
        
        if (sender === 'user') {
            avatar.src = localStorage.getItem('userProfilePic') || "/static/img/avatars/default_profile.jpeg";
            avatar.alt = 'User Avatar';
        } else {
            avatar.src = BOT_AVATAR_URL;
            avatar.alt = 'Bot Avatar';
        }

        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message-content', `${sender}-content`);
        messageDiv.innerHTML = renderMarkdown(message);

        if (sender === 'user') {
            messageWrapper.appendChild(messageDiv);
            messageWrapper.appendChild(avatar);
        } else {
            messageWrapper.appendChild(avatar);
            messageWrapper.appendChild(messageDiv);
        }

        chatWindow.appendChild(messageWrapper);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    async function sendChatMessage() {
        const message = chatInput.value.trim();
        if (!message) return;

        addMessageToChat(message, 'user');
        chatInput.value = '';

        chatHistory.push({ role: 'user', parts: [{ text: message }] });
        sessionStorage.setItem('learnChatHistory', JSON.stringify(chatHistory));

        sendChatBtn.disabled = true;

        const useOwnApiKey = localStorage.getItem('useOwnApiKey') === 'true';
        let headers = { 'Content-Type': 'application/json' };
        if (useOwnApiKey) {
            const userGeminiApiKey = sessionStorage.getItem('userGeminiApiKey');
            if (!userGeminiApiKey) {
                console.error("Gemini API key is missing.");
                addMessageToChat("Error: Gemini API key is missing. Please provide it.", "bot");
                sendChatBtn.disabled = false;
                return;
            }
            headers['X-User-Gemini-API-Key'] = userGeminiApiKey;
        }

        try {
            const response = await fetch('/api/chatbot_message', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({ message: message, history: chatHistory })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Failed to get response from chatbot.');
            }
            
            const data = await response.json();
            addMessageToChat(data.response, 'bot');
            chatHistory = data.history;
            sessionStorage.setItem('learnChatHistory', JSON.stringify(chatHistory));

        } catch (error) {
            console.error('Error sending chat message:', error);
            addMessageToChat("Sorry, I'm having trouble responding right now. Please try again.", "bot");
        } finally {
            sendChatBtn.disabled = false;
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

    if (clearChatBtn) {
        clearChatBtn.addEventListener('click', () => {
            chatWindow.innerHTML = '';
            chatHistory = [];
            sessionStorage.removeItem('learnChatHistory');
            addMessageToChat("Chat cleared. How can I help you learn today?", "bot");
        });
    }

    if (suggestionButtonsContainer) {
        suggestionButtonsContainer.addEventListener('click', (event) => {
            if (event.target.classList.contains('suggestion-btn')) {
                chatInput.value = event.target.dataset.suggestion;
                sendChatMessage();
            }
        });
    }

    function loadChatHistory() {
        if (chatHistory.length > 0) {
            chatHistory.forEach(entry => {
                if (entry.role === 'user') {
                    addMessageToChat(entry.parts[0].text, 'user');
                } else if (entry.role === 'model') {
                    addMessageToChat(entry.parts[0].text, 'bot');
                }
            });
        } else {
            addMessageToChat("Hello! I'm your Media Mentor. I'm here to help you learn about media literacy, fact-checking, identifying bias, and navigating information online. What would you like to know?", "bot");
        }
    }
    loadChatHistory();

    function showTab(tabName) {
        if (chatbotSection) chatbotSection.style.display = 'none';
        if (learnArticlesSection) learnArticlesSection.style.display = 'none';
        if (quizSection) quizSection.style.display = 'none';

        if (chatbotTabBtn) chatbotTabBtn.classList.remove('active');
        if (articlesTabBtn) articlesTabBtn.classList.remove('active');
        if (quizTabBtn) quizTabBtn.classList.remove('active');

        if (tabName === 'chatbot' && chatbotSection && chatbotTabBtn) {
            chatbotSection.style.display = 'block';
            chatbotTabBtn.classList.add('active');
        } else if (tabName === 'articles' && learnArticlesSection && articlesTabBtn) {
            learnArticlesSection.style.display = 'block';
            articlesTabBtn.classList.add('active');
            renderLearningUnits();
        } else if (tabName === 'quiz' && quizSection && quizTabBtn) {
            quizSection.style.display = 'block';
            quizTabBtn.classList.add('active');
        }
    }

    if (chatbotTabBtn) {
        chatbotTabBtn.addEventListener('click', () => showTab('chatbot'));
    }
    if (articlesTabBtn) {
        articlesTabBtn.addEventListener('click', () => showTab('articles'));
    }
    if (quizTabBtn) {
        quizTabBtn.addEventListener('click', () => showTab('quiz'));
    }

    showTab('chatbot');

    function createUnitDropdown(unit) {
        const unitContainer = document.createElement('div');
        unitContainer.classList.add('unit-dropdown-container');
        unitContainer.dataset.unitId = unit.id;

        const unitHeader = document.createElement('div');
        unitHeader.classList.add('unit-header');
        unitHeader.innerHTML = `
            <div class="unit-icon-square" style="background-color: ${unit.color};">
                <img src="/static/img/${unit.icon}" alt="${unit.title} Icon">
            </div>
            <div class="unit-text-content">
                <div class="unit-title-row">
                    <h3 class="unit-title">${unit.title}</h3>
                    <span class="unit-lesson-count">${unit.lessons.length} lessons</span>
                </div>
                <p class="unit-subtitle">${unit.subtitle}</p>
            </div>
            <img src="/static/img/down-arrow.png" alt="Toggle Arrow" class="unit-arrow-icon">
        `;
        unitContainer.appendChild(unitHeader);

        const lessonsContainer = document.createElement('div');
        lessonsContainer.classList.add('lessons-container');
        lessonsContainer.style.maxHeight = '0';
        lessonsContainer.style.overflow = 'hidden';
        lessonsContainer.style.transition = 'max-height 0.3s ease-out, padding 0.3s ease-out';

        unit.lessons.forEach(lesson => {
            const lessonCard = document.createElement('div');
            lessonCard.classList.add('lesson-card');
            lessonCard.style.backgroundColor = unit.color;
            
            lessonCard.addEventListener('click', () => {
                window.location.href = `/learn/${lesson.id}`;
            });
            
            lessonCard.innerHTML = `
                <span class="lesson-title">${lesson.title}</span>
                <div class="lesson-start-indicator">
                    <span>Start</span>
                    <img src="/static/img/right-arrow.png" alt="Start" class="start-icon">
                </div>
            `;
            lessonsContainer.appendChild(lessonCard);
        });
        unitContainer.appendChild(lessonsContainer);

        unitHeader.addEventListener('click', () => {
            const isExpanded = unitContainer.classList.contains('expanded');
            const arrowIcon = unitHeader.querySelector('.unit-arrow-icon');
            
            if (isExpanded) {
                lessonsContainer.style.maxHeight = '0';
                lessonsContainer.style.paddingTop = '0';
                lessonsContainer.style.paddingBottom = '0';
                arrowIcon.classList.remove('rotated');
                unitContainer.classList.remove('expanded');
            } else {
                lessonsContainer.style.maxHeight = lessonsContainer.scrollHeight + 'px';
                lessonsContainer.style.paddingTop = '0';
                lessonsContainer.style.paddingBottom = '25px';
                arrowIcon.classList.add('rotated');
                unitContainer.classList.add('expanded');
            }
        });

        return unitContainer;
    }

    function renderLearningUnits() {
        if (!learnUnitsContainer) {
            console.error("Knowledge Hub container not found.");
            return;
        }

        learnUnitsContainer.innerHTML = '';

        let totalLessons = 0;
        learningUnitsData.forEach(unit => {
            learnUnitsContainer.appendChild(createUnitDropdown(unit));
            totalLessons += unit.lessons.length;
        });

        if (totalArticlesCountDisplay) {
            totalArticlesCountDisplay.textContent = `${totalLessons} total lessons`;
        }
    }
    // ----------------------------------------------
// ✅ AUTO SAVE PROGRESS FROM QUIZZES
// ----------------------------------------------

// Automatically detect quiz containers and track answers
    function enableQuickCheckAutoTracking() {
        // Look for any quiz blocks (adjust the selector to match your HTML)
        const quizzes = document.querySelectorAll('.quick-check, .quiz-container');

        quizzes.forEach(quiz => {
            const lessonId = quiz.dataset.lessonId || window.currentLessonId || "unknown";

            let totalQuestions = quiz.querySelectorAll('.question').length;
            let answeredCount = 0;

            // Listen for answer clicks or selections
            quiz.addEventListener('click', event => {
                if (event.target.classList.contains('answer-option')) {
                    answeredCount = Math.min(answeredCount + 1, totalQuestions);
                    recordQuickCheckProgress(lessonId, answeredCount, totalQuestions);
                }
            });

            // Optional: if your quizzes have a "Submit" button
            const submitBtn = quiz.querySelector('.submit-quiz');
            if (submitBtn) {
                submitBtn.addEventListener('click', () => {
                    recordQuickCheckProgress(lessonId, totalQuestions, totalQuestions);
                });
            }
        });
    }

    // Call this once the page loads
    enableQuickCheckAutoTracking();


// Make these functions globally accessible
    window.recordQuickCheckProgress = function (lessonId, questionsAnswered, totalQuestions) {
        const progressData = JSON.parse(localStorage.getItem('debunkd_quick_check_progress') || '{}');
        const totalData = JSON.parse(localStorage.getItem('debunkd_quick_check_totals') || '{}');

        progressData[lessonId] = Math.min(questionsAnswered, totalQuestions);
        totalData[lessonId] = totalQuestions;

        localStorage.setItem('debunkd_quick_check_progress', JSON.stringify(progressData));
        localStorage.setItem('debunkd_quick_check_totals', JSON.stringify(totalData));

        console.log(`Progress saved for ${lessonId}: ${questionsAnswered}/${totalQuestions}`);
    };

    window.calculateOverallProgress = function () {
        const progressData = JSON.parse(localStorage.getItem('debunkd_quick_check_progress') || '{}');
        const totalData = JSON.parse(localStorage.getItem('debunkd_quick_check_totals') || '{}');

        let answered = 0;
        let total = 0;

        for (const lessonId in totalData) {
            total += totalData[lessonId] || 0;
            answered += progressData[lessonId] || 0;
        }

        return total > 0 ? Math.round((answered / total) * 100) : 0;
    };

    window.resetLearningProgress = function () {
        localStorage.removeItem('debunkd_quick_check_progress');
        localStorage.removeItem('debunkd_quick_check_totals');
        console.log("All learning progress reset.");
    };

});