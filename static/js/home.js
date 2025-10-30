document.addEventListener('DOMContentLoaded', () => {
    const savedArticlesGrid = document.getElementById('saved-articles-grid');
    const noArticlesMessage = document.getElementById('no-articles-message');
    const viewAllSavedBtn = document.getElementById('view-all-saved-btn');
    const learningProgressFill = document.getElementById('learning-progress-fill');
    const learningProgressPercentage = document.getElementById('learning-progress-percentage');

    const MAX_DISPLAY_SAVED_ARTICLES = 4; // Max articles to display on home page
    const SAVED_ARTICLES_KEY = 'debunkd_saved_articles'; // Key for localStorage

    // Helper to get saved articles from localStorage
    function getSavedArticles() {
        try {
            const saved = localStorage.getItem(SAVED_ARTICLES_KEY);
            // Parse as an object, then convert to an array of articles
            const articlesMap = saved ? JSON.parse(saved) : {};
            return Object.values(articlesMap); // Return an array of article objects
        } catch (e) {
            console.error("Error parsing saved articles from localStorage in home.js:", e);
            return [];
        }
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

    // Function to create an article card HTML element (reused from feed.js concept)
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

        // For saved articles, we assume they are 'saved'
        // We will add a remove button instead of a save button
        articleCard.innerHTML = `
            <img src="${article.image_url || 'https://placehold.co/600x400/e0e0e0/555555?text=No+Image'}" alt="${article.title}" class="article-card-image" onerror="this.onerror=null;this.src='https://placehold.co/600x400/e0e0e0/555555?text=No+Image';">
            <div class="article-card-content">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="article-card-category-tag" style="background-color: ${colors.bg}; color: ${colors.text};">${categoryText}</span>
                    <i class="fas fa-bookmark save-article-btn saved" data-article-id="${article.id}"></i> {# Always show as saved, acts as remove #}
                </div>
                <h3>${article.title}</h3>
                <p>${article.summary}</p>
                {# NEW: Conditionally render Key Insights, Viewpoints, Sources if they exist #}
                ${article.key_insights && article.key_insights.length > 0 ? `
                    <h4 class="card-section-title">Key Insights:</h4>
                    <ul class="card-list">
                        ${article.key_insights.map(insight => `<li>${insight}</li>`).join('')}
                    </ul>
                ` : ''}
                ${article.viewpoints && article.viewpoints.length > 0 ? `
                    <h4 class="card-section-title">Viewpoints:</h4>
                    <ul class="card-list">
                        ${article.viewpoints.map(viewpoint => `<li>${viewpoint}</li>`).join('')}
                    </ul>
                ` : ''}
                ${article.sources && article.sources.length > 0 ? `
                    <h4 class="card-section-title">Sources:</h4>
                    <div class="card-sources">
                        ${article.sources.map(source => `<a href="${source.url}" target="_blank" rel="noopener noreferrer">${source.name}</a>`).join(', ')}
                    </div>
                ` : ''}
            </div>
        `;

        // Add event listener for the save button (which acts as a remove button here)
        const saveBtn = articleCard.querySelector('.save-article-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', (event) => {
                event.stopPropagation(); // Prevent card click from triggering
                const articleId = saveBtn.dataset.articleId;
                const savedArticlesMap = getSavedArticlesMap();
                if (savedArticlesMap[articleId]) {
                    delete savedArticlesMap[articleId];
                    localStorage.setItem(SAVED_ARTICLES_KEY, JSON.stringify(savedArticlesMap));
                    renderSavedArticles(); // Re-render the grid after removal
                    // Optionally, show a message
                    // alert('Article removed from saved.');
                }
            });
        }

        // Add event listener for clicking the card (to view full article)
        articleCard.addEventListener('click', () => {
            window.location.href = `/article/${article.id}`;
        });

        return articleCard;
    }

    // Function to render saved articles on the home page
    function renderSavedArticles() {
        const savedArticles = getSavedArticles(); // Get array of articles
        savedArticlesGrid.innerHTML = ''; // Clear existing articles

        if (savedArticles.length === 0) {
            noArticlesMessage.style.display = 'block'; // Show "No articles saved" card
            savedArticlesGrid.style.display = 'none'; // Hide grid
            viewAllSavedBtn.style.display = 'none'; // Hide "View All Saved" button
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
    // Function to calculate and display learning progress
    function updateLearningProgress() {
        const progressData = JSON.parse(localStorage.getItem('debunkd_quick_check_progress') || '{}');
        const totalData = JSON.parse(localStorage.getItem('debunkd_quick_check_totals') || '{}');

        let answered = 0;
        let total = 0;

        // Calculate total answered and total questions
        for (const lessonId in totalData) {
            total += totalData[lessonId] || 0;
            answered += progressData[lessonId] || 0;
        }

        // Avoid division by zero
        const percentage = total > 0 ? Math.min(Math.round((answered / total) * 100), 100) : 0;

        // Update bar visuals
        learningProgressFill.style.width = `${percentage}%`;
        learningProgressPercentage.textContent = `${percentage}%`;

        // Update message dynamically
        const message = document.querySelector('.encouraging-message');
        if (message) {
            if (percentage === 0) {
                message.textContent = "Let's get started! Try your first Quick Check.";
            } else if (percentage < 50) {
                message.textContent = "Nice work! Keep answering Quick Checks to boost your score.";
            } else if (percentage < 100) {
                message.textContent = "You're doing great! You're over halfway there!";
            } else {
                message.textContent = "Amazing! You've completed all Quick Checks!";
            }
        }
    }

    function updateLearningProgress() {
        const progressData = JSON.parse(localStorage.getItem('debunkd_quick_check_progress') || '{}');
        const totalData = JSON.parse(localStorage.getItem('debunkd_quick_check_totals') || '{}');

        let answered = 0;
        let total = 0;

        for (const lessonId in totalData) {
            total += totalData[lessonId] || 0;
            answered += progressData[lessonId] || 0;
        }

        const percentage = total > 0 ? Math.min(Math.round((answered / total) * 100), 100) : 0;

        learningProgressFill.style.width = `${percentage}%`;
        learningProgressPercentage.textContent = `${percentage}%`;

        const message = document.querySelector('.encouraging-message');
        if (message) {
            if (percentage === 0) {
                message.textContent = "Let's get started! Try your first Quick Check.";
            } else if (percentage < 50) {
                message.textContent = "Nice work! Keep answering Quick Checks to boost your score.";
            } else if (percentage < 100) {
                message.textContent = "You're doing great! You're over halfway there!";
            } else {
                message.textContent = "Amazing! You've completed all Quick Checks!";
            }
        }
    }


    // Initial render on page load
    renderSavedArticles();
    updateLearningProgress();
});