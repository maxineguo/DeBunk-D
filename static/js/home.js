document.addEventListener('DOMContentLoaded', () => {
    // Logic for loading saved articles from localStorage
    const savedArticlesList = document.getElementById('saved-articles-list');
    const savedArticles = JSON.parse(localStorage.getItem('savedArticles') || '[]');

    if (savedArticles.length > 0) {
        savedArticlesList.innerHTML = ''; // Clear default message
        savedArticles.forEach(article => {
            const articleCard = document.createElement('div');
            articleCard.classList.add('article-card');
            articleCard.innerHTML = `
                <h3>${article.title}</h3>
                <p>${article.summary}</p>
                `;
            savedArticlesList.appendChild(articleCard);
        });
    }

    // Logic for Learn Progress Bar
    const learnProgressBar = document.getElementById('learn-progress-bar');
    const learnProgressText = document.getElementById('learn-progress-text');

    // This is a placeholder calculation.
    // You'll need to define how you calculate "progress" based on
    // saved chatbot history length and quiz completion status from localStorage.
    const chatbotHistory = JSON.parse(localStorage.getItem('chatHistory') || '[]');
    const quizProgress = JSON.parse(localStorage.getItem('quizProgress') || '{}'); // e.g., {'quiz1': true, 'quiz2': false}

    // Example calculation: (Simplified for now)
    // Assume 1 quiz + some chatbot interaction for 100%
    const totalQuizzes = 2; // For your example articles
    let completedQuizzes = 0;
    for (const quizId in quizProgress) {
        if (quizProgress[quizId] === true) { // Assuming true means completed
            completedQuizzes++;
        }
    }
    const quizPercentage = (completedQuizzes / totalQuizzes) * 50; // Quizzes count for 50%
    const chatbotActivityScore = Math.min(chatbotHistory.length / 10, 1) * 50; // E.g., 10 messages = 50%

    const overallProgress = Math.round(quizPercentage + chatbotActivityScore); // Max 100%

    learnProgressBar.style.width = `${overallProgress}%`;
    learnProgressText.textContent = `Learn: ${overallProgress}% complete`;

    // Ensure there's a default profile image in static/img/
    // You can upload your own or use a placeholder icon.
    // For now, let's include a dummy image path.
    // (A default_profile.png is referenced in base.html)
});