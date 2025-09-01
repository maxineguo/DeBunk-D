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

        const newsApiKey = useOwnApiKey ? sessionStorage.getItem('userNewsApiKey') || '' : '';
        const geminiApiKey = useOwnApiKey ? sessionStorage.getItem('userGeminiApiKey') || '' : '';

        return {
            'x-newsapi-key': newsApiKey,
            'x-gemini-api-key': geminiApiKey
        };
    }

    // Helper function to show a temporary message
    function showFeedMessage(message, isError = false, timeout = 3000) {
        if (feedMessage) {
            feedMessage.textContent = message;
            feedMessage.className = `info-message ${isError ? 'error-message' : 'success-message'}`;
            feedMessage.style.display = 'block';

            clearTimeout(window.feedMessageTimeout);
            window.feedMessageTimeout = setTimeout(() => {
                feedMessage.style.display = 'none';
            }, timeout);
        }
    }

    // Function to create an individual article card
    function createArticleCard(article) {
        if (!article || !article.id) {
            console.error("ERROR: Invalid article data received.", article);
            return null;
        }

        const articleCard = document.createElement('a');
        articleCard.href = `/article/${article.id}`;
        articleCard.classList.add('article-card');

        const categoryClass = article.category ? article.category.toLowerCase().replace(' ', '-') : 'general';

        const cardContent = `
            <div class="article-content">
                <span class="article-category-tag ${categoryClass}">${article.category || 'General'}</span>
                <h3 class="article-title">${article.title || 'No Title'}</h3>
                <p class="article-summary">${article.summary || 'No summary available.'}</p>
            </div>
        `;

        articleCard.innerHTML = cardContent;
        return articleCard;
    }

    // Function to render articles into a specified container
    function renderArticles(articles, gridElement) {
        if (!gridElement) {
            console.error("ERROR: Grid element is null or undefined. Cannot render articles.");
            return;
        }

        gridElement.innerHTML = ''; // Clear existing articles

        if (articles && articles.length > 0) {
            articles.forEach(article => {
                const articleCard = createArticleCard(article);
                if (articleCard) {
                    gridElement.appendChild(articleCard);
                }
            });
        } else {
            gridElement.innerHTML = '<p class="info-message">No articles available in this section yet. Please refresh or check back later.</p>';
        }
    }

    async function fetchArticles(section = null, isRefresh = false) {
        if (isRefresh && refreshFeedBtn) {
            refreshFeedBtn.disabled = true;
            if (loadingIndicator) loadingIndicator.style.display = 'block';
            if (refreshIcon) refreshIcon.style.display = 'none';
            showFeedMessage("Fetching new stories...", false, 99999);
        } else {
            showFeedMessage("Loading news articles...", false, 99999);
        }

        console.log("DEBUG: Attempting to fetch articles...");

        try {
            const url = `/api/get_feed_articles`;
            const headers = getUserApiKeys();
            const response = await fetch(url, { headers: headers });

            console.log("DEBUG: Fetch request complete. Response status:", response.status);

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
            }

            const data = await response.json();
            console.log("DEBUG: Data received from API:", data);

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

    // Initial fetch when the page loads
    fetchArticles();
});