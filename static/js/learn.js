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
    const quizTabBtn = document.getElementById('quiz-tab-btn'); // Still might be null if not present

    const chatbotSection = document.getElementById('media-mentor-section');
    const learnArticlesSection = document.getElementById('knowledge-hub-section');
    const quizSection = document.getElementById('quiz-section'); // Still might be null if not present

    // Knowledge Hub Elements
    const learnUnitsContainer = document.getElementById('learn-units-container');
    const totalArticlesCountDisplay = document.getElementById('total-articles-count');

    // Initialize chat history from session storage or an empty array
    let chatHistory = JSON.parse(sessionStorage.getItem('learnChatHistory') || '[]');

    // --- NEW: Learning Units Data based on the refined curriculum ---
    const learningUnitsData = [
        {
            id: 'unit1', title: 'Unit 1: What is Media Literacy?', subtitle: 'Understanding media forms, functions, and critical thinking', color: '#e3f2fd', icon: 'bbook.png', lessons: [
                { id: 'u1-l1', title: '1.1 What is Media? Forms, Functions, Evolution', read_time: '5 min read', summary: 'Explore the diverse forms and evolving functions of media in our daily lives.' },
                { id: 'u1-l2', title: '1.2 Why Media Literacy Matters: Navigating the Information Age', read_time: '6 min read', summary: 'Understand the critical importance of media literacy in a world saturated with information.' },
                { id: 'u1-l3', title: '1.3 How Media Shapes Us: Individuals and Society', read_time: '7 min read', summary: 'Examine how media shapes perceptions, behaviors, and societal norms.' },
                { id: 'u1-l4', title: '1.4 Thinking Critically About Media', read_time: '8 min read', summary: 'Learn foundational skills to analyze, evaluate, and interpret media messages effectively.' },
            ]
        },
        {
            id: 'unit2', title: 'Unit 2: How Media Messages Work', subtitle: 'Breaking down media messages and understanding persuasion', color: '#e8f5e9', icon: 'gtarget.png', lessons: [
                { id: 'u2-l1', title: '2.1 Breaking Down Media Messages: Purpose and Audience', read_time: '7 min read', summary: 'Unpack media messages by identifying their creators\' intentions and target demographics.' },
                { id: 'u2-l2', title: '2.2 The Power of Words and Framing', read_time: '8 min read', summary: 'Discover how word choice and narrative structure influence understanding and perception.' },
                { id: 'u2-l3', title: '2.3 Understanding Pictures, Videos, and Infographics', read_time: '9 min read', summary: 'Analyze the persuasive power of visual media and how it conveys information and emotion.' },
                { id: 'u2-l4', title: '2.4 Finding the Main Point: Arguments and Persuasion', read_time: '7 min read', summary: 'Distinguish between logical arguments and various rhetorical strategies used to influence.' },
            ]
        },
        {
            id: 'unit3', title: 'Unit 3: Spotting Fake News & Bias', subtitle: 'Recognizing misinformation and breaking out of echo chambers', color: '#fff3e0', icon: 'yeye.png', lessons: [
                { id: 'u3-l1', title: '3.1 What\'s the Difference? Misinformation, Disinformation, Malinformation', read_time: '6 min read', summary: 'Define and differentiate between various forms of false or misleading information.' },
                { id: 'u3-l2', title: '3.2 Uncovering Different Kinds of Bias: Personal, Political, Commercial', read_time: '7 min read', summary: 'Learn to identify and analyze different types of bias present in media content.' },
                { id: 'u3-l3', title: '3.3 Watch Out! Propaganda and Tricky Tactics', read_time: '9 min read', summary: 'Recognize common propaganda techniques and manipulative strategies used in media.' },
                { id: 'u3-l4', title: '3.4 Breaking Out of Your Bubble: Confirmation Bias and Echo Chambers', read_time: '10 min read', summary: 'Understand how personal biases and online environments can limit exposure to diverse viewpoints.' },
            ]
        },
        {
            id: 'unit4', title: 'Unit 4: Finding Reliable Information', subtitle: 'Identifying credible sources and expert content', color: '#ede7f6', icon: 'pmagnify.png', lessons: [
                { id: 'u4-l1', title: '4.1 Who Made This? Authorship and Expertise', read_time: '6 min read', summary: 'Evaluate the credentials and background of content creators and their relevance to the topic.' },
                { id: 'u4-l2', title: '4.2 Where Did This Come From? Publishers, Platforms, URLs', read_time: '7 min read', summary: 'Assess the reputation and potential biases of the outlets and platforms distributing information.' },
                { id: 'u4-l3', title: '4.3 Following the Money: Funding and Bias', read_time: '9 min read', summary: 'Investigate financial interests or affiliations that could influence media content.' },
                { id: 'u4-l4', title: '4.4 Trusting Experts: Peer Review and Research', read_time: '10 min read', summary: 'Understand the importance of peer-reviewed research and expert consensus in verifying information.' },
                { id: 'u4-l5', title: '4.5 News vs. Opinion: Different Kinds of Sources', read_time: '8 min read', summary: 'Distinguish between factual reporting, analytical pieces, and purely opinion-based content.' },
            ]
        },
        {
            id: 'unit5', title: 'Unit 5: Becoming a Fact-Checking Pro', subtitle: 'Advanced research techniques and verification skills', color: '#ffebee', icon: 'rlightning.png', lessons: [
                { id: 'u5-l1', title: '5.1 Smart Searching: How to Research Effectively', read_time: '7 min read', summary: 'Master advanced search queries, operators, and strategies to find reliable information quickly.' },
                { id: 'u5-l2', title: '5.2 Digging Deeper: Lateral Reading and Reverse Image Search', read_time: '8 min read', summary: 'Learn powerful techniques to verify information by cross-referencing and tracing image origins.' },
                { id: 'u5-l3', title: '5.3 Checking the Numbers: Verifying Data and Statistics', read_time: '9 min read', summary: 'Understand how to critically evaluate numerical data, graphs, and statistical claims.' },
                { id: 'u5-l4', title: '5.4 Is it Real? Spotting Deepfakes and AI-Generated Content', read_time: '7 min read', summary: 'Identify characteristics of synthetic media and learn tools to detect AI-generated fakes.' },
            ]
        },
        {
            id: 'unit6', title: 'Unit 6: Being Smart Online & on Social Media', subtitle: 'Digital citizenship and media literacy', color: '#e0f2f7', icon: 'bpeople.png', lessons: [
                { id: 'u6-l1', title: '6.1 Being a Good Digital Citizen: Rights and Responsibilities', read_time: '6 min read', summary: 'Understand your role and impact in the digital community, promoting positive online interactions.' },
                { id: 'u6-l2', title: '6.2 Keeping Your Info Safe: Privacy and Data Security', read_time: '8 min read', summary: 'Learn strategies to protect personal data and understand online privacy settings.' },
                { id: 'u6-l3', title: '6.3 Understanding Social Media: Algorithms and Their Effects', read_time: '9 min read', summary: 'Explore how social media platforms curate content and influence user behavior.' },
                { id: 'u6-l4', title: '6.4 Spotting Online Scams and Tricky Ads: Influencers, Sponsored Content', read_time: '7 min read', summary: 'Identify deceptive online practices, including phishing, scams, and hidden advertisements.' },
                { id: 'u6-l5', title: '6.5 Standing Up to Cyberbullying & Being Kind Online', read_time: '6 min read', summary: 'Learn how to address cyberbullying and foster a supportive and empathetic online environment.' },
                { id: 'u6-l6', title: '6.6 Your Digital Footprint: What You Leave Behind', read_time: '8 min read', summary: 'Understand the lasting impact of your online activities and how to manage your digital reputation.' },
            ]
        },
        {
            id: 'unit7', title: 'Unit 7: Creating Media & Future Trends', subtitle: 'Media creation ethics and future technologies', color: '#fce4ec', icon: 'plightning.png', lessons: [
                { id: 'u7-l1', title: '7.1 Making Media Responsibly: Ethics and Best Practices', read_time: '7 min read', summary: 'Guidelines for producing honest, accurate, and fair media content.' },
                { id: 'u7-l2', title: '7.2 Using Other People\'s Work: Copyright and Fair Use', read_time: '9 min read', summary: 'Understand legal and ethical considerations for using and sharing digital content.' },
                { id: 'u7-l3', title: '7.3 AI in Media: Friend or Foe?', read_time: '8 min read', summary: 'Explore how AI is transforming media creation, consumption, and the challenges it presents.' },
                { id: 'u7-l4', title: '7.4 The Future is Now: VR, AR, and New Ways to Get Info', read_time: '10 min read', summary: 'Consider the evolving landscape of news and information and its societal implications.' },
            ]
        }
    ];

    // Function to render markdown (using a simple regex for bold, italic, lists)
    function renderMarkdown(text) {
        // Bold
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Italic
        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
        // Headings (basic)
        text = text.replace(/^### (.*)$/gm, '<h3>$1</h3>');
        text = text.replace(/^## (.*)$/gm, '<h2>$1</h2>');
        text = text.replace(/^# (.*)$/gm, '<h1>$1</h1>');
        // Unordered lists
        text = text.replace(/^- (.*)$/gm, '<li>$1</li>');
        if (text.includes('<li>')) {
            text = `<ul>${text}</ul>`;
        }
        // Newlines to breaks
        text = text.replace(/\n/g, '<br>');
        return text;
    }

    function addMessageToChat(message, sender) {
        const messageWrapper = document.createElement('div');
        messageWrapper.classList.add('message-bubble', `${sender}-message`);

        const avatar = document.createElement('img');
        avatar.classList.add('message-profile-pic');
        avatar.src = sender === 'user' ? USER_AVATAR_URL : BOT_AVATAR_URL;
        avatar.alt = sender === 'user' ? 'User Avatar' : 'Bot Avatar';

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
                console.error("Gemini API key is missing. Please provide it.");
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
                if (response.status === 401) {
                    console.error("API keys are missing or invalid. Please enter them to use the chatbot.");
                    addMessageToChat("Error: API keys are missing or invalid. Please enter them to use the chatbot.", "bot");
                } else {
                    throw new Error(errorData.message || 'Failed to get response from chatbot.');
                }
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
            // Only add initial message if chat history is empty
            addMessageToChat("Hello! I'm your Media Mentor. I'm here to help you learn about media literacy, fact-checking, identifying bias, and navigating information online. What would you like to know?", "bot");
        }
    }
    loadChatHistory();


    // Tab functionality for Learn page
    function showTab(tabName) {
        // Ensure all sections are hidden first
        if (chatbotSection) chatbotSection.style.display = 'none';
        if (learnArticlesSection) learnArticlesSection.style.display = 'none';
        if (quizSection) quizSection.style.display = 'none';

        // Remove active class from all tabs
        if (chatbotTabBtn) chatbotTabBtn.classList.remove('active');
        if (articlesTabBtn) articlesTabBtn.classList.remove('active');
        if (quizTabBtn) quizTabBtn.classList.remove('active');

        // Show the selected tab and add active class
        if (tabName === 'chatbot' && chatbotSection && chatbotTabBtn) {
            chatbotSection.style.display = 'flex'; // Changed to flex for vertical layout
            chatbotTabBtn.classList.add('active');
        } else if (tabName === 'articles' && learnArticlesSection && articlesTabBtn) {
            learnArticlesSection.style.display = 'block';
            articlesTabBtn.classList.add('active');
            renderLearningUnits(); // Render units when this tab is shown
        } else if (tabName === 'quiz' && quizSection && quizTabBtn) {
            quizSection.style.display = 'block';
            quizTabBtn.classList.add('active');
        }
    }

    // Added null checks for tab buttons
    if (chatbotTabBtn) {
        chatbotTabBtn.addEventListener('click', () => showTab('chatbot'));
    }
    if (articlesTabBtn) {
        articlesTabBtn.addEventListener('click', () => showTab('articles'));
    }
    if (quizTabBtn) {
        quizTabBtn.addEventListener('click', () => showTab('quiz'));
    }

    // --- NEW: Knowledge Hub (Learn Units) Rendering ---
    function createUnitDropdown(unit) {
        const unitContainer = document.createElement('div');
        unitContainer.classList.add('unit-dropdown-container');
        unitContainer.dataset.unitId = unit.id; // Store unit ID for easy access

        const unitHeader = document.createElement('div');
        unitHeader.classList.add('unit-header');
        unitHeader.innerHTML = `
            <div class="unit-icon-square" style="background-color: ${unit.color};">
                <img src="/static/img/${unit.icon}" alt="${unit.title} Icon">
            </div>
            <div class="unit-text-content">
                <h3 class="unit-title">${unit.title}</h3>
                <p class="unit-subtitle">${unit.subtitle}</p>
            </div>
            <span class="unit-lesson-count">${unit.lessons.length} lessons</span>
            <img src="/static/img/down-arrow.png" alt="Toggle Arrow" class="unit-arrow-icon">
        `;
        unitContainer.appendChild(unitHeader);

        const lessonsContainer = document.createElement('div');
        lessonsContainer.classList.add('lessons-container');
        lessonsContainer.style.display = 'none'; // Initially hidden

        unit.lessons.forEach(lesson => {
            const lessonCard = document.createElement('div');
            lessonCard.classList.add('lesson-card');
            lessonCard.style.backgroundColor = unit.color; // Match unit color
            lessonCard.dataset.unitId = unit.id;
            lessonCard.dataset.lessonId = lesson.id;
            lessonCard.dataset.lessonTitle = lesson.title; // Pass title for URL

            lessonCard.innerHTML = `
                <span class="lesson-title">${lesson.title}</span>
                <a href="/learn_article/${unit.id}/${lesson.id}/${encodeURIComponent(lesson.title)}" class="start-button">
                    Start <img src="/static/img/right-arrow.png" alt="Start" class="start-icon">
                </a>
            `;
            lessonsContainer.appendChild(lessonCard);
        });
        unitContainer.appendChild(lessonsContainer);

        // Toggle functionality
        unitHeader.addEventListener('click', () => {
            const isExpanded = lessonsContainer.style.display === 'block';
            lessonsContainer.style.display = isExpanded ? 'none' : 'block';
            unitHeader.querySelector('.unit-arrow-icon').src = isExpanded ? '/static/img/down-arrow.png' : '/static/img/up-arrow.png';
            unitContainer.classList.toggle('expanded', !isExpanded); // Add/remove expanded class
        });

        return unitContainer;
    }

    function renderLearningUnits() {
        if (!learnUnitsContainer || !totalArticlesCountDisplay) {
            console.error("Knowledge Hub container or total count display not found.");
            return;
        }

        learnUnitsContainer.innerHTML = ''; // Clear previous content

        let totalLessons = 0;
        learningUnitsData.forEach(unit => {
            learnUnitsContainer.appendChild(createUnitDropdown(unit));
            totalLessons += unit.lessons.length;
        });

        totalArticlesCountDisplay.textContent = `Total: ${totalLessons} lessons across ${learningUnitsData.length} learning units`;
    }

    // Initial load of content when the page loads
    showTab('chatbot'); // Default to chatbot tab on load
    renderLearningUnits(); // Render units initially for Knowledge Hub
});