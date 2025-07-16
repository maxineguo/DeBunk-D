document.addEventListener('DOMContentLoaded', () => {
    // Chatbot functionality
    const chatWindow = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const sendChatBtn = document.getElementById('send-chat-btn');
    const clearChatBtn = document.getElementById('clear-chat-btn');
    const suggestionButtonsContainer = document.querySelector('.suggestion-buttons'); // This might be null if not present

    // Tab functionality
    const chatbotTabBtn = document.getElementById('media-mentor-tab');
    const articlesTabBtn = document.getElementById('knowledge-hub-tab');
    const quizTabBtn = document.getElementById('quiz-tab-btn'); // This might be null if not present

    const chatbotSection = document.getElementById('media-mentor-section');
    const learnArticlesSection = document.getElementById('knowledge-hub-section');
    const quizSection = document.getElementById('quiz-section'); // This might be null if not present

    // Knowledge Hub Elements
    const categoryFilter = document.getElementById('category-filter');
    const difficultyFilter = document.getElementById('difficulty-filter');
    const articlesCountDisplay = document.getElementById('articles-count');
    const learnArticlesGrid = document.getElementById('learn-articles-grid');

    // Initialize chat history from session storage or an empty array
    let chatHistory = JSON.parse(sessionStorage.getItem('learnChatHistory') || '[]');

    // Placeholder for learning articles data (now populated with provided titles)
    const learningArticlesData = [
        // Unit 1: The Importance of Media Literacy
        { id: 'u1-l1', category: 'Fundamentals', difficulty: 'Beginner', title: 'Why Media Literacy Matters in Today\'s World', read_time: '5 min read', summary: 'Explore the critical role of media literacy in navigating the modern information landscape.' },
        { id: 'u1-l2', category: 'Fundamentals', difficulty: 'Beginner', title: 'The Impact of Media on Individuals and Society', read_time: '6 min read', summary: 'Understand how media shapes our perceptions, behaviors, and societal norms.' },
        { id: 'u1-l3', category: 'Fundamentals', difficulty: 'Beginner', title: 'Navigating Information Overload', read_time: '7 min read', summary: 'Strategies for managing the vast amount of information available and focusing on what matters.' },
        { id: 'u1-l4', category: 'Fundamentals', difficulty: 'Beginner', title: 'Developing Critical Thinking Skills for Media Consumption', read_time: '8 min read', summary: 'Learn to analyze, evaluate, and interpret media messages effectively.' },
        { id: 'u1-l5', category: 'Fundamentals', difficulty: 'Beginner', title: 'Media Literacy as a Foundation for Informed Decision-Making', read_time: '6 min read', summary: 'How strong media literacy skills empower better choices in personal and civic life.' },

        // Unit 2: Understanding Media and Its Purpose
        { id: 'u2-l1', category: 'Understanding Media', difficulty: 'Beginner', title: 'What is Media Literacy?', read_time: '5 min read', summary: 'A foundational look at the definition and scope of media literacy.' },
        { id: 'u2-l2', category: 'Understanding Media', difficulty: 'Beginner', title: 'The Role of Media in Society', read_time: '7 min read', summary: 'Examining the various functions media serves in a democratic society.' },
        { id: 'u2-l3', category: 'Understanding Media', difficulty: 'Beginner', title: 'Different Forms of Media (Print, Broadcast, Digital, Social)', read_time: '8 min read', summary: 'An overview of the diverse platforms and formats through which media is consumed.' },
        { id: 'u2-l4', category: 'Understanding Media', difficulty: 'Beginner', title: 'Media as Information, Entertainment, and Persuasion', read_time: '6 min read', summary: 'Differentiating between the primary purposes of various media content.' },

        // Unit 3: Credible Sources
        { id: 'u3-l1', category: 'Credible Sources', difficulty: 'Intermediate', title: 'Overview of Source Credibility', read_time: '6 min read', summary: 'Introduction to the principles of evaluating information sources for trustworthiness.' },
        { id: 'u3-l2', category: 'Credible Sources', difficulty: 'Intermediate', title: 'Identifying Credible Authors/Creators', read_time: '7 min read', summary: 'Techniques for researching and verifying the expertise and reputation of content creators.' },
        { id: 'u3-l3', category: 'Credible Sources', difficulty: 'Intermediate', title: 'Evaluating Credible Publishers/Platforms', read_time: '8 min read', summary: 'Assessing the reliability of the outlets and platforms distributing information.' },
        { id: 'u3-l4', category: 'Credible Sources', difficulty: 'Intermediate', title: 'Recognizing Red Flags in Sources (e.g., lack of attribution, sensationalism)', read_time: '9 min read', summary: 'Key indicators that suggest a source may not be reliable or unbiased.' },
        { id: 'u3-l5', category: 'Credible Sources', difficulty: 'Intermediate', title: 'Fact-Checking Tools and Techniques', read_time: '10 min read', summary: 'Practical methods and resources for verifying facts and claims.' },

        // Unit 4: Identifying Bias
        { id: 'u4-l1', category: 'Identifying Bias', difficulty: 'Intermediate', title: 'What is Bias? (Personal, Systemic, Media)', read_time: '7 min read', summary: 'Defining different forms of bias that influence information.' },
        { id: 'u4-l2', category: 'Identifying Bias', difficulty: 'Intermediate', title: 'Types of Media Bias (Political, Commercial, Cultural)', read_time: '8 min read', summary: 'Exploring various categories of bias prevalent in media content.' },
        { id: 'u4-l3', category: 'Identifying Bias', difficulty: 'Intermediate', title: 'Recognizing Bias in News Reporting (Word Choice, Omission, Placement)', read_time: '9 min read', summary: 'Practical tips for detecting subtle and overt forms of bias in news.' },
        { id: 'u4-l4', category: 'Identifying Bias', difficulty: 'Intermediate', title: 'Understanding Confirmation Bias and Echo Chambers', read_time: '7 min read', summary: 'How personal biases and online environments can reinforce existing beliefs.' },
        { id: 'u4-l5', category: 'Identifying Bias', difficulty: 'Intermediate', title: 'Strategies for Detecting and Mitigating Bias', read_time: '10 min read', summary: 'Methods to critically analyze information and reduce the impact of bias.' },

        // Unit 5: Deconstructing Media Messages
        { id: 'u5-l1', category: 'Deconstructing Messages', difficulty: 'Advanced', title: 'Analyzing Headlines and Lead Paragraphs', read_time: '6 min read', summary: 'Understanding how initial text elements frame and influence perception.' },
        { id: 'u5-l2', category: 'Deconstructing Messages', difficulty: 'Advanced', title: 'Understanding Visuals (Images, Videos, Infographics)', read_time: '9 min read', summary: 'The power of visual media to convey messages and evoke emotions.' },
        { id: 'u5-l3', category: 'Deconstructing Messages', difficulty: 'Advanced', title: 'The Power of Language and Framing', read_time: '8 min read', summary: 'How word choice and narrative structure shape understanding.' },
        { id: 'u5-l4', category: 'Deconstructing Messages', difficulty: 'Advanced', title: 'Identifying Arguments and Appeals (Logic vs. Emotion)', read_time: '7 min read', summary: 'Distinguishing between rational arguments and emotional manipulation.' },
        { id: 'u5-l5', category: 'Deconstructing Messages', difficulty: 'Advanced', title: 'Recognizing Propaganda Techniques', read_time: '10 min read', summary: 'Identifying common persuasive tactics used to influence opinions.' },

        // Unit 6: Digital Citizenship and Online Safety
        { id: 'u6-l1', category: 'Digital Citizenship', difficulty: 'Intermediate', title: 'Navigating the Digital Landscape', read_time: '6 min read', summary: 'Essential skills for safe and responsible online interaction.' },
        { id: 'u6-l2', category: 'Digital Citizenship', difficulty: 'Intermediate', title: 'Understanding Privacy and Data Security', read_time: '8 min read', summary: 'Protecting personal information and understanding online data practices.' },
        { id: 'u6-l3', category: 'Digital Citizenship', difficulty: 'Intermediate', title: 'Recognizing and Avoiding Misinformation/Disinformation', read_time: '9 min read', summary: 'Strategies to combat false and misleading content online.' },
        { id: 'u6-l4', category: 'Digital Citizenship', difficulty: 'Intermediate', title: 'Identifying Online Scams and Phishing', read_time: '7 min read', summary: 'How to spot and avoid common online threats.' },
        { id: 'u6-l5', category: 'Digital Citizenship', difficulty: 'Intermediate', title: 'Digital Footprint and Online Reputation', read_time: '6 min read', summary: 'Managing your online presence and its long-term implications.' },

        // Unit 7: Social Media Literacy
        { id: 'u7-l1', category: 'Social Media Literacy', difficulty: 'Intermediate', title: 'How Social Media Algorithms Work', read_time: '7 min read', summary: 'Understanding the mechanics behind content delivery on social platforms.' },
        { id: 'u7-l2', category: 'Social Media Literacy', difficulty: 'Intermediate', title: 'The Impact of Social Media on Information Consumption', read_time: '8 min read', summary: 'Analyzing how social media influences what and how we learn.' },
        { id: 'u7-l3', category: 'Social Media Literacy', difficulty: 'Intermediate', title: 'Verifying Information on Social Platforms', read_time: '9 min read', summary: 'Specific techniques for fact-checking content shared on social media.' },
        { id: 'u7-l4', category: 'Social Media Literacy', difficulty: 'Intermediate', title: 'Understanding Influencers and Sponsored Content', read_time: '6 min read', summary: 'Recognizing commercial and promotional content on social media.' },
        { id: 'u7-l5', category: 'Social Media Literacy', difficulty: 'Intermediate', title: 'Responsible Social Media Engagement', read_time: '7 min read', summary: 'Best practices for ethical and constructive interaction online.' },

        // Unit 8: Media and Ethics
        { id: 'u8-l1', category: 'Media and Ethics', difficulty: 'Advanced', title: 'The Role of Ethics in Journalism', read_time: '8 min read', summary: 'Examining the ethical principles guiding journalistic practice.' },
        { id: 'u8-l2', category: 'Media and Ethics', difficulty: 'Advanced', title: 'Copyright, Plagiarism, and Fair Use', read_time: '7 min read', summary: 'Understanding legal and ethical considerations for content usage.' },
        { id: 'u8-l3', category: 'Media and Ethics', difficulty: 'Advanced', title: 'Privacy vs. Public Interest', read_time: '9 min read', summary: 'Balancing individual privacy rights with the public\'s right to know.' },
        { id: 'u8-l4', category: 'Media and Ethics', difficulty: 'Advanced', title: 'The Impact of Media on Society and Culture', read_time: '10 min read', summary: 'Broad societal effects of media representation and narratives.' },
        { id: 'u8-l5', category: 'Media and Ethics', difficulty: 'Advanced', title: 'Promoting Ethical Media Practices', read_time: '8 min read', summary: 'Advocating for and contributing to responsible media environments.' },

        // Unit 9: Creating Responsible Media
        { id: 'u9-l1', category: 'Creating Responsible Media', difficulty: 'Advanced', title: 'Principles of Ethical Content Creation', read_time: '7 min read', summary: 'Guidelines for producing honest, accurate, and fair media content.' },
        { id: 'u9-l2', category: 'Creating Responsible Media', difficulty: 'Advanced', title: 'Research and Fact-Checking for Content Creators', read_time: '9 min read', summary: 'Ensuring accuracy and reliability in self-produced media.' },
        { id: 'u9-l3', category: 'Creating Responsible Media', difficulty: 'Advanced', title: 'Citing Sources Properly', read_time: '6 min read', summary: 'Best practices for attributing information and avoiding plagiarism.' },
        { id: 'u9-l4', category: 'Creating Responsible Media', difficulty: 'Advanced', title: 'Understanding Your Audience and Message', read_time: '8 min read', summary: 'Tailoring content effectively while maintaining integrity.' },
        { id: 'u9-l5', category: 'Creating Responsible Media', difficulty: 'Advanced', title: 'Promoting Diverse Perspectives', read_time: '7 min read', summary: 'The importance of inclusivity and representation in media creation.' },

        // Unit 10: Media in a Global Context
        { id: 'u10-l1', category: 'Media in Global Context', difficulty: 'Advanced', title: 'International News and Global Perspectives', read_time: '8 min read', summary: 'Analyzing news from diverse international sources and viewpoints.' },
        { id: 'u10-l2', category: 'Media in Global Context', difficulty: 'Advanced', title: 'Understanding Cultural Differences in Media', read_time: '7 min read', summary: 'How cultural contexts shape media production and reception.' },
        { id: 'u10-l3', category: 'Media in Global Context', difficulty: 'Advanced', title: 'The Role of Media in International Relations', read_time: '9 min read', summary: 'Media\'s influence on diplomacy, conflict, and global understanding.' },
        { id: 'u10-l4', category: 'Media in Global Context', difficulty: 'Advanced', title: 'Addressing Global Misinformation Challenges', read_time: '10 min read', summary: 'Strategies for combating false narratives on an international scale.' },

        // Unit 11: The Future of Media
        { id: 'u11-l1', category: 'Future of Media', difficulty: 'Advanced', title: 'Emerging Media Technologies (AI, VR, AR)', read_time: '9 min read', summary: 'Exploring the impact of new technologies on media creation and consumption.' },
        { id: 'u11-l2', category: 'Future of Media', difficulty: 'Advanced', title: 'The Evolution of News Consumption', read_time: '8 min read', summary: 'Predicting changes in how individuals access and engage with news.' },
        { id: 'u11-l3', category: 'Future of Media', difficulty: 'Advanced', title: 'Challenges and Opportunities in the Digital Age', read_time: '10 min read', summary: 'Navigating the complexities and potentials of the modern media environment.' },
        { id: 'u11-l4', category: 'Future of Media', difficulty: 'Advanced', title: 'Lifelong Learning in Media Literacy', read_time: '7 min read', summary: 'The ongoing need for adaptation and continuous learning in media literacy.' }
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

    // Corrected addMessageToChat to use correct element IDs and classes
    // BOT_AVATAR_URL and USER_AVATAR_URL are now expected to be defined globally in learn.html
    // REMOVED: const BOT_AVATAR_URL = "{{ url_for('static', filename='img/robot.png') }}";
    // REMOVED: const USER_AVATAR_URL = "{{ url_for('static', filename='img/default_profile.jpeg') }}";

    function addMessageToChat(message, sender) {
        const messageWrapper = document.createElement('div');
        messageWrapper.classList.add('message-bubble', `${sender}-message`); // Use existing classes

        const avatar = document.createElement('img');
        avatar.classList.add('message-profile-pic'); // Use existing class
        // Ensure these global variables are accessible here
        avatar.src = sender === 'user' ? USER_AVATAR_URL : BOT_AVATAR_URL;
        avatar.alt = sender === 'user' ? 'User Avatar' : 'Bot Avatar';

        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message-content', `${sender}-content`); // Use existing classes
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
            renderLearningArticles(); // Render articles when this tab is shown
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

    // Knowledge Hub (Learn Articles) Rendering
    function createLearningArticleCard(article) {
        const card = document.createElement('div');
        card.classList.add('learn-article-card');
        card.addEventListener('click', () => {
            // For now, just log or show a message, as there's no full article page yet
            alert(`You clicked on: ${article.title}`);
            // window.location.href = `/article/${article.id}`; // Uncomment when article pages exist
        });

        const categoryClass = article.category ? article.category.toLowerCase().replace(/[\s-]/g, '') : 'general'; // Remove spaces and hyphens
        const difficultyClass = article.difficulty ? article.difficulty.toLowerCase().replace(/[\s-]/g, '') : 'beginner'; // Remove spaces and hyphens

        card.innerHTML = `
            <div class="tags-container">
                <span class="category-tag ${categoryClass}">${article.category}</span>
                <span class="difficulty-tag ${difficultyClass}">${article.difficulty}</span>
            </div>
            <h3>${article.title}</h3>
            <p class="read-time">${article.read_time}</p>
            <p class="summary">${article.summary}</p>
            <a href="#" class="read-article-link">
                Read Article <i class="fas fa-arrow-right"></i>
            </a>
        `;
        return card;
    }

    function renderLearningArticles() {
        // Added null checks for filters and grid
        if (!categoryFilter || !difficultyFilter || !learnArticlesGrid || !articlesCountDisplay) {
            console.error("Knowledge Hub filter or grid elements not found.");
            return;
        }

        const selectedCategory = categoryFilter.value;
        const selectedDifficulty = difficultyFilter.value;

        const filteredArticles = learningArticlesData.filter(article => {
            const articleCategoryNormalized = article.category.toLowerCase().replace(/[\s-]/g, '');
            const articleDifficultyNormalized = article.difficulty.toLowerCase().replace(/[\s-]/g, '');

            const matchesCategory = selectedCategory === 'all' || articleCategoryNormalized === selectedCategory.replace(/[\s-]/g, '');
            const matchesDifficulty = selectedDifficulty === 'all' || articleDifficultyNormalized === selectedDifficulty.replace(/[\s-]/g, '');
            return matchesCategory && matchesDifficulty;
        });

        learnArticlesGrid.innerHTML = ''; // Clear previous articles
        if (filteredArticles.length > 0) {
            filteredArticles.forEach(article => {
                learnArticlesGrid.appendChild(createLearningArticleCard(article));
            });
            articlesCountDisplay.textContent = `Showing ${filteredArticles.length} of ${learningArticlesData.length} articles`;
        } else {
            learnArticlesGrid.innerHTML = '<p class="info-message">No articles found matching your filters.</p>';
            articlesCountDisplay.textContent = `Showing 0 of ${learningArticlesData.length} articles`;
        }
    }

    if (categoryFilter) { // Added null check
        categoryFilter.addEventListener('change', renderLearningArticles);
    }
    if (difficultyFilter) { // Added null check
        difficultyFilter.addEventListener('change', renderLearningArticles);
    }

    // Initial load of articles when the page loads
    // Ensure the correct tab is shown on load
    showTab('chatbot'); // Default to chatbot tab on load
    renderLearningArticles(); // Render articles initially for Knowledge Hub
});