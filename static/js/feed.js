document.addEventListener('DOMContentLoaded', () => {
    const refreshFeedBtn = document.getElementById('refresh-feed-btn');
    const articlesContainer = document.getElementById('articles-container');
    const loadingIndicator = document.getElementById('feed-loading-indicator');

    const INITIAL_DISPLAY_COUNT = 4; // Number of articles to show initially per section

    // Function to create an article card HTML element
    function createArticleCard(article) {
        const articleCard = document.createElement('div');
        articleCard.classList.add('article-card');
        // Use the new `id` for the URL
        const articlePageUrl = `/article/${article.id}`;

        // Determine category class for styling
        const categoryClass = article.category ? article.category.toLowerCase().replace(' ', '-') : 'general';

        articleCard.innerHTML = `
            <span class="article-card-category-tag ${categoryClass}">${article.category || 'General'}</span>
            <h3>${article.title}</h3>
            <p>${article.summary}</p>
        `;
        // Add click listener to the entire card
        articleCard.addEventListener('click', (event) => {
            // Navigate to the full article page
            window.location.href = articlePageUrl;
        });
        return articleCard;
    }

    // Function to render a section of articles
    function renderArticleSection(container, title, articles, sectionId) {
        const sectionDiv = document.createElement('div');
        sectionDiv.classList.add('feed-section');

        const headerHtml = `
            <div class="page-header">
                <h1>${title}</h1>
                ${articles.length > INITIAL_DISPLAY_COUNT ? `<a href="#" class="more-link" data-section-id="${sectionId}">More <i class="fas fa-arrow-right"></i></a>` : ''}
            </div>
        `;
        sectionDiv.innerHTML = headerHtml + `<div class="article-grid" id="${sectionId}-grid"></div>`;
        const articleGrid = sectionDiv.querySelector('.article-grid');

        if (articles && articles.length > 0) {
            // Display only the initial count
            articles.slice(0, INITIAL_DISPLAY_COUNT).forEach(article => {
                articleGrid.appendChild(createArticleCard(article));
            });

            // If there are more articles than initial display, add click handler to "More" link
            if (articles.length > INITIAL_DISPLAY_COUNT) {
                const moreLink = sectionDiv.querySelector(`.more-link[data-section-id="${sectionId}"]`);
                if (moreLink) {
                    moreLink.addEventListener('click', (event) => {
                        event.preventDefault(); // Prevent default link behavior
                        articleGrid.innerHTML = ''; // Clear current display
                        articles.forEach(article => {
                            articleGrid.appendChild(createArticleCard(article));
                        });
                        moreLink.style.display = 'none'; // Hide link after showing all
                    });
                }
            }

        } else {
            articleGrid.innerHTML = '<p class="info-message">No articles found for this section.</p>';
        }
        container.appendChild(sectionDiv);
    }

    async function fetchFeedArticles() {
        loadingIndicator.style.display = 'inline-block';
        refreshFeedBtn.disabled = true;
        articlesContainer.innerHTML = '<p class="info-message">Loading news articles...</p>'; // Use info-message class

        const useOwnApiKey = localStorage.getItem('useOwnApiKey') === 'true';
        let headers = {};
        if (useOwnApiKey) {
            const userNewsApiKey = sessionStorage.getItem('userNewsApiKey');
            const userGeminiApiKey = sessionStorage.getItem('userGeminiApiKey');

            if (!userNewsApiKey || !userGeminiApiKey) {
                window.showApiKeyPopup();
                loadingIndicator.style.display = 'none';
                refreshFeedBtn.disabled = false;
                articlesContainer.innerHTML = '<p class="error-message">Please enter both NewsAPI and Gemini API Keys to fetch articles.</p>';
                return;
            }
            headers['X-User-News-API-Key'] = userNewsApiKey;
            headers['X-User-Gemini-API-Key'] = userGeminiApiKey;
        }

        try {
            const response = await fetch('/api/get_feed_articles', { headers: headers });
            if (!response.ok) {
                const errorData = await response.json();
                if (response.status === 401) {
                    window.showApiKeyPopup();
                    articlesContainer.innerHTML = '<p class="error-message">API keys are missing or invalid. Please enter them to fetch articles.</p>';
                } else {
                    throw new Error(`HTTP error! status: ${response.status} - ${errorData.message || response.statusText}`);
                }
            }
            const data = await response.json();

            articlesContainer.innerHTML = ''; // Clear "Loading..." message

            renderArticleSection(articlesContainer, 'Latest News', data.latest_news, 'latest-news');
            renderArticleSection(articlesContainer, 'General Misconceptions', data.general_misconceptions, 'misconceptions');
            renderArticleSection(articlesContainer, 'Important Issues', data.important_issues, 'issues');

            // No save buttons on feed cards in mockup, so this listener might be removed or moved to full article page
            // For now, keeping it as a functional fallback if you still want it.
            document.querySelectorAll('.save-article-btn').forEach(button => {
                button.addEventListener('click', (event) => {
                    event.stopPropagation(); // Prevent card click from firing
                    const articleToSave = JSON.parse(event.target.dataset.article);
                    let savedArticles = JSON.parse(localStorage.getItem('savedArticles') || '[]');
                    if (!savedArticles.some(a => a.id === articleToSave.id)) {
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

    fetchFeedArticles();
});