document.addEventListener('DOMContentLoaded', () => {
    const savedArticlesGrid = document.getElementById('saved-articles-grid');
    const learnProgressBar = document.getElementById('learn-progress-bar');
    const learnProgressText = document.getElementById('learn-progress-text');

    // Function to create an article card HTML element (reused from feed.js concept)
    function createSavedArticleCard(article) {
        const articleCard = document.createElement('div');
        articleCard.classList.add('article-card');
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
            window.location.href = articlePageUrl;
        });
        return articleCard;
    }

    // Render saved articles
    function renderSavedArticles() {
        let savedArticles = JSON.parse(localStorage.getItem('savedArticles') || '[]');
        savedArticlesGrid.innerHTML = ''; // Clear previous content

        if (savedArticles.length > 0) {
            savedArticles.forEach(article => {
                savedArticlesGrid.appendChild(createSavedArticleCard(article));
            });
        } else {
            savedArticlesGrid.innerHTML = '<p class="info-message">No articles saved yet. Start saving from the <a href="/feed">Feed</a> or <a href="/search">Search</a> pages!</p>';
        }
    }

    // Update learn tab reading progress
    function updateLearnProgress() {
        // Placeholder: In a real app, this would come from user progress tracking
        // For now, let's simulate a progress
        const progressPercentage = 75; // Example: 75% complete
        learnProgressBar.style.width = `${progressPercentage}%`;
        learnProgressText.textContent = `${progressPercentage}% Complete`;
    }

    // Initial render on page load
    renderSavedArticles();
    updateLearnProgress();
});