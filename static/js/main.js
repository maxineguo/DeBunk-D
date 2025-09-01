document.addEventListener('DOMContentLoaded', () => {
    // --- Theme Switching Logic ---
    const body = document.body;
    const lightThemeRadio = document.getElementById('light-theme-radio');
    const darkThemeRadio = document.getElementById('dark-theme-radio');
    const lightModePreviewBox = document.getElementById('light-mode-preview');
    const darkModePreviewBox = document.getElementById('dark-mode-preview');

    const headerLogo = document.getElementById('header-logo');
    const lightLogoPath = headerLogo ? headerLogo.dataset.lightLogo : '';
    const darkLogoPath = headerLogo ? headerLogo.dataset.darkLogo : '';

    if (headerLogo) {
        headerLogo.onerror = function() {
            console.error("Failed to load header logo image:", headerLogo.src, "Check file path and server permissions.");
        };
    }

    function applyTheme(theme) {
        if (theme === 'dark') {
            body.classList.add('dark-theme');
            body.classList.remove('light-theme');
            if (darkThemeRadio) darkThemeRadio.checked = true;
            if (darkModePreviewBox) darkModePreviewBox.classList.add('selected');
            if (lightModePreviewBox) lightModePreviewBox.classList.remove('selected');
            if (headerLogo && darkLogoPath) headerLogo.src = darkLogoPath;
        } else {
            body.classList.add('light-theme');
            body.classList.remove('dark-theme');
            if (lightThemeRadio) lightThemeRadio.checked = true;
            if (lightModePreviewBox) lightModePreviewBox.classList.add('selected');
            if (darkModePreviewBox) darkModePreviewBox.classList.remove('selected');
            if (headerLogo && lightLogoPath) headerLogo.src = lightLogoPath;
        }
        localStorage.setItem('theme', theme);
    }

    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);

    if (lightThemeRadio) {
        lightThemeRadio.addEventListener('change', () => applyTheme('light'));
    }
    if (darkThemeRadio) {
        darkThemeRadio.addEventListener('change', () => applyTheme('dark'));
    }

    // --- Profile Modal Logic ---
    const headerProfilePic = document.querySelector('.profile-pic-container .profile-pic');
    const profileModal = document.getElementById('profile-modal');
    const profileCloseBtn = document.getElementById('profile-close-btn');

    const profilePicDisplayArea = document.getElementById('profile-pic-display-area');
    const modalProfilePic = document.getElementById('modal-profile-pic');
    const mainSettingsView = document.getElementById('main-settings-view');
    const profilePicOptionsView = document.getElementById('profile-pic-options-view');
    const backToSettingsBtn = document.getElementById('back-to-settings-btn');
    const avatarOptionsGrid = document.getElementById('avatar-options-grid');
    const selectedPfpTopImg = document.getElementById('selected-pfp-top-img');

    const usernameArea = document.getElementById('username-area');
    const usernameText = document.getElementById('username-text');
    const usernameEditIcon = document.getElementById('username-edit-icon');
    const usernameInput = document.getElementById('username-input');
    const defaultUsername = "Your name";

    // API Key Settings elements
    const useOwnApiKeyToggle = document.getElementById('use-own-api-key-toggle');
    const apiKeyInputContainer = document.getElementById('news-api-key-input-container');
    const newsApiKeyInput = document.getElementById('news-api-key-input');
    const geminiApiKeyInput = document.getElementById('gemini-api-key-input');
    const saveApiKeysBtn = document.getElementById('save-api-keys-btn');
    const apiKeyMessage = document.getElementById('api-key-message');

    const welcomeMessageElement = document.getElementById('welcome-message');

    function showModalMessage(message, isError = false) {
        if (apiKeyMessage) {
            apiKeyMessage.textContent = message;
            apiKeyMessage.style.display = 'block';
            apiKeyMessage.classList.remove('text-green-600', 'text-red-600');
            apiKeyMessage.classList.add(isError ? 'text-red-600' : 'text-green-600');
            setTimeout(() => {
                apiKeyMessage.style.display = 'none';
                apiKeyMessage.textContent = '';
            }, 3000);
        }
    }

    const avatarPaths = [
        "/static/img/avatars/alienpfp.png", "/static/img/avatars/catpfp.png", "/static/img/avatars/catwomanpfp.png",
        "/static/img/avatars/ciapfp.png", "/static/img/avatars/diverpfp.png", "/static/img/avatars/dogpfp.png",
        "/static/img/avatars/englishpfp.png", "/static/img/avatars/firepfp.png", "/static/img/avatars/flowerpfp.png",
        "/static/img/avatars/frogpfp.png", "/static/img/avatars/gnomepfp.png", "/static/img/avatars/hikerpfp.png",
        "/static/img/avatars/hogpfp.png", "/static/img/avatars/indianpfp.png", "/static/img/avatars/knightpfp.png",
        "/static/img/avatars/lionpfp.png", "/static/img/avatars/monsterpfp.png", "/static/img/avatars/mummypfp.png",
        "/static/img/avatars/pandapfp.png", "/static/img/avatars/pigeonpfp.png", "/static/img/avatars/pilotpfp.png",
        "/static/img/avatars/piratepfp.png", "/static/img/avatars/plantpfp.png", "/static/img/avatars/robotpfp.png",
        "/static/img/avatars/singerpfp.png", "/static/img/avatars/spacepfp.png", "/static/img/avatars/wizardpfp.png",
        "/static/img/avatars/zombiepfp.png"
    ];
    const defaultAvatarPath = "/static/img/avatars/default_profile.jpeg";


    // --- Page Scroll Lock Functions ---
    function disablePageScroll() {
        document.body.style.overflow = 'hidden';
    }

    function enablePageScroll() {
        document.body.style.overflow = '';
    }

    // --- Profile Picture View Management ---
    function showProfileSettings() {
        if (mainSettingsView && profilePicOptionsView && profilePicDisplayArea && usernameArea) {
            mainSettingsView.style.display = 'block';
            profilePicOptionsView.style.display = 'none';
            profilePicDisplayArea.style.display = 'flex';
            usernameArea.style.display = 'flex';
            usernameText.style.display = 'inline';
            usernameInput.style.display = 'none';
            loadUsername();
        }
    }

    function showAvatarOptions() {
        if (mainSettingsView && profilePicOptionsView && profilePicDisplayArea && usernameArea) {
            mainSettingsView.style.display = 'none';
            profilePicOptionsView.style.display = 'flex';
            profilePicDisplayArea.style.display = 'none';
            usernameArea.style.display = 'none';

            const currentAvatar = localStorage.getItem('userProfilePic') || defaultAvatarPath;
            if (selectedPfpTopImg) {
                selectedPfpTopImg.src = currentAvatar;
            }
            renderAvatarOptions();
        }
    }

    function renderAvatarOptions() {
        if (!avatarOptionsGrid) return;
        avatarOptionsGrid.innerHTML = '';
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
                const previouslySelected = avatarOptionsGrid.querySelector('.avatar-option.selected');
                if (previouslySelected) {
                    previouslySelected.classList.remove('selected');
                }
                avatarOptionDiv.classList.add('selected');
                localStorage.setItem('userProfilePic', path);
                updateProfilePictures(path);
                if (selectedPfpTopImg) {
                    selectedPfpTopImg.src = path;
                }
            });
        });
    }

    function updateProfilePictures(newPath) {
        if (headerProfilePic) {
            headerProfilePic.src = newPath;
        }
        if (modalProfilePic) {
            modalProfilePic.src = newPath;
        }
    }

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
                localStorage.removeItem('username');
                if (usernameText) usernameText.textContent = defaultUsername;
            }
            usernameText.style.display = 'inline';
            usernameEditIcon.style.display = 'inline';
            usernameInput.style.display = 'none';
            updateWelcomeMessage();
        }
    }

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

    if (headerProfilePic) {
        headerProfilePic.addEventListener('click', () => {
            if (profileModal) {
                profileModal.style.display = 'flex';
                disablePageScroll();
                showProfileSettings();

                // Load current API key settings (this is where the toggle state is read and applied)
                const useOwnKey = localStorage.getItem('useOwnApiKey') === 'true';
                if (useOwnApiKeyToggle) useOwnApiKeyToggle.checked = useOwnKey;

                // MODIFIED: Toggle class instead of inline style
                if (apiKeyInputContainer) {
                    if (useOwnKey) {
                        apiKeyInputContainer.classList.remove('hidden-api-keys');
                        apiKeyInputContainer.classList.add('show-api-keys');
                    } else {
                        apiKeyInputContainer.classList.remove('show-api-keys');
                        apiKeyInputContainer.classList.add('hidden-api-keys');
                    }
                }

                if (useOwnKey) {
                    const userNewsApiKey = sessionStorage.getItem('userNewsApiKey');
                    const userGeminiApiKey = sessionStorage.getItem('userGeminiApiKey');
                    if (newsApiKeyInput) newsApiKeyInput.value = userNewsApiKey || '';
                    if (geminiApiKeyInput) geminiApiKeyInput.value = userGeminiApiKey || '';
                } else {
                    if (newsApiKeyInput) newsApiKeyInput.value = '';
                    if (geminiApiKeyInput) geminiApiKeyInput.value = '';
                }
                if (apiKeyMessage) apiKeyMessage.style.display = 'none';
            }
        });
    } else {
        console.error("Header profile icon element not found!");
    }

    if (profileCloseBtn) {
        profileCloseBtn.addEventListener('click', () => {
            if (profileModal) {
                profileModal.style.display = 'none';
                enablePageScroll();
            }
        });
    }

    window.addEventListener('click', (event) => {
        if (profileModal && event.target === profileModal) {
            profileModal.style.display = 'none';
            enablePageScroll();
        }
    });

    if (profilePicDisplayArea) {
        profilePicDisplayArea.addEventListener('click', showAvatarOptions);
    } else {
        console.error("Profile pic display area in modal not found!");
    }

    if (backToSettingsBtn) {
        backToSettingsBtn.addEventListener('click', showProfileSettings);
    } else {
        console.error("Back to settings button not found!");
    }

    if (usernameArea && usernameText && usernameInput && usernameEditIcon) {
        usernameArea.addEventListener('click', () => {
            if (usernameInput.style.display === 'none') {
                usernameText.style.display = 'none';
                usernameEditIcon.style.display = 'none';
                usernameInput.style.display = 'inline-block';
                usernameInput.focus();
                usernameInput.select();
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
            // MODIFIED: Toggle class instead of inline style
            if (apiKeyInputContainer) {
                if (isChecked) {
                    apiKeyInputContainer.classList.remove('hidden-api-keys');
                    apiKeyInputContainer.classList.add('show-api-keys');
                } else {
                    apiKeyInputContainer.classList.remove('show-api-keys');
                    apiKeyInputContainer.classList.add('hidden-api-keys');
                }
            }
            localStorage.setItem('useOwnApiKey', isChecked);

            if (!isChecked) {
                sessionStorage.removeItem('userNewsApiKey');
                sessionStorage.removeItem('userGeminiApiKey');
                if (newsApiKeyInput) newsApiKeyInput.value = '';
                if (geminiApiKeyInput) geminiApiKeyInput.value = '';
            }
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
    const navLinks = document.querySelectorAll('.main-nav a');

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
    const savedProfilePic = localStorage.getItem('userProfilePic');
    if (savedProfilePic) {
        updateProfilePictures(savedProfilePic);
    } else {
        updateProfilePictures(defaultAvatarPath);
    }
    loadUsername();
    updateWelcomeMessage();
});