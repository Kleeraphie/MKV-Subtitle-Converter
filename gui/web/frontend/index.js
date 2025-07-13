import { filesize } from "https://esm.sh/filesize";
import { loadTranslations, setLanguage, t } from './i18n.js';

document.addEventListener('DOMContentLoaded', async () => {
    // Set default language and load translations
    const userLanguage = 'de'; // or get from user settings
    loadTranslations(userLanguage).then(() => {
        // Apply translations to the DOM
        applyTranslations();
    }).catch(error => {
        console.error(`Error loading translations for ${userLanguage}:`, error);
    });
    setLanguage(userLanguage);

    // --- DOM Elements ---
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('file-input');
    const fileList = document.getElementById('file-list');
    const uploadPrompt = document.getElementById('upload-prompt');
    const brightnessSlider = document.getElementById('brightness-slider');
    const brightnessValue = document.getElementById('brightness-value');
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const sunIcon = document.getElementById('sun-icon');
    const moonIcon = document.getElementById('moon-icon');
    const convertButton = document.getElementById('convert-button');
    let uploadedFiles = [];

    // --- Dark Mode Logic ---
    const applyDarkMode = (isDark) => {
        if (isDark) {
            document.documentElement.classList.add('dark');
            if(sunIcon) sunIcon.classList.add('hidden');
            if(moonIcon) moonIcon.classList.remove('hidden');
        } else {
            document.documentElement.classList.remove('dark');
            if(sunIcon) sunIcon.classList.remove('hidden');
            if(moonIcon) moonIcon.classList.add('hidden');
        }
    };

    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', () => {
            const isDarkMode = document.documentElement.classList.toggle('dark');
            localStorage.setItem('darkMode', isDarkMode);
            applyDarkMode(isDarkMode);
            setTheme(isDarkMode ? 'Dark' : 'Light'); // Save theme preference
        });
    }

    // On page load, check for saved preference and apply it
    const savedMode = localStorage.getItem('darkMode') === 'true';
    applyDarkMode(savedMode);

    // --- File Handling Logic ---
    if (dropArea) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
          dropArea.addEventListener(eventName, preventDefaults, false);
          document.body.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
          e.preventDefault();
          e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
          dropArea.addEventListener(eventName, () => dropArea.classList.add('bg-blue-50', 'dark:bg-blue-900/50', 'border-blue-500'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
          dropArea.addEventListener(eventName, () => dropArea.classList.remove('bg-blue-50', 'dark:bg-blue-900/50', 'border-blue-500'), false);
        });

        dropArea.addEventListener('drop', (e) => handleFiles(e.dataTransfer.files), false);
    }

    if (fileInput) {
        fileInput.addEventListener('change', (e) => handleFiles(e.target.files));
    }

    function handleFiles(files) {
        if (!files.length) return;
        
        const newFilesToAdd = [];
        for (const newFile of files) {
            const isDuplicate = uploadedFiles.some(existingFile => 
                existingFile.name === newFile.name && existingFile.size === newFile.size
            );

            if (!isDuplicate) {
                newFilesToAdd.push(newFile);
            }
        }

        uploadedFiles = [...uploadedFiles, ...newFilesToAdd]; 
        renderFileList(); // Call a new function to render the list
    }

    function renderFileList() {
        if(fileList) fileList.innerHTML = ''; 
        
        if (uploadedFiles.length > 0) {
            if(uploadPrompt) uploadPrompt.classList.add('hidden');
            if(fileList) fileList.classList.remove('hidden');
        } else {
            if(uploadPrompt) uploadPrompt.classList.remove('hidden');
            if(fileList) fileList.classList.add('hidden');
        }

        uploadedFiles.forEach((file, index) => {
            const fileElement = document.createElement('div');
            fileElement.className = 'flex items-center justify-between bg-white dark:bg-slate-700 p-2 rounded-md border border-slate-200 dark:border-slate-600 mb-2';
            fileElement.innerHTML = `
                <div class="flex items-center overflow-hidden">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" class="size-4 text-slate-500 dark:text-slate-400">
                        <path fill-rule="evenodd" d="M1 3.5A1.5 1.5 0 0 1 2.5 2h11A1.5 1.5 0 0 1 15 3.5v9a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 1 12.5v-9Zm1.5.25a.25.25 0 0 1 .25-.25h1.5a.25.25 0 0 1 .25.25v1a.25.25 0 0 1-.25.25h-1.5a.25.25 0 0 1-.25-.25v-1Zm3.75-.25a.25.25 0 0 0-.25.25v3.5c0 .138.112.25.25.25h3.5a.25.25 0 0 0 .25-.25v-3.5a.25.25 0 0 0-.25-.25h-3.5ZM6 8.75a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.5a.25.25 0 0 1-.25.25h-3.5a.25.25 0 0 1-.25-.25v-3.5Zm5.75-5.25a.25.25 0 0 0-.25.25v1c0 .138.112.25.25.25h1.5a.25.25 0 0 0 .25-.25v-1a.25.25 0 0 0-.25-.25h-1.5ZM2.5 11.25a.25.25 0 0 1 .25-.25h1.5a.25.25 0 0 1 .25.25v1a.25.25 0 0 1-.25.25h-1.5a.25.25 0 0 1-.25-.25v-1Zm9.25-.25a.25.25 0 0 0-.25.25v1c0 .138.112.25.25.25h1.5a.25.25 0 0 0 .25-.25v-1a.25.25 0 0 0-.25-.25h-1.5ZM2.5 8.75a.25.25 0 0 1 .25-.25h1.5a.25.25 0 0 1 .25.25v1a.25.25 0 0 1-.25.25h-1.5a.25.25 0 0 1-.25-.25v-1Zm9.25-.25a.25.25 0 0 0-.25.25v1c0 .138.112.25.25.25h1.5a.25.25 0 0 0 .25-.25v-1a.25.25 0 0 0-.25-.25h-1.5ZM2.5 6.25A.25.25 0 0 1 2.75 6h1.5a.25.25 0 0 1 .25.25v1a.25.25 0 0 1-.25.25h-1.5a.25.25 0 0 1-.25-.25v-1ZM11.75 6a.25.25 0 0 0-.25.25v1c0 .138.112.25.25.25h1.5a.25.25 0 0 0 .25-.25v-1a.25.25 0 0 0-.25-.25h-1.5Z" clip-rule="evenodd" />
                    </svg>
                    <span class="ml-3 text-sm text-slate-700 dark:text-slate-200 truncate">${file.name}</span>
                </div>
                <div class="flex items-center">
                    <span class="text-xs text-slate-500 dark:text-slate-400 flex-shrink-0 ml-2">${filesize(file.size)}</span>
                    <button class="delete-file-btn ml-3 p-1 rounded-full text-slate-400 hover:text-red-500 hover:bg-red-100 dark:hover:bg-red-900/50 transition-colors duration-200" data-index="${index}" title="Datei entfernen">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" class="size-4">
                            <path fill-rule="evenodd" d="M8 15A7 7 0 1 0 8 1a7 7 0 0 0 0 14Zm2.78-4.22a.75.75 0 0 0 0-1.06L9.06 8l1.72-1.72a.75.75 0 0 0-1.06-1.06L8 6.94l-1.72-1.72a.75.75 0 0 0-1.06 1.06L6.94 8l-1.72 1.72a.75.75 0 1 0 1.06 1.06L8 9.06l1.72 1.72a.75.75 0 0 0 1.06 0Z" clip-rule="evenodd" />
                        </svg>
                    </button>
                </div>
                `;
            if(fileList) fileList.appendChild(fileElement);
        });

        document.querySelectorAll('.delete-file-btn').forEach(button => {
            button.addEventListener('click', (e) => {
                const indexToDelete = parseInt(e.currentTarget.dataset.index);
                deleteFile(indexToDelete);
            });
        });
    }

    // New function to delete a file
    function deleteFile(index) {
        if (index > -1 && index < uploadedFiles.length) {
            uploadedFiles.splice(index, 1); // Remove the file at the given index
            renderFileList(); // Re-render the list
        }
    }

    // --- Slider Logic ---
    if (brightnessSlider) {
        brightnessSlider.addEventListener('input', (e) => {
            if(brightnessValue) brightnessValue.textContent = `${e.target.value}%`;
        });
    }

    function getVersion() {
    fetch('/version')
        .then(response => response.text())
        .then(version => {
            const versionElement = document.getElementById('help-version');
            if (versionElement) {
                versionElement.textContent = `${version}`;
            }
        })
        .catch(error => console.error('Error fetching version:', error));
    }

    function getTheme() {
        fetch('/theme')
            .then(response => response.text())
            .then(theme => {
                // select theme in the dropdown
                const themeSelect = document.getElementById('popup-theme');
                if (themeSelect) {
                    themeSelect.value = theme;
                }
                // apply dark mode based on the theme
                applyDarkMode(theme === 'dark');
            })
            .catch(error => console.error('Error fetching theme:', error));

            // print response.text to console
            fetch('/theme')
                .then(response => response.text())
                .then(theme => console.log('Current theme:', theme))
                .catch(error => console.error('Error fetching theme:', error));
    }

    function setTheme(theme) {
        fetch('/theme', {
            method: 'POST',
            headers: {
                'Content-Type': 'text/plain'
            },
            body: theme
        })
        .then(response => {
            if (!response.ok) {
                console.error('Failed to set theme:', response.statusText);
            }
        })
        .catch(error => console.error('Error setting theme:', error));
    }

    async function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                console.error('File upload failed:', response.statusText);
            }
        } catch (error) {
            console.error('Error uploading file:', error);
        }
    }

    async function startConversion() {
        for (const file of uploadedFiles) {
            await uploadFile(file);
        }

        const settings = {
            brightness: document.getElementById('brightness-slider').value,
            edit: document.getElementById('edit-before-muxing').checked,
            saveImages: document.getElementById('save-pgs-images').checked,
            keepFiles: document.getElementById('keep-original-mkv').checked,
            keepOldSubs: document.getElementById('keep-copy-old').checked,
            keepNewSubs: document.getElementById('keep-copy-new').checked,
            useDiffLang: document.getElementById('use-different-languages').checked
        };

        try {
            const response = await fetch('/convert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });

            const data = await response.json();
            if (data.success) {
                alert('Konvertierung erfolgreich!');
            } else {
                alert('Fehler bei der Konvertierung: ' + data.error);
            }
        } catch (error) {
            console.error('Error during conversion:', error);
        }
    }

    // Fetch the version when the page loads
    getVersion();
    getTheme();

    convertButton.addEventListener('click', startConversion);

    function applyTranslations() {
        document.querySelectorAll('[i18n]').forEach(element => {
            const key = element.getAttribute('i18n');
            element.textContent = t(key);
        });
    }
});
