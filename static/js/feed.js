document.addEventListener('DOMContentLoaded', () => {
    const latestNewsGrid = document.getElementById('latest-news-grid');
    const generalMisconceptionsGrid = document.getElementById('general-misconceptions-grid');
    const importantIssuesGrid = document.getElementById('important-issues-grid');
    const refreshFeedBtn = document.getElementById('refresh-feed-btn');
    const loadingIndicator = refreshFeedBtn ? refreshFeedBtn.querySelector('.loading-indicator') : null;
    const refreshIcon = refreshFeedBtn ? refreshFeedBtn.querySelector('.refresh-icon') : null;
    const feedMessage = document.getElementById('feed-message');

    const SAVED_ARTICLES_KEY = 'debunkd_saved_articles'; // Key for localStorage

    // Helper to get API keys from session storage or default to empty string
    function getUserApiKeys() {
        const useOwnApiKey = localStorage.getItem('useOwnApiKey') === 'true';
        console.log("DEBUG: useOwnApiKey from localStorage:", useOwnApiKey);
        const newsApiKey = useOwnApiKey ? sessionStorage.getItem('userNewsApiKey') || '' : '';
        const geminiApiKey = useOwnApiKey ? sessionStorage.getItem('userGeminiApiKey') || '' : '';
        console.log("DEBUG: Retrieved NewsAPI Key (first 5 chars):", newsApiKey.substring(0, 5));
        console.log("DEBUG: Retrieved Gemini API Key (first 5 chars):", geminiApiKey.substring(0, 5));
        return { newsApiKey, geminiApiKey };
    }

    // Function to show messages below the refresh button
    function showFeedMessage(message, isError = false, duration = 5000) { // Added duration parameter
        if (feedMessage) {
            feedMessage.textContent = message;
            feedMessage.style.display = 'block';
            feedMessage.classList.remove('error-message', 'info-message');
            feedMessage.classList.add(isError ? 'error-message' : 'info-message');
            if (duration > 0) { // Only hide if duration is positive
                setTimeout(() => {
                    feedMessage.style.display = 'none';
                    feedMessage.textContent = '';
                }, duration);
            }
        }
    }

    // Helper to get saved articles from localStorage
    function getSavedArticles() {
        try {
            const saved = localStorage.getItem(SAVED_ARTICLES_KEY);
            const articlesMap = saved ? JSON.parse(saved) : {};
            return Object.values(articlesMap);
        } catch (e) {
            console.error("Error parsing saved articles from localStorage in home.js:", e);
            return [];
        }
    }

    // Helper to save an article to localStorage
    function saveArticle(article) {
        const savedArticles = getSavedArticlesMap(); // Use getSavedArticlesMap to modify map directly
        if (!savedArticles[article.id]) {
            savedArticles[article.id] = article;
            localStorage.setItem(SAVED_ARTICLES_KEY, JSON.stringify(savedArticles));
            // showFeedMessage(`'${article.title}' saved!`); // This message is now handled by article_detail.html
            return true;
        }
        return false;
    }

    // Helper to remove an article from localStorage
    function removeArticle(articleId) {
        const savedArticles = getSavedArticlesMap();
        if (savedArticles[articleId]) {
            delete savedArticles[articleId];
            localStorage.setItem(SAVED_ARTICLES_KEY, JSON.stringify(savedArticles));
            // showFeedMessage('Article removed from saved.'); // This message is now handled by article_detail.html
            return true;
        }
        return false;
    }

    // Helper to get saved articles as a map (needed for removal logic)
    function getSavedArticlesMap() {
        try {
            const saved = localStorage.getItem(SAVED_ARTICLES_KEY);
            return saved ? JSON.parse(saved) : {};
        } catch (e) {
            console.error("Error parsing saved articles map from localStorage:", e);
            return {};
        }
    }

    // Function to create an article card HTML element
    function createArticleCard(article) {
        const articleCard = document.createElement('div');
        articleCard.classList.add('article-card');
        articleCard.dataset.id = article.id; // Store article ID on the card

        // Determine category class and colors for styling
        let categoryText = article.category || 'General';
        let categoryKey = categoryText.toLowerCase().replace(' ', '-');
        const categoryColors = {
            'health': { bg: '#e8f5e9', text: '#2e7d32' },
            'environment': { bg: '#e3f2fd', text: '#1565c0' },
            'science': { bg: '#ffe0b2', text: '#e65100' },
            'technology': { bg: '#ede7f6', text: '#673ab7' },
            'business': { bg: '#fffde7', text: '#fbc02d' },
            'politics': { bg: '#ffebee', text: '#c62828' },
            'society': { bg: '#eeeeee', text: '#616161' },
            'education': { bg: '#e0f2f7', text: '#006064' },
            'general': { bg: '#f0f0f0', text: '#424242' },
            'events': { bg: '#fde0dc', text: '#d32f2f' }
        };
        const colors = categoryColors[categoryKey] || categoryColors['general'];

        const savedArticles = getSavedArticlesMap(); // Get the map to check if saved
        const isSaved = !!savedArticles[article.id]; // Convert to boolean

        articleCard.innerHTML = `
            <img src="${article.image_url || 'https://placehold.co/600x400/e0e0e0/555555?text=No+Image'}" alt="${article.title}" class="article-card-image" onerror="this.onerror=null;this.src='https://placehold.co/600x400/e0e0e0/555555?text=No+Image';">
            <div class="article-card-content">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="article-card-category-tag" style="background-color: ${colors.bg}; color: ${colors.text};">${categoryText}</span>
                    <i class="far fa-bookmark save-article-btn ${isSaved ? 'saved fas' : ''}" data-article-id="${article.id}"></i>
                </div>
                <h3>${article.title}</h3>
                <p>${article.summary}</p>
            </div>
        `;

        // Add event listener for the save button
        const saveBtn = articleCard.querySelector('.save-article-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', (event) => {
                event.stopPropagation(); // Prevent card click from triggering
                const articleId = saveBtn.dataset.articleId;
                if (saveBtn.classList.contains('saved')) {
                    removeArticle(articleId);
                    saveBtn.classList.remove('saved', 'fas');
                    saveBtn.classList.add('far'); // Change to outline icon
                    // showFeedMessage('Article removed from saved!', false, 2000); // Shorter duration
                } else {
                    saveArticle(article); // Pass the full article object
                    saveBtn.classList.add('saved', 'fas'); // Change to solid icon
                    saveBtn.classList.remove('far');
                    // showFeedMessage('Article saved!', false, 2000); // Shorter duration
                }
            });
        }

        // Add event listener for clicking the card (to view full article)
        articleCard.addEventListener('click', () => {
            window.location.href = `/article/${article.id}`;
        });

        return articleCard;
    }

    // Function to render articles into a grid
    function renderArticles(articles, gridElement) {
        gridElement.innerHTML = ''; // Clear existing articles
        if (articles && articles.length > 0) {
            console.log(`DEBUG: Rendering ${articles.length} articles into ${gridElement.id}`);
            articles.forEach(article => {
                gridElement.appendChild(createArticleCard(article));
            });
        } else {
            console.log(`DEBUG: No articles to render for ${gridElement.id}. Displaying message.`);
            gridElement.innerHTML = '<p class="info-message">No articles available in this section.</p>';
        }
    }

    // Function to fetch articles from the backend
    async function fetchArticles(section = null, refresh = false) {
        console.log(`DEBUG: fetchArticles called. Refresh: ${refresh}`);
        if (loadingIndicator) loadingIndicator.style.display = 'inline-block';
        if (refreshIcon) refreshIcon.style.display = 'none';
        if (refreshFeedBtn) refreshFeedBtn.disabled = true; // Disable button during fetch

        const { newsApiKey, geminiApiKey } = getUserApiKeys();

        // Check if API keys are available for the initial fetch
        if (!newsApiKey || !geminiApiKey) {
            console.warn("WARNING: API keys missing. Cannot fetch articles from backend.");
            showFeedMessage("Please enter your NewsAPI and Gemini API keys in Profile Settings to fetch articles.", true, 0); // Display indefinitely
            if (loadingIndicator) loadingIndicator.style.display = 'none';
            if (refreshIcon) refreshIcon.style.display = 'inline-block';
            if (refreshFeedBtn) refreshFeedBtn.disabled = false;
            return; // Stop execution if keys are missing
        } else {
            // Clear any previous persistent error message if keys are now present
            if (feedMessage && feedMessage.textContent.includes("API keys missing")) {
                feedMessage.style.display = 'none';
                feedMessage.textContent = '';
            }
        }

        try {
            const queryParams = new URLSearchParams();
            if (refresh) {
                queryParams.append('refresh', 'true');
            }

            console.log("DEBUG: Fetching from /api/get_feed_articles with keys...");
            const response = await fetch(`/api/get_feed_articles?${queryParams.toString()}`, {
                headers: {
                    'X-User-News-API-Key': newsApiKey,
                    'X-User-Gemini-API-Key': geminiApiKey
                }
            });

            const data = await response.json();
            console.log("DEBUG: API Response Data:", data);

            if (!response.ok) {
                if (response.status === 401 && data.error && data.error.includes("API keys not provided")) {
                    showFeedMessage("API keys are missing or invalid. Please update them in your profile settings.", true, 0); // Display indefinitely
                } else {
                    showFeedMessage(data.error || 'Failed to fetch articles. Please try again.', true);
                }
                return;
            }

            // Render articles for each section
            renderArticles(data.latest_news, latestNewsGrid);
            renderArticles(data.general_misconceptions, generalMisconceptionsGrid);
            renderArticles(data.important_issues, importantIssuesGrid);

            const allSectionsLoaded = data.latest_news.length > 0 &&
                                      data.general_misconceptions.length > 0 &&
                                      data.important_issues.length > 0;

            if (data.initial_generation_complete === false || !allSectionsLoaded) {
                showFeedMessage("Generating initial articles. Please wait a moment or refresh.", false, 5000);
            } else {
                showFeedMessage("Feed updated!", false, 3000);
            }

        } catch (error) {
            console.error('Error fetching feed articles:', error);
            showFeedMessage('An error occurred while fetching articles. Please check console.', true);
        } finally {
            if (loadingIndicator) loadingIndicator.style.display = 'none';
            if (refreshIcon) refreshIcon.style.display = 'inline-block';
            if (refreshFeedBtn) refreshFeedBtn.disabled = false;
        }
    }

    // Event listener for refresh button
    if (refreshFeedBtn) {
        refreshFeedBtn.addEventListener('click', () => fetchArticles(null, true));
    }

    // Event listeners for "More" links (if you still have them, they are not in your latest feed.html)
    document.querySelectorAll('.more-link').forEach(link => {
        link.addEventListener('click', async (event) => {
            event.preventDefault();
            const section = event.currentTarget.dataset.section;
            fetchArticles(section, true); // This will trigger a full refresh of all sections
        });
    });

    // Initial fetch when the page loads
    fetchArticles();
});