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
    const headerProfilePic = document.querySelector('.profile-pic-container .profile-pic'); // The small profile pic in the header
    const profileModal = document.getElementById('profile-modal');
    const profileCloseBtn = document.getElementById('profile-close-btn');

    // Elements for profile pic selection
    const profilePicDisplayArea = document.getElementById('profile-pic-display-area'); // Wrapper for current pic & overlay
    const modalProfilePic = document.getElementById('modal-profile-pic'); // The larger profile pic img in the modal
    const mainSettingsView = document.getElementById('main-settings-view'); // Container for Theme and API settings
    const profilePicOptionsView = document.getElementById('profile-pic-options-view'); // Container for avatar grid
    const backToSettingsBtn = document.getElementById('back-to-settings-btn');
    const avatarOptionsGrid = document.getElementById('avatar-options-grid');
    const selectedPfpTopImg = document.getElementById('selected-pfp-top-img'); // The image for the selected PFP at the top of the options view

    // Username Elements
    const usernameArea = document.getElementById('username-area');
    const usernameText = document.getElementById('username-text');
    const usernameEditIcon = document.getElementById('username-edit-icon');
    const usernameInput = document.getElementById('username-input');
    const defaultUsername = "Your name";

    // API Key Settings Elements
    const useOwnApiKeyToggle = document.getElementById('use-own-api-key-toggle');
    const apiKeyInputContainer = document.getElementById('api-key-input-container');
    const newsApiKeyInput = document.getElementById('news-api-key-input');
    const geminiApiKeyInput = document.getElementById('gemini-api-key-input');
    const saveApiKeysBtn = document.getElementById('save-api-keys-btn');
    const apiKeyMessage = document.getElementById('api-key-message'); // Message display area within modal

    // Home Page Welcome Message Element
    const welcomeMessageElement = document.getElementById('welcome-message'); // NEW: Reference to the welcome message

    // Function to display messages within the modal
    function showModalMessage(message, isError = false) {
        if (apiKeyMessage) {
            apiKeyMessage.textContent = message;
            apiKeyMessage.style.display = 'block';
            apiKeyMessage.classList.remove('text-green-600', 'text-red-600');
            apiKeyMessage.classList.add(isError ? 'text-red-600' : 'text-green-600');
            setTimeout(() => {
                apiKeyMessage.style.display = 'none';
                apiKeyMessage.textContent = '';
            }, 3000); // Hide after 3 seconds
        }
    }

    // --- Avatar Data (Your provided list of 28 avatars) ---
    const avatarPaths = [
        "/static/img/avatars/alienpfp.png",
        "/static/img/avatars/catpfp.png",
        "/static/img/avatars/catwomanpfp.png",
        "/static/img/avatars/ciapfp.png",
        "/static/img/avatars/diverpfp.png",
        "/static/img/avatars/dogpfp.png",
        "/static/img/avatars/englishpfp.png",
        "/static/img/avatars/firepfp.png",
        "/static/img/avatars/flowerpfp.png",
        "/static/img/avatars/frogpfp.png",
        "/static/img/avatars/gnomepfp.png",
        "/static/img/avatars/hikerpfp.png",
        "/static/img/avatars/hogpfp.png",
        "/static/img/avatars/indianpfp.png",
        "/static/img/avatars/knightpfp.png",
        "/static/img/avatars/lionpfp.png",
        "/static/img/avatars/monsterpfp.png",
        "/static/img/avatars/mummypfp.png",
        "/static/img/avatars/pandapfp.png",
        "/static/img/avatars/pigeonpfp.png",
        "/static/img/avatars/pilotpfp.png",
        "/static/img/avatars/piratepfp.png",
        "/static/img/avatars/plantpfp.png",
        "/static/img/avatars/robotpfp.png",
        "/static/img/avatars/singerpfp.png",
        "/static/img/avatars/spacepfp.png",
        "/static/img/avatars/wizardpfp.png",
        "/static/img/avatars/zombiepfp.png"
    ];
    // Fallback if no specific avatar is chosen
    const defaultAvatarPath = "{{ url_for('static', filename='img/default_profile.jpeg') }}";


    // --- Page Scroll Lock Functions ---
    function disablePageScroll() {
        document.body.style.overflow = 'hidden';
    }

    function enablePageScroll() {
        document.body.style.overflow = ''; // Resets to default
    }

    // --- Profile Picture View Management ---
    function showProfileSettings() {
        if (mainSettingsView && profilePicOptionsView && profilePicDisplayArea && usernameArea) {
            mainSettingsView.style.display = 'block';
            profilePicOptionsView.style.display = 'none';
            profilePicDisplayArea.style.display = 'flex'; // Show current profile pic area
            usernameArea.style.display = 'flex'; // Show username area
            usernameText.style.display = 'inline'; // Ensure text is visible
            usernameInput.style.display = 'none'; // Hide input
            loadUsername(); // Load current username
        }
    }

    function showAvatarOptions() {
        if (mainSettingsView && profilePicOptionsView && profilePicDisplayArea && usernameArea) {
            mainSettingsView.style.display = 'none';
            profilePicOptionsView.style.display = 'flex'; // Use flex for column layout
            profilePicDisplayArea.style.display = 'none'; // Hide current profile pic area
            usernameArea.style.display = 'none'; // HIDE USERNAME AREA ON AVATAR SELECTION PAGE

            // Update the selected PFP at the top of the options view
            const currentAvatar = localStorage.getItem('userProfilePic') || defaultAvatarPath;
            if (selectedPfpTopImg) {
                selectedPfpTopImg.src = currentAvatar;
            }

            renderAvatarOptions(); // Render avatars when this view is shown
        }
    }

    // --- Render Avatar Options ---
    function renderAvatarOptions() {
        if (!avatarOptionsGrid) return;

        avatarOptionsGrid.innerHTML = ''; // Clear previous options

        const currentSelectedAvatar = localStorage.getItem('userProfilePic') || defaultAvatarPath;

        avatarPaths.forEach(path => {
            const avatarOptionDiv = document.createElement('div');
            avatarOptionDiv.classList.add('avatar-option');
            if (path === currentSelectedAvatar) {
                avatarOptionDiv.classList.add('selected');
            }

            const img = document.createElement('img');
            img.src = path;
            img.alt = 'Avatar';

            avatarOptionDiv.appendChild(img);
            avatarOptionsGrid.appendChild(avatarOptionDiv);

            avatarOptionDiv.addEventListener('click', () => {
                // Remove 'selected' from previously selected
                const previouslySelected = avatarOptionsGrid.querySelector('.avatar-option.selected');
                if (previouslySelected) {
                    previouslySelected.classList.remove('selected');
                }
                // Add 'selected' to the clicked one
                avatarOptionDiv.classList.add('selected');
                
                // Save and update profile pictures
                localStorage.setItem('userProfilePic', path);
                updateProfilePictures(path);
                
                // Update the selected PFP at the top of the options view immediately
                if (selectedPfpTopImg) {
                    selectedPfpTopImg.src = path;
                }
                
                // Optionally, go back to settings after selection
                // showProfileSettings(); // Uncomment if you want it to go back automatically
            });
        });
    }

    // --- Update Profile Pictures (Header and Modal) ---
    function updateProfilePictures(newPath) {
        if (headerProfilePic) {
            headerProfilePic.src = newPath;
        }
        if (modalProfilePic) {
            modalProfilePic.src = newPath;
        }
    }

    // --- Username Functions ---
    function loadUsername() {
        const savedUsername = localStorage.getItem('username');
        if (usernameText) {
            usernameText.textContent = savedUsername || defaultUsername;
        }
        if (usernameInput) {
            usernameInput.value = savedUsername || defaultUsername;
        }
    }

    function saveUsername() {
        if (usernameInput) {
            const newUsername = usernameInput.value.trim();
            if (newUsername) {
                localStorage.setItem('username', newUsername);
                if (usernameText) usernameText.textContent = newUsername;
            } else {
                localStorage.removeItem('username'); // Clear if empty
                if (usernameText) usernameText.textContent = defaultUsername;
            }
            usernameText.style.display = 'inline'; // Show text
            usernameEditIcon.style.display = 'inline'; // Show pencil icon
            usernameInput.style.display = 'none'; // Hide input
            updateWelcomeMessage(); // NEW: Update welcome message after saving username
        }
    }

    // --- Dynamic Welcome Message Function ---
    function updateWelcomeMessage() {
        if (welcomeMessageElement) {
            const currentUsername = localStorage.getItem('username');
            if (currentUsername && currentUsername !== defaultUsername) {
                welcomeMessageElement.textContent = `Welcome back, ${currentUsername}!`;
            } else {
                welcomeMessageElement.textContent = `Welcome back!`;
            }
        }
    }

    // --- Event Listeners ---
    if (headerProfilePic) {
        headerProfilePic.addEventListener('click', () => {
            if (profileModal) {
                profileModal.style.display = 'flex';
                disablePageScroll(); // Disable scroll when modal opens
                showProfileSettings(); // Show main settings view by default when modal opens
                
                // Load current API key settings
                const useOwnKey = localStorage.getItem('useOwnApiKey') === 'true';
                if (useOwnApiKeyToggle) useOwnApiKeyToggle.checked = useOwnKey;
                if (apiKeyInputContainer) apiKeyInputContainer.style.display = useOwnKey ? 'block' : 'none';

                if (useOwnKey) {
                    const userNewsApiKey = sessionStorage.getItem('userNewsApiKey');
                    const userGeminiApiKey = sessionStorage.getItem('userGeminiApiKey');
                    if (newsApiKeyInput) newsApiKeyInput.value = userNewsApiKey || '';
                    if (geminiApiKeyInput) geminiApiKeyInput.value = userGeminiApiKey || '';
                } else {
                    // Clear inputs if toggle is off
                    if (newsApiKeyInput) newsApiKeyInput.value = '';
                    if (geminiApiKeyInput) geminiApiKeyInput.value = '';
                }
                // Hide any previous messages
                if (apiKeyMessage) apiKeyMessage.style.display = 'none';
            }
        });
    } else {
        console.error("Header profile icon element not found!"); // Debugging log
    }

    if (profileCloseBtn) {
        profileCloseBtn.addEventListener('click', () => {
            if (profileModal) {
                profileModal.style.display = 'none';
                enablePageScroll(); // Enable scroll when modal closes
            }
        });
    }

    // Close modal if clicking outside
    window.addEventListener('click', (event) => {
        if (profileModal && event.target === profileModal) {
            profileModal.style.display = 'none';
            enablePageScroll(); // Enable scroll when modal closes by clicking outside
        }
    });

    // Event listener for clicking the main profile picture in the modal to choose new avatar
    if (profilePicDisplayArea) {
        profilePicDisplayArea.addEventListener('click', showAvatarOptions);
    } else {
        console.error("Profile pic display area in modal not found!"); // Debugging log
    }

    // Event listener for the "Back to Settings" button
    if (backToSettingsBtn) {
        backToSettingsBtn.addEventListener('click', showProfileSettings);
    } else {
        console.error("Back to settings button not found!"); // Debugging log
    }

    // --- Username Edit Listeners ---
    if (usernameArea && usernameText && usernameInput && usernameEditIcon) {
        usernameArea.addEventListener('click', () => {
            // Only toggle if not already in input mode
            if (usernameInput.style.display === 'none') {
                usernameText.style.display = 'none';
                usernameEditIcon.style.display = 'none'; // Hide pencil when editing
                usernameInput.style.display = 'inline-block'; // Show input
                usernameInput.focus(); // Focus the input for immediate typing
                usernameInput.select(); // Select existing text
            }
        });

        usernameInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                saveUsername();
            }
        });

        usernameInput.addEventListener('blur', () => {
            saveUsername();
        });
    }


    // --- API Key Toggle Logic within Profile Modal ---
    if (useOwnApiKeyToggle) {
        useOwnApiKeyToggle.addEventListener('change', () => {
            const isChecked = useOwnApiKeyToggle.checked;
            if (apiKeyInputContainer) apiKeyInputContainer.style.display = isChecked ? 'block' : 'none';
            localStorage.setItem('useOwnApiKey', isChecked); // Persist toggle state

            if (!isChecked) {
                sessionStorage.removeItem('userNewsApiKey'); // Clear ephemeral key if toggle off
                sessionStorage.removeItem('userGeminiApiKey'); // Clear Gemini key
                if (newsApiKeyInput) newsApiKeyInput.value = '';
                if (geminiApiKeyInput) geminiApiKeyInput.value = '';
            }
            // Hide any messages when toggle changes
            if (apiKeyMessage) apiKeyMessage.style.display = 'none';
        });
    }

    if (saveApiKeysBtn) {
        saveApiKeysBtn.addEventListener('click', () => {
            const newsKey = newsApiKeyInput ? newsApiKeyInput.value.trim() : '';
            const geminiKey = geminiApiKeyInput ? geminiApiKeyInput.value.trim() : '';

            if (newsKey || geminiKey) {
                if (newsKey) sessionStorage.setItem('userNewsApiKey', newsKey);
                else sessionStorage.removeItem('userNewsApiKey');
                
                if (geminiKey) sessionStorage.setItem('userGeminiApiKey', geminiKey);
                else sessionStorage.removeItem('userGeminiApiKey');
                
                showModalMessage('API Key(s) saved for this session!');
            } else {
                showModalMessage('Please enter at least one API Key.', true);
            }
        });
    }

    // --- Navigation Active State and Underline ---
    const navLinks = document.querySelectorAll('.main-nav ul li a');

    function updateNavActiveState() {
        const currentPath = window.location.pathname.replace(/\/$/, '');
        navLinks.forEach(link => {
            const linkPath = link.getAttribute('href').replace(/\/$/, '');
            link.classList.remove('active');

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
            // CSS handles this with :not(.active):hover::after
        });
        link.addEventListener('mouseleave', () => {
            // No direct JS manipulation needed
        });
    });

    // --- Initial Load of Profile Picture and Username ---
    // Load the user's saved profile picture or use the default
    const savedProfilePic = localStorage.getItem('userProfilePic');
    if (savedProfilePic) {
        updateProfilePictures(savedProfilePic);
    } else {
        updateProfilePictures(defaultAvatarPath);
    }
    // Load the username on initial page load
    loadUsername();
    // NEW: Update welcome message on initial page load
    updateWelcomeMessage();
});