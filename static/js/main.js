document.addEventListener('DOMContentLoaded', () => {
    // --- Theme Switching Logic ---
    const body = document.body;
    const lightThemeRadio = document.getElementById('light-theme-radio');
    const darkThemeRadio = document.getElementById('dark-theme-radio');

    // Function to apply theme
    function applyTheme(theme) {
        if (theme === 'dark') {
            body.classList.add('dark-theme');
            body.classList.remove('light-theme');
            darkThemeRadio.checked = true;
        } else {
            body.classList.add('light-theme');
            body.classList.remove('dark-theme');
            lightThemeRadio.checked = true;
        }
        localStorage.setItem('theme', theme); // Save preference
    }

    // Load theme from localStorage on page load
    const savedTheme = localStorage.getItem('theme') || 'light'; // Default to light
    applyTheme(savedTheme);

    // Event listeners for theme radio buttons
    if (lightThemeRadio) {
        lightThemeRadio.addEventListener('change', () => applyTheme('light'));
    }
    if (darkThemeRadio) {
        darkThemeRadio.addEventListener('change', () => applyTheme('dark'));
    }

    // --- Profile Modal Logic ---
    const profileIcon = document.getElementById('profile-icon');
    const profileModal = document.getElementById('profile-modal');
    const profileCloseBtn = document.getElementById('profile-close-btn');

    if (profileIcon) {
        profileIcon.addEventListener('click', () => {
            profileModal.style.display = 'flex'; // Use flex to center
            // Load current API key settings here if they were previously saved in session/local storage
            const useOwnApiKeyToggle = document.getElementById('use-own-api-key-toggle');
            const newsApiKeyInputContainer = document.getElementById('news-api-key-input-container');
            const newsApiKeyInput = document.getElementById('news-api-key-input');

            const useOwnKey = localStorage.getItem('useOwnApiKey') === 'true';
            useOwnApiKeyToggle.checked = useOwnKey;
            newsApiKeyInputContainer.style.display = useOwnKey ? 'block' : 'none';

            if (useOwnKey) {
                const ephemeralApiKey = sessionStorage.getItem('userNewsApiKey');
                if (ephemeralApiKey) {
                    newsApiKeyInput.value = ephemeralApiKey;
                }
            }
        });
    }

    if (profileCloseBtn) {
        profileCloseBtn.addEventListener('click', () => {
            profileModal.style.display = 'none';
        });
    }

    // Close modal if clicking outside
    window.addEventListener('click', (event) => {
        if (event.target === profileModal) {
            profileModal.style.display = 'none';
        }
        // Also close API key popup if clicking outside
        const apiKeyPopup = document.getElementById('api-key-popup');
        if (event.target === apiKeyPopup) {
             apiKeyPopup.style.display = 'none';
        }
    });

    // --- API Key Toggle Logic within Profile Modal ---
    const useOwnApiKeyToggle = document.getElementById('use-own-api-key-toggle');
    const newsApiKeyInputContainer = document.getElementById('news-api-key-input-container');
    const newsApiKeyInput = document.getElementById('news-api-key-input');
    const saveNewsApiKeyBtn = document.getElementById('save-news-api-key-btn');

    if (useOwnApiKeyToggle) {
        useOwnApiKeyToggle.addEventListener('change', () => {
            const isChecked = useOwnApiKeyToggle.checked;
            newsApiKeyInputContainer.style.display = isChecked ? 'block' : 'none';
            localStorage.setItem('useOwnApiKey', isChecked); // Persist toggle state

            if (!isChecked) {
                sessionStorage.removeItem('userNewsApiKey'); // Clear ephemeral key if toggle off
                newsApiKeyInput.value = '';
            }
        });
    }

    if (saveNewsApiKeyBtn) {
        saveNewsApiKeyBtn.addEventListener('click', () => {
            const key = newsApiKeyInput.value.trim();
            if (key) {
                sessionStorage.setItem('userNewsApiKey', key);
                alert('NewsAPI Key saved for this session!');
                profileModal.style.display = 'none'; // Close modal after saving
            } else {
                alert('Please enter a valid NewsAPI Key.');
            }
        });
    }

    // --- API Key Input Pop-up Logic (for when a key is required) ---
    // This pop-up will be shown by specific page scripts (feed.js, search.js, learn.js)
    // when an API call fails due to a missing user-provided key.
    const apiKeyPopup = document.getElementById('api-key-popup');
    const submitApiKeysBtn = document.getElementById('submit-api-keys-btn');
    const popupNewsApiKeyInput = document.getElementById('popup-news-api-key');
    const popupGeminiApiKeyInput = document.getElementById('popup-gemini-api-key');

    // Function to show the API Key Pop-up
    window.showApiKeyPopup = function() {
        apiKeyPopup.style.display = 'flex';
        // Pre-fill if keys were in session storage from a previous submission
        popupNewsApiKeyInput.value = sessionStorage.getItem('userNewsApiKey') || '';
        popupGeminiApiKeyInput.value = sessionStorage.getItem('userGeminiApiKey') || ''; // Assuming a Gemini key option for user later
    };

    if (submitApiKeysBtn) {
        submitApiKeysBtn.addEventListener('click', () => {
            const newsKey = popupNewsApiKeyInput.value.trim();
            const geminiKey = popupGeminiApiKeyInput.value.trim(); // Even if not used yet, for future proofing

            let keysProvided = 0;
            if (newsKey) {
                sessionStorage.setItem('userNewsApiKey', newsKey);
                keysProvided++;
            }
            if (geminiKey) {
                sessionStorage.setItem('userGeminiApiKey', geminiKey);
                keysProvided++;
            }

            if (keysProvided > 0) {
                alert('API Key(s) saved for this session! Please try your action again.');
                apiKeyPopup.style.display = 'none';
                // You might want to trigger a refresh of the page/content here
                // depending on where this popup was triggered from.
            } else {
                alert('Please enter at least one API Key.');
            }
        });
    }

    // --- Navigation Active State ---
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.main-nav a');

    navLinks.forEach(link => {
        // Remove trailing slashes for consistent comparison
        const linkPath = link.getAttribute('href').replace(/\/$/, '');
        const cleanedCurrentPath = currentPath.replace(/\/$/, '');

        // Special handling for the root path '/' and other paths
        if (cleanedCurrentPath === linkPath ||
            (linkPath === '' && cleanedCurrentPath === '/') || // Match '/' to 'home'
            (linkPath === '/feed' && cleanedCurrentPath === '/feed') || // Match /feed
            (linkPath === '/search' && cleanedCurrentPath === '/search') || // Match /search
            (linkPath === '/learn' && cleanedCurrentPath === '/learn') // Match /learn
           ) {
            link.classList.add('active');
        } else if (linkPath === '/' && cleanedCurrentPath === '') { // Handles root path when it's just the domain
            link.classList.add('active');
        }
    });

    // Default profile image (create this image in static/img/)
    // This is a placeholder, you can replace it with a proper default profile icon
    const defaultProfileImage = "{{ url_for('static', filename='img/default_profile.jpeg') }}";
    if (profileIcon) {
        profileIcon.onerror = function() {
            // Fallback if the image doesn't load
            profileIcon.src = defaultProfileImage; // Set a default fallback image path
        };
    }
});