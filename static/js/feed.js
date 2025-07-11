document.addEventListener('DOMContentLoaded', () => {
    const refreshFeedBtn = document.getElementById('refresh-feed-btn');
    const articlesContainer = document.getElementById('articles-container'); // This will now hold all sections
    const loadingIndicator = document.getElementById('feed-loading-indicator');

    // Function to create an article card HTML element
    function createArticleCard(article) {
        const articleCard = document.createElement('div');
        articleCard.classList.add('article-card');
        // Use article.url as a fallback if full_content.url is not available
        const articleUrl = article.url || (article.full_content ? article.full_content.url : '#');
        // Use article.image_url, or a generic placeholder if not available
        const imageUrl = article.image_url || `https://placehold.co/300x200/CCCCCC/333333?text=${article.category || 'Article'}`;

        articleCard.innerHTML = `
            <img src="${imageUrl}" alt="${article.title}" class="article-card-image" onerror="this.onerror=null;this.src='https://placehold.co/300x200/CCCCCC/333333?text=Image+Error';">
            <div class="article-card-content">
                <h3>${article.title}</h3>
                <p>${article.summary}</p>
                <div class="article-card-actions">
                    <a href="${articleUrl}" target="_blank" class="btn secondary-btn view-source-btn">View Source</a>
                    <button class="btn primary-btn save-article-btn" data-article='${JSON.stringify(article)}'>Save Article</button>
                </div>
            </div>
        `;
        return articleCard;
    }

    // Function to render a section of articles
    function renderArticleSection(container, title, articles) {
        const sectionDiv = document.createElement('div');
        sectionDiv.classList.add('feed-section');
        sectionDiv.innerHTML = `<h2>${title}</h2><div class="article-grid"></div>`;
        const articleGrid = sectionDiv.querySelector('.article-grid');

        if (articles && articles.length > 0) {
            // Display only the first 3 articles initially
            articles.slice(0, 3).forEach(article => {
                articleGrid.appendChild(createArticleCard(article));
            });

            // If there are more than 3 articles, add a "More" button
            if (articles.length > 3) {
                const moreButtonContainer = document.createElement('div');
                moreButtonContainer.classList.add('more-button-container');
                const moreButton = document.createElement('button');
                moreButton.classList.add('btn', 'secondary-btn', 'more-articles-btn');
                moreButton.textContent = 'Load More Articles';
                moreButton.dataset.startIndex = 3; // Start index for next batch
                moreButton.dataset.articlesData = JSON.stringify(articles); // Store all articles for later use

                moreButton.addEventListener('click', function() {
                    const startIndex = parseInt(this.dataset.startIndex);
                    const allArticles = JSON.parse(this.dataset.articlesData);
                    const nextBatch = allArticles.slice(startIndex, startIndex + 12); // Load next 12

                    nextBatch.forEach(article => {
                        articleGrid.appendChild(createArticleCard(article));
                    });

                    this.dataset.startIndex = startIndex + nextBatch.length;

                    if (parseInt(this.dataset.startIndex) >= allArticles.length) {
                        this.style.display = 'none'; // Hide button if no more articles
                    }
                });
                moreButtonContainer.appendChild(moreButton);
                sectionDiv.appendChild(moreButtonContainer);
            }

        } else {
            articleGrid.innerHTML = '<p>No articles found for this section.</p>';
        }
        container.appendChild(sectionDiv);
    }

    async function fetchFeedArticles() {
        loadingIndicator.style.display = 'inline-block';
        refreshFeedBtn.disabled = true;
        articlesContainer.innerHTML = '<p>Loading news articles...</p>'; // Clear previous content

        // Get user's API key from sessionStorage if 'useOwnApiKey' is true in localStorage
        const useOwnApiKey = localStorage.getItem('useOwnApiKey') === 'true';
        let headers = {};
        if (useOwnApiKey) {
            const userNewsApiKey = sessionStorage.getItem('userNewsApiKey');
            const userGeminiApiKey = sessionStorage.getItem('userGeminiApiKey'); // Get Gemini key too

            if (!userNewsApiKey || !userGeminiApiKey) {
                window.showApiKeyPopup(); // Show the popup
                loadingIndicator.style.display = 'none';
                refreshFeedBtn.disabled = false;
                articlesContainer.innerHTML = '<p class="error-message">Please enter both NewsAPI and Gemini API Keys to fetch articles.</p>';
                return;
            }
            // Pass the user's keys in headers for the backend to use
            headers['X-User-News-API-Key'] = userNewsApiKey;
            headers['X-User-Gemini-API-Key'] = userGeminiApiKey;
        }

        try {
            const response = await fetch('/api/get_feed_articles', { headers: headers });
            if (!response.ok) {
                const errorData = await response.json();
                // Check for specific error codes related to API keys
                if (response.status === 401) {
                    window.showApiKeyPopup(); // Prompt user for key
                    articlesContainer.innerHTML = '<p class="error-message">API keys are missing or invalid. Please enter them to fetch articles.</p>';
                } else {
                    throw new Error(`HTTP error! status: ${response.status} - ${errorData.message || response.statusText}`);
                }
            }
            const data = await response.json();

            articlesContainer.innerHTML = ''; // Clear "Loading..." message

            // Render each section
            renderArticleSection(articlesContainer, 'Latest News', data.latest_news);
            renderArticleSection(articlesContainer, 'General Misconceptions', data.general_misconceptions);
            renderArticleSection(articlesContainer, 'Important Issues', data.important_issues);

            // Add event listeners for save buttons (after all articles are rendered)
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