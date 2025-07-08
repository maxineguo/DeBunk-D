document.addEventListener('DOMContentLoaded', () => {
    const refreshFeedBtn = document.getElementById('refresh-feed-btn');
    const articlesContainer = document.getElementById('articles-container');
    const loadingIndicator = document.getElementById('feed-loading-indicator');

    async function fetchFeedArticles() {
        loadingIndicator.style.display = 'inline-block';
        refreshFeedBtn.disabled = true;
        articlesContainer.innerHTML = '<p>Loading news articles...</p>'; // Clear previous content

        // Get user's API key from sessionStorage if 'useOwnApiKey' is true in localStorage
        const useOwnApiKey = localStorage.getItem('useOwnApiKey') === 'true';
        let headers = {};
        if (useOwnApiKey) {
            const userNewsApiKey = sessionStorage.getItem('userNewsApiKey');
            if (!userNewsApiKey) {
                // If user chose to use their own key but hasn't provided it for this session
                window.showApiKeyPopup(); // Show the popup
                loadingIndicator.style.display = 'none';
                refreshFeedBtn.disabled = false;
                articlesContainer.innerHTML = '<p class="error-message">Please enter your NewsAPI Key to fetch articles.</p>';
                return;
            }
            // Pass the user's key in a header for the backend to use
            // (Backend should expect this header, e.g., 'X-User-News-API-Key')
            headers['X-User-News-API-Key'] = userNewsApiKey;
        }

        try {
            const response = await fetch('/api/get_feed_articles', { headers: headers });
            if (!response.ok) {
                const errorData = await response.json();
                // Check for specific error codes related to API keys
                if (response.status === 401 && errorData.code === "apiKeyMissingOrInvalid") { // Example error code
                    window.showApiKeyPopup(); // Prompt user for key
                    articlesContainer.innerHTML = '<p class="error-message">Your API key is missing or invalid. Please enter it to fetch articles.</p>';
                } else {
                    throw new Error(`HTTP error! status: ${response.status} - ${errorData.message || response.statusText}`);
                }
            }
            const data = await response.json();

            articlesContainer.innerHTML = ''; // Clear "Loading..." message
            if (data.articles && data.articles.length > 0) {
                data.articles.forEach(article => {
                    const articleCard = document.createElement('div');
                    articleCard.classList.add('article-card');
                    articleCard.innerHTML = `
                        <h3>${article.title}</h3>
                        <p>${article.summary}</p>
                        <button class="btn secondary-btn save-article-btn" data-article='${JSON.stringify(article)}'>Save Article</button>
                    `;
                    articlesContainer.appendChild(articleCard);
                });
                // Add event listeners for save buttons
                document.querySelectorAll('.save-article-btn').forEach(button => {
                    button.addEventListener('click', (event) => {
                        const articleToSave = JSON.parse(event.target.dataset.article);
                        let savedArticles = JSON.parse(localStorage.getItem('savedArticles') || '[]');
                        // Prevent duplicates based on title/url
                        if (!savedArticles.some(a => a.title === articleToSave.title && a.url === articleToSave.url)) {
                            savedArticles.push(articleToSave);
                            localStorage.setItem('savedArticles', JSON.stringify(savedArticles));
                            alert('Article saved successfully!');
                        } else {
                            alert('Article already saved!');
                        }
                    });
                });
            } else {
                articlesContainer.innerHTML = '<p>No articles found. Try again later!</p>';
            }
        } catch (error) {
            console.error('Error fetching feed articles:', error);
            articlesContainer.innerHTML = `<p class="error-message">Failed to load articles: ${error.message}. Please try again.</p>`;
        } finally {
            loadingIndicator.style.display = 'none';
            refreshFeedBtn.disabled = false;
        }
    }

    if (refreshFeedBtn) {
        refreshFeedBtn.addEventListener('click', fetchFeedArticles);
    }

    // Initial load of articles when the page loads
    fetchFeedArticles();
});