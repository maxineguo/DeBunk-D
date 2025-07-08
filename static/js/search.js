document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');
    const searchResultsContainer = document.getElementById('search-results-container');

    async function performSearch() {
        const query = searchInput.value.trim();
        if (!query) {
            searchResultsContainer.innerHTML = '<p class="error-message">Please enter a search query.</p>';
            return;
        }

        searchResultsContainer.innerHTML = '<p>Searching...</p>';

        // Get user's API key from sessionStorage if 'useOwnApiKey' is true in localStorage
        const useOwnApiKey = localStorage.getItem('useOwnApiKey') === 'true';
        let headers = {};
        if (useOwnApiKey) {
            const userNewsApiKey = sessionStorage.getItem('userNewsApiKey');
            if (!userNewsApiKey) {
                window.showApiKeyPopup(); // Show the popup
                searchResultsContainer.innerHTML = '<p class="error-message">Please enter your NewsAPI Key to perform a search.</p>';
                return;
            }
            headers['X-User-News-API-Key'] = userNewsApiKey;
        }

        try {
            const response = await fetch('/api/search_articles?query=' + encodeURIComponent(query), {
                method: 'GET', // Or POST if your backend expects JSON in body
                headers: headers
            });

            if (!response.ok) {
                const errorData = await response.json();
                if (response.status === 401 && errorData.code === "apiKeyMissingOrInvalid") { // Example error code
                    window.showApiKeyPopup(); // Prompt user for key
                    searchResultsContainer.innerHTML = '<p class="error-message">Your API key is missing or invalid. Please enter it to search.</p>';
                } else {
                    throw new Error(`HTTP error! status: ${response.status} - ${errorData.message || response.statusText}`);
                }
            }

            const data = await response.json();

            searchResultsContainer.innerHTML = ''; // Clear "Searching..." message

            if (data.results && data.results.length > 0) {
                // Assuming data.results[0] is the main processed article for simplicity
                const article = data.results[0]; // Your backend should return the structured data
                searchResultsContainer.innerHTML = `
                    <div class="page-section article-detail">
                        <h3>${article.title || 'No Title'}</h3>
                        <p><strong>Source:</strong> ${article.source || 'N/A'}</p>
                        <p><strong>URL:</strong> <a href="${article.url}" target="_blank">${article.url || 'N/A'}</a></p>

                        <h4>Summary:</h4>
                        <p>${article.summary || 'No summary available.'}</p>

                        <h4>Key Findings:</h4>
                        <ul>
                            ${article.key_findings ? article.key_findings.map(item => `<li>${item}</li>`).join('') : '<li>No key findings.</li>'}
                        </ul>

                        <h4>Multiple Perspectives:</h4>
                        <ul>
                            ${article.multiple_perspectives ? article.multiple_perspectives.map(item => `<li>${item}</li>`).join('') : '<li>No multiple perspectives.</li>'}
                        </ul>

                        <h4>Verified Sources:</h4>
                        <ul>
                            ${article.verified_sources ? article.verified_sources.map(item => `<li><a href="${item.url}" target="_blank">${item.name}</a></li>`).join('') : '<li>No verified sources.</li>'}
                        </ul>

                        <button class="btn primary-btn save-article-btn" data-article='${JSON.stringify(article)}'>Save Article</button>
                    </div>
                `;
                 // Add event listener for save button
                 document.querySelectorAll('.save-article-btn').forEach(button => {
                    button.addEventListener('click', (event) => {
                        const articleToSave = JSON.parse(event.target.dataset.article);
                        let savedArticles = JSON.parse(localStorage.getItem('savedArticles') || '[]');
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
                searchResultsContainer.innerHTML = '<p>No results found for your query. Try a different search!</p>';
            }
        } catch (error) {
            console.error('Error performing search:', error);
            searchResultsContainer.innerHTML = `<p class="error-message">Failed to perform search: ${error.message}. Please try again.</p>`;
        }
    }

    if (searchBtn) {
        searchBtn.addEventListener('click', performSearch);
    }
    if (searchInput) {
        searchInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                performSearch();
            }
        });
    }
});