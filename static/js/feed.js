document.addEventListener('DOMContentLoaded', () => {
    console.log('feed.js: DOMContentLoaded event fired.');

    const refreshFeedBtn = document.getElementById('refresh-feed-btn');
    const articlesContainer = document.getElementById('articles-container');
    const loadingIndicator = document.getElementById('feed-loading-indicator');

    console.log('feed.js: refreshFeedBtn found:', !!refreshFeedBtn);
    console.log('feed.js: articlesContainer found:', !!articlesContainer);
    console.log('feed.js: loadingIndicator found:', !!loadingIndicator);


    const INITIAL_DISPLAY_COUNT = 4; // Number of articles to show initially per section
    const MAX_DISPLAY_COUNT_ON_MORE = 12; // Max articles to show when "More" is clicked

    // Define category tag colors for consistent styling
    const categoryColors = {
        'health': { bg: '#e8f5e9', text: '#2e7d32' }, // Green
        'environment': { bg: '#e8f5e9', text: '#2e7d32' }, // Green
        'science': { bg: '#e3f2fd', text: '#1565c0' }, // Blue
        'technology': { bg: '#e3f2fd', text: '#1565c0' }, // Blue
        'business': { bg: '#ede7f6', text: '#673ab7' }, // Purple
        'politics': { bg: '#ffebee', text: '#c62828' }, // Red
        'society': { bg: '#eeeeee', text: '#616161' }, // Grey
        'education': { bg: '#eeeeee', text: '#616161' }, // Grey
        'general': { bg: '#eeeeee', text: '#616161' }, // Default Grey
        'fact-check': { bg: '#e3f2fd', text: '#1565c0' }, // Blue for Fact-Check
        'news-report': { bg: '#e3f2fd', text: '#1565c0' }, // Blue for News Report
        'error': { bg: '#ffebee', text: '#c62828' } // Red for Errors
    };

    // Function to create an article card HTML element
    function createArticleCard(article) {
        const articleCard = document.createElement('div');
        articleCard.classList.add('article-card');
        const articlePageUrl = `/article/${article.id}`;

        // Determine category class and colors for styling
        let categoryText = article.category || 'General';
        let categoryKey = categoryText.toLowerCase().replace(' ', '-');
        // Handle specific category names from backend if they don't directly map
        if (categoryKey === 'news-report') categoryKey = 'news-report';
        if (categoryKey === 'fact-check') categoryKey = 'fact-check';
        if (categoryKey === 'error') categoryKey = 'error';

        const colors = categoryColors[categoryKey] || categoryColors['general'];

        // Apply inline styles for tag colors
        const tagStyle = `background-color: ${colors.bg}; color: ${colors.text};`;

        articleCard.innerHTML = `
            <span class="article-card-category-tag ${categoryKey}" style="${tagStyle}">${categoryText}</span>
            <h3>${article.title}</h3>
            <p>${article.summary}</p>
        `;
        // Add click listener to the entire card
        articleCard.addEventListener('click', (event) => {
            window.location.href = articlePageUrl;
        });
        return articleCard;
    }

    // Function to render a section of articles
    function renderArticleSection(container, title, articles, sectionId) {
        console.log(`feed.js: Rendering section: ${title}. Articles received:`, articles.map(a => a.id + ' | ' + a.title));
        const sectionDiv = document.createElement('div');
        sectionDiv.classList.add('feed-section');

        const headerHtml = `
            <div class="page-header">
                <h1>${title}</h1>
                <a href="#" class="more-link" data-section-id="${sectionId}">More</a>
            </div>
        `;
        sectionDiv.innerHTML = headerHtml + `<div class="article-grid" id="${sectionId}-grid"></div>`;
        const articleGrid = sectionDiv.querySelector('.article-grid');
        const moreLink = sectionDiv.querySelector(`.more-link[data-section-id="${sectionId}"]`);

        if (articles && articles.length > 0) {
            // Display only the initial count (4 articles)
            console.log(`feed.js: Displaying initial ${INITIAL_DISPLAY_COUNT} articles for ${title}.`);
            articles.slice(0, INITIAL_DISPLAY_COUNT).forEach((article, index) => {
                console.log(`feed.js: Adding initial article ${index + 1}: ${article.id} - ${article.title}`);
                articleGrid.appendChild(createArticleCard(article));
            });

            // "More" button functionality
            if (moreLink) {
                if (articles.length > INITIAL_DISPLAY_COUNT) {
                    moreLink.style.display = 'inline-block'; // Ensure it's visible
                    moreLink.addEventListener('click', (event) => {
                        event.preventDefault(); // Prevent default link behavior
                        articleGrid.innerHTML = ''; // Clear current display

                        // Display up to MAX_DISPLAY_COUNT_ON_MORE articles
                        console.log(`feed.js: Displaying up to ${MAX_DISPLAY_COUNT_ON_MORE} articles for ${title} on 'More' click.`);
                        articles.slice(0, MAX_DISPLAY_COUNT_ON_MORE).forEach((article, index) => {
                            console.log(`feed.js: Adding 'More' article ${index + 1}: ${article.id} - ${article.title}`);
                            articleGrid.appendChild(createArticleCard(article));
                        });
                        // Hide the "More" link if all 12 are shown or if there are no more
                        if (articles.length <= MAX_DISPLAY_COUNT_ON_MORE) {
                            moreLink.style.display = 'none';
                        }
                    });
                } else {
                    moreLink.style.display = 'none'; // Hide if there are 4 or fewer articles
                }
            }

        } else {
            articleGrid.innerHTML = '<p class="info-message">No articles found for this section.</p>';
            if (moreLink) moreLink.style.display = 'none'; // Hide "More" if no articles
        }
        container.appendChild(sectionDiv);
    }

    async function fetchFeedArticles(isRefreshClick = false) {
        console.log('feed.js: fetchFeedArticles called. isRefreshClick:', isRefreshClick);

        let data = null; // Initialize data to null

        if (loadingIndicator) loadingIndicator.style.display = 'inline-block';
        if (refreshFeedBtn) refreshFeedBtn.disabled = true;
        if (articlesContainer) articlesContainer.innerHTML = '<p class="info-message">Loading news articles...</p>';

        const useOwnApiKey = localStorage.getItem('useOwnApiKey') === 'true';
        let headers = {};
        let urlParams = '';

        if (isRefreshClick) {
            urlParams = '?refresh=true';
        }

        if (useOwnApiKey) {
            const userNewsApiKey = sessionStorage.getItem('userNewsApiKey');
            const userGeminiApiKey = sessionStorage.getItem('userGeminiApiKey');

            if (!userNewsApiKey || !userGeminiApiKey) {
                console.warn('feed.js: API keys missing for user-provided mode. Showing popup.');
                window.showApiKeyPopup();
                if (loadingIndicator) loadingIndicator.style.display = 'none';
                if (refreshFeedBtn) refreshFeedBtn.disabled = false;
                if (articlesContainer) articlesContainer.innerHTML = '<p class="error-message">Please enter both NewsAPI and Gemini API Keys to fetch articles.</p>';
                return;
            }
            headers['X-User-News-API-Key'] = userNewsApiKey;
            headers['X-User-Gemini-API-Key'] = userGeminiApiKey;
            console.log('feed.js: Using user-provided API keys from session storage.');
        } else {
            console.log('feed.js: Using default API keys (from backend environment variables).');
        }

        try {
            console.log(`feed.js: Attempting to fetch /api/get_feed_articles${urlParams}...`);
            const response = await fetch(`/api/get_feed_articles${urlParams}`, { headers: headers });

            console.log('feed.js: Response status:', response.status);

            if (!response.ok) {
                let errorMessage = `HTTP error! status: ${response.status}`;
                try {
                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('application/json')) {
                        const errorData = await response.json();
                        errorMessage = errorData.message || errorData.detail || response.statusText || errorMessage;
                        console.error('feed.js: API response error data (JSON):', errorData);
                    } else {
                        const responseText = await response.text();
                        errorMessage = responseText || response.statusText || errorMessage;
                        console.error('feed.js: API response error data (Text):', responseText);
                    }

                    if (response.status === 401) {
                        window.showApiKeyPopup();
                        if (articlesContainer) articlesContainer.innerHTML = '<p class="error-message">API keys are missing or invalid. Please enter them to fetch articles.</p>';
                    } else if (response.status === 403) {
                         if (articlesContainer) articlesContainer.innerHTML = `<p class="error-message">Access Forbidden: Your API keys might be invalid or lack necessary permissions. Please verify them in your settings.</p>`;
                    } else {
                        if (articlesContainer) articlesContainer.innerHTML = `<p class="error-message">Failed to load articles: ${errorMessage}. Please try again.</p>`;
                    }
                } catch (parseError) {
                    console.error('feed.js: Error processing non-OK response body:', parseError);
                    if (articlesContainer) articlesContainer.innerHTML = `<p class="error-message">Failed to load articles (Error: ${response.status} - ${response.statusText}). Please check console for details.</p>`;
                }
                return;
            }

            data = await response.json();
            console.log('feed.js: API data received:', data);

            // --- Polling Logic ---
            // If initial generation is NOT complete, set a timeout to poll again
            if (data && !data.initial_generation_complete) {
                console.log('feed.js: Initial generation not complete. Polling again in 2 seconds...');
                setTimeout(() => fetchFeedArticles(isRefreshClick), 2000);
                return; // IMPORTANT: Exit here to prevent rendering incomplete data
            }
            // --- End Polling Logic ---

            // If initial generation IS complete, proceed to render
            if (articlesContainer) articlesContainer.innerHTML = ''; // Clear "Loading..." message

            renderArticleSection(articlesContainer, 'Latest News', data.latest_news, 'latest-news');
            renderArticleSection(articlesContainer, 'General Misconceptions', data.general_misconceptions, 'misconceptions');
            renderArticleSection(articlesContainer, 'Important Issues', data.important_issues, 'issues');

        } catch (error) {
            console.error('feed.js: Error fetching feed articles (general catch):', error);
            if (articlesContainer) articlesContainer.innerHTML = `<p class="error-message">Failed to load articles: ${error.message}. Please try again.</p>`;
        } finally {
            // Only hide loading indicator and enable button if initial generation IS complete
            // OR if there was an error that prevented data from being received at all.
            // If data is null (meaning fetch failed or parsing failed), we can hide loading.
            // If data exists, but initial_generation_complete is false, the polling timeout handles it.
            if (loadingIndicator) loadingIndicator.style.display = 'none';
            if (refreshFeedBtn) refreshFeedBtn.disabled = false;
            console.log('feed.js: fetchFeedArticles finished.');
        }
    }

    if (refreshFeedBtn) {
        refreshFeedBtn.addEventListener('click', () => fetchFeedArticles(true));
    }

    fetchFeedArticles(false);
});