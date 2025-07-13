document.addEventListener('DOMContentLoaded', () => {
    const savedArticlesGrid = document.getElementById('saved-articles-grid');
    const noArticlesMessage = document.getElementById('no-articles-message');
    const viewAllSavedBtn = document.getElementById('view-all-saved-btn');
    const learningProgressFill = document.getElementById('learning-progress-fill');
    const learningProgressPercentage = document.getElementById('learning-progress-percentage');

    const MAX_DISPLAY_SAVED_ARTICLES = 4; // Max articles to display on home page

    // Function to create an article card HTML element (reused from feed.js concept)
    function createArticleCard(article) {
        const articleCard = document.createElement('div');
        articleCard.classList.add('article-card');
        // For saved articles, we don't necessarily need a detailed article page yet,
        // but if you implement one, the ID would be useful. For now, a placeholder.
        const articlePageUrl = article.url || '#'; // Use original URL or placeholder

        // Determine category class and colors for styling (can be simplified if only a few categories are expected for saved)
        let categoryText = article.category || 'General';
        let categoryKey = categoryText.toLowerCase().replace(' ', '-');
        
        // Simplified category colors for saved articles if needed, or reuse from feed.js logic
        const categoryColors = {
            'health': { bg: '#e8f5e9', text: '#2e7d32' },
            'environment': { bg: '#e8f5e9', text: '#2e7d32' },
            'science': { bg: '#e3f2fd', text: '#1565c0' },
            'technology': { bg: '#e3f2fd', text: '#1565c0' },
            'business': { bg: '#ede7f6', text: '#673ab7' },
            'politics': { bg: '#ffebee', text: '#c62828' },
            'society': { bg: '#eeeeee', text: '#616161' },
            'education': { bg: '#eeeeee', text: '#616161' },
            'general': { bg: '#eeeeee', text: '#616161' },
            'fact-check': { bg: '#e3f2fd', text: '#1565c0' },
            'news-report': { bg: '#e3f2fd', text: '#1565c0' },
            'error': { bg: '#ffebee', text: '#c62828' }
        };
        const colors = categoryColors[categoryKey] || categoryColors['general'];
        const tagStyle = `background-color: ${colors.bg}; color: ${colors.text};`;


        articleCard.innerHTML = `
            <span class="article-card-category-tag ${categoryKey}" style="${tagStyle}">${categoryText}</span>
            <h3>${article.title}</h3>
            <p>${article.summary}</p>
        `;
        // Add click listener if you want saved articles to be clickable to a detail page
        articleCard.addEventListener('click', () => {
            // This would navigate to a full article view if you implement it for saved articles
            // For now, it might just link to the original source if 'article.url' is present
            if (article.url && article.url !== '#') {
                window.open(article.url, '_blank');
            }
        });
        return articleCard;
    }

    // Function to render saved articles
    function renderSavedArticles() {
        savedArticlesGrid.innerHTML = ''; // Clear previous content
        const savedArticles = JSON.parse(localStorage.getItem('savedArticles') || '[]');

        if (savedArticles.length === 0) {
            noArticlesMessage.style.display = 'flex'; // Show "No articles saved" card
            savedArticlesGrid.style.display = 'none'; // Hide grid
            viewAllSavedBtn.style.display = 'none'; // Hide button
        } else {
            noArticlesMessage.style.display = 'none'; // Hide "No articles saved" card
            savedArticlesGrid.style.display = 'grid'; // Show grid

            // Display up to MAX_DISPLAY_SAVED_ARTICLES
            savedArticles.slice(0, MAX_DISPLAY_SAVED_ARTICLES).forEach(article => {
                savedArticlesGrid.appendChild(createArticleCard(article));
            });

            // Show "View All Saved" button if there are more articles than displayed
            if (savedArticles.length > MAX_DISPLAY_SAVED_ARTICLES) {
                viewAllSavedBtn.style.display = 'inline-block';
            } else {
                viewAllSavedBtn.style.display = 'none';
            }
        }
    }

    // Function to update learning progress bar (random for now)
    function updateLearningProgress() {
        const randomProgress = Math.floor(Math.random() * 101); // Random number between 0 and 100
        learningProgressFill.style.width = `${randomProgress}%`;
        learningProgressPercentage.textContent = `${randomProgress}%`;
    }

    // Event listener for "View All Saved" button (for future implementation)
    if (viewAllSavedBtn) {
        viewAllSavedBtn.addEventListener('click', (event) => {
            event.preventDefault();
            // TODO: Implement navigation to a page showing all saved articles
            alert('View All Saved Articles functionality coming soon!');
        });
    }

    // Initial render on page load
    renderSavedArticles();
    updateLearningProgress();
});