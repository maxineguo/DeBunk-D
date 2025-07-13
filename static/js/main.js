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
            if (darkThemeRadio) darkThemeRadio.checked = true;
        } else {
            body.classList.add('light-theme');
            body.classList.remove('dark-theme');
            if (lightThemeRadio) lightThemeRadio.checked = true;
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
    const profileIcon = document.querySelector('.profile-pic-container .profile-pic'); // Select the image directly
    const profileModal = document.getElementById('profile-modal');
    const profileCloseBtn = document.getElementById('profile-close-btn');

    if (profileIcon) {
        profileIcon.addEventListener('click', () => {
            if (profileModal) {
                profileModal.style.display = 'flex'; // Use flex to center
                // Load current API key settings here if they were previously saved in session/local storage
                const useOwnApiKeyToggle = document.getElementById('use-own-api-key-toggle');
                const newsApiKeyInputContainer = document.getElementById('news-api-key-input-container');
                const newsApiKeyInput = document.getElementById('news-api-key-input');
                const geminiApiKeyInput = document.getElementById('gemini-api-key-input'); // Assuming you'll add this input

                const useOwnKey = localStorage.getItem('useOwnApiKey') === 'true';
                if (useOwnApiKeyToggle) useOwnApiKeyToggle.checked = useOwnKey;
                if (newsApiKeyInputContainer) newsApiKeyInputContainer.style.display = useOwnKey ? 'block' : 'none';

                if (useOwnKey) {
                    const userNewsApiKey = sessionStorage.getItem('userNewsApiKey');
                    const userGeminiApiKey = sessionStorage.getItem('userGeminiApiKey');
                    if (newsApiKeyInput) newsApiKeyInput.value = userNewsApiKey || '';
                    if (geminiApiKeyInput) geminiApiKeyInput.value = userGeminiApiKey || '';
                }
            }
        });
    }

    if (profileCloseBtn) {
        profileCloseBtn.addEventListener('click', () => {
            if (profileModal) profileModal.style.display = 'none';
        });
    }

    // Close modal if clicking outside
    window.addEventListener('click', (event) => {
        if (profileModal && event.target === profileModal) {
            profileModal.style.display = 'none';
        }
        const apiKeyPopup = document.getElementById('api-key-popup');
        if (apiKeyPopup && event.target === apiKeyPopup) {
             apiKeyPopup.style.display = 'none';
        }
    });

    // --- API Key Toggle Logic within Profile Modal ---
    const useOwnApiKeyToggle = document.getElementById('use-own-api-key-toggle');
    const newsApiKeyInputContainer = document.getElementById('news-api-key-input-container');
    const newsApiKeyInput = document.getElementById('news-api-key-input');
    const geminiApiKeyInput = document.getElementById('gemini-api-key-input'); // New: Gemini API key input
    const saveApiKeysBtn = document.getElementById('save-api-keys-btn'); // Renamed from saveNewsApiKeyBtn

    if (useOwnApiKeyToggle) {
        useOwnApiKeyToggle.addEventListener('change', () => {
            const isChecked = useOwnApiKeyToggle.checked;
            if (newsApiKeyInputContainer) newsApiKeyInputContainer.style.display = isChecked ? 'block' : 'none';
            localStorage.setItem('useOwnApiKey', isChecked); // Persist toggle state

            if (!isChecked) {
                sessionStorage.removeItem('userNewsApiKey'); // Clear ephemeral key if toggle off
                sessionStorage.removeItem('userGeminiApiKey'); // Clear Gemini key
                if (newsApiKeyInput) newsApiKeyInput.value = '';
                if (geminiApiKeyInput) geminiApiKeyInput.value = '';
            }
        });
    }

    if (saveApiKeysBtn) { // Use the renamed button
        saveApiKeysBtn.addEventListener('click', () => {
            const newsKey = newsApiKeyInput ? newsApiKeyInput.value.trim() : '';
            const geminiKey = geminiApiKeyInput ? geminiApiKeyInput.value.trim() : '';

            if (newsKey || geminiKey) { // Allow saving even if only one is provided
                if (newsKey) sessionStorage.setItem('userNewsApiKey', newsKey);
                if (geminiKey) sessionStorage.setItem('userGeminiApiKey', geminiKey);
                alert('API Key(s) saved for this session!');
                if (profileModal) profileModal.style.display = 'none'; // Close modal after saving
            } else {
                alert('Please enter at least one API Key.');
            }
        });
    }

    // --- API Key Input Pop-up Logic (for when a key is required) ---
    const apiKeyPopup = document.getElementById('api-key-popup');
    const submitApiKeysBtn = document.getElementById('submit-api-keys-btn');
    const popupNewsApiKeyInput = document.getElementById('popup-news-api-key');
    const popupGeminiApiKeyInput = document.getElementById('popup-gemini-api-key');

    // Function to show the API Key Pop-up
    window.showApiKeyPopup = function() {
        if (apiKeyPopup) {
            apiKeyPopup.style.display = 'flex';
            // Pre-fill if keys were in session storage from a previous submission
            if (popupNewsApiKeyInput) popupNewsApiKeyInput.value = sessionStorage.getItem('userNewsApiKey') || '';
            if (popupGeminiApiKeyInput) popupGeminiApiKeyInput.value = sessionStorage.getItem('userGeminiApiKey') || '';
        }
    };

    if (submitApiKeysBtn) {
        submitApiKeysBtn.addEventListener('click', () => {
            const newsKey = popupNewsApiKeyInput ? popupNewsApiKeyInput.value.trim() : '';
            const geminiKey = popupGeminiApiKeyInput ? popupGeminiApiKeyInput.value.trim() : '';

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
                if (apiKeyPopup) apiKeyPopup.style.display = 'none';
                // You might want to trigger a refresh of the page/content here
                // depending on where this popup was triggered from.
            } else {
                alert('Please enter at least one API Key.');
            }
        });
    }

    // --- Navigation Active State and Underline ---
    const navLinks = document.querySelectorAll('.main-nav ul li a');
    const navUnderline = document.querySelector('.main-nav a.active::after'); // This won't work directly in JS for pseudo-elements

    function updateNavActiveState() {
        const currentPath = window.location.pathname.replace(/\/$/, ''); // Remove trailing slash
        navLinks.forEach(link => {
            const linkPath = link.getAttribute('href').replace(/\/$/, ''); // Remove trailing slash
            link.classList.remove('active'); // Remove active from all first

            // Check for exact match or special home path
            if (currentPath === linkPath || (linkPath === '/' && currentPath === '')) {
                link.classList.add('active');
            }
        });
    }

    // Call on load
    updateNavActiveState();

    // Add hover effects for navigation
    navLinks.forEach(link => {
        link.addEventListener('mouseenter', () => {
            // No direct JS manipulation for :hover pseudo-elements
            // CSS handles this with :not(.active):hover::after
        });
        link.addEventListener('mouseleave', () => {
            // No direct JS manipulation needed
        });
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