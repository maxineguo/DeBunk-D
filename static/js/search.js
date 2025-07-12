document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const searchResultsContainer = document.getElementById('search-results-container');
    const loadingIndicator = document.getElementById('search-loading-indicator');

    function createSearchResultCard(article) {
        const articleCard = document.createElement('div');
        articleCard.classList.add('article-card'); // Re-using feed article card styles
        const articlePageUrl = `/article/${article.id}`;

        // Determine category class for styling
        // For search results, category might be 'News' or 'General' (Fact-Check)
        let categoryText = article.category || 'General';
        let categoryClass = categoryText.toLowerCase().replace(' ', '-');
        if (categoryText === 'News Report') categoryClass = 'news'; // Specific class for news search
        if (categoryText === 'Fact-Check') categoryClass = 'fact-check'; // Specific class for general search

        articleCard.innerHTML = `
            <span class="article-card-category-tag ${categoryClass}">${categoryText}</span>
            <h3>${article.title}</h3>
            <p>${article.summary}</p>
        `;
        // Add click listener to the entire card
        articleCard.addEventListener('click', (event) => {
            window.location.href = articlePageUrl;
        });
        return articleCard;
    }

    async function performSearch() {
        const query = searchInput.value.trim();
        if (!query) {
            searchResultsContainer.innerHTML = '<p class="info-message">Please enter a search query.</p>';
            return;
        }

        loadingIndicator.style.display = 'inline-block';
        searchButton.disabled = true;
        searchResultsContainer.innerHTML = ''; // Clear previous results

        const useOwnApiKey = localStorage.getItem('useOwnApiKey') === 'true';
        let headers = {};
        if (useOwnApiKey) {
            const userNewsApiKey = sessionStorage.getItem('userNewsApiKey');
            const userGeminiApiKey = sessionStorage.getItem('userGeminiApiKey');

            if (!userNewsApiKey || !userGeminiApiKey) {
                window.showApiKeyPopup();
                loadingIndicator.style.display = 'none';
                searchButton.disabled = false;
                searchResultsContainer.innerHTML = '<p class="error-message">Please enter both NewsAPI and Gemini API Keys to perform searches.</p>';
                return;
            }
            headers['X-User-News-API-Key'] = userNewsApiKey;
            headers['X-User-Gemini-API-Key'] = userGeminiApiKey;
        }

        try {
            const response = await fetch(`/api/search_articles?query=${encodeURIComponent(query)}`, { headers: headers });
            if (!response.ok) {
                const errorData = await response.json();
                if (response.status === 401) {
                    window.showApiKeyPopup();
                    searchResultsContainer.innerHTML = '<p class="error-message">API keys are missing or invalid. Please enter them to perform searches.</p>';
                } else {
                    throw new Error(`HTTP error! status: ${response.status} - ${errorData.message || response.statusText}`);
                }
            }
            const data = await response.json();

            if (data.results && data.results.length > 0) {
                const article = data.results[0]; // Expecting one main result for search
                const searchResultSection = document.createElement('div');
                searchResultSection.classList.add('feed-section'); // Re-using styling for sections
                searchResultSection.innerHTML = `
                    <div class="page-header">
                        <h1>Search Result for "${query}"</h1>
                    </div>
                    <div class="article-grid" id="search-result-grid"></div>
                `;
                const articleGrid = searchResultSection.querySelector('.article-grid');
                articleGrid.appendChild(createSearchResultCard(article));
                searchResultsContainer.appendChild(searchResultSection);

            } else {
                searchResultsContainer.innerHTML = '<p class="info-message">No results found for your query. Try a different search term.</p>';
            }
        } catch (error) {
            console.error('Error during search:', error);
            searchResultsContainer.innerHTML = `<p class="error-message">Failed to perform search: ${error.message}. Please try again.</p>`;
        } finally {
            loadingIndicator.style.display = 'none';
            searchButton.disabled = false;
        }
    }

    searchButton.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            performSearch();
        }
    });
});