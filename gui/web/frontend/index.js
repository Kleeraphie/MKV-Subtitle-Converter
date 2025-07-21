import { filesize } from "https://esm.sh/filesize";
import { loadTranslations, setLanguage, t } from './i18n.js';

let languages = []
let allIsoCodes = []
// --- Language Mapping Elements ---
const useDifferentLanguagesCheckbox = document.getElementById('use-different-languages');
const languageMappingContainer = document.getElementById('language-mapping-container');
const languageMappingRows = document.getElementById('language-mapping-rows');
const addMappingBtn = document.getElementById('add-language-mapping');

const fileInput = document.getElementById('file-input');
const fileList = document.getElementById('file-list');
const uploadPrompt = document.getElementById('upload-prompt');
const sunIcon = document.getElementById('sun-icon');
const moonIcon = document.getElementById('moon-icon');
let uploadedFiles = [];
let availableVideos = {};

// Elements for file browser modal
const fileBrowserModal = document.getElementById('file-browser-modal');
const availableVideosContainer = document.getElementById('available-videos-container');
const closeFileBrowserBtn = document.getElementById('close-file-browser');
const closeFileBrowserBtn2 = document.getElementById('close-file-browser-2');


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
    const brightnessSlider = document.getElementById('brightness-slider');
    const brightnessValue = document.getElementById('brightness-value');
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    const convertButton = document.getElementById('convert-button');
    

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
    if (fileInput) {
        // We listen on the label, not the hidden input itself
        fileInput.parentElement.addEventListener('click', (e) => {
            // Only open modal if not clicking a delete button or inside the file list
            if (e.target.closest('.delete-file-btn') || e.target.closest('#file-list')) return;
            e.preventDefault();
            if (fileBrowserModal) {
                fileBrowserModal.classList.remove('hidden');
            }
        });
    }
    
    // --- NEU: Event-Listener zum Schließen des Modals ---
    if (closeFileBrowserBtn) {
        closeFileBrowserBtn.addEventListener('click', () => fileBrowserModal.classList.add('hidden'));
    }
    if (closeFileBrowserBtn2) {
        closeFileBrowserBtn2.addEventListener('click', () => fileBrowserModal.classList.add('hidden'));
    }

    // --- Slider Logic ---
    if (brightnessSlider) {
        brightnessSlider.addEventListener('input', (e) => {
            if (brightnessValue) brightnessValue.textContent = `${e.target.value}%`;
        });
    }

    // --- Language Mapping Logic ---
    // Await the languages before setting up the rest of the logic
    await fetchLanguages();
    // Await the IsoCodes before setting up the rest of the logic
    await fetchIsoCodes();

    if (useDifferentLanguagesCheckbox) {
        useDifferentLanguagesCheckbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                languageMappingContainer.classList.remove('hidden');
                if (languageMappingRows.children.length === 0) {
                    addMappingRow(); // Add one row by default
                }
            } else {
                languageMappingContainer.classList.add('hidden');
            }
        });
    }

    if (addMappingBtn) {
        addMappingBtn.addEventListener('click', addMappingRow);
    }
    
    if(convertButton) {
        convertButton.addEventListener('click', startConversion);
    }

    // Fetch the version when the page loads
    getVersion();
    getTheme();
    fetchVideos();
});

// --- Dark Mode Logic ---
const applyDarkMode = (isDark) => {
    if (isDark) {
        document.documentElement.classList.add('dark');
        if (sunIcon) sunIcon.classList.add('hidden');
        if (moonIcon) moonIcon.classList.remove('hidden');
    } else {
        document.documentElement.classList.remove('dark');
        if (sunIcon) sunIcon.classList.remove('hidden');
        if (moonIcon) moonIcon.classList.add('hidden');
    }
};

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
    if (fileList) fileList.innerHTML = '';

    if (uploadedFiles.length > 0) {
        if (uploadPrompt) uploadPrompt.classList.add('hidden');
        if (fileList) fileList.classList.remove('hidden');
    } else {
        if (uploadPrompt) uploadPrompt.classList.remove('hidden');
        if (fileList) fileList.classList.add('hidden');
    }

    uploadedFiles.forEach((file, index) => {
        const truncatedName = truncateMiddle(file.name, 48);
        
        const fileElement = document.createElement('div');
        fileElement.className = 'flex items-center justify-between bg-white dark:bg-slate-700 p-2 rounded-md border border-slate-200 dark:border-slate-600 mb-2';
        fileElement.innerHTML = `
            <div class="flex items-center overflow-hidden" title="${file.name}">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" class="size-4 text-slate-500 dark:text-slate-400">
                    <path fill-rule="evenodd" d="M1 3.5A1.5 1.5 0 0 1 2.5 2h11A1.5 1.5 0 0 1 15 3.5v9a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 1 12.5v-9Zm1.5.25a.25.25 0 0 1 .25-.25h1.5a.25.25 0 0 1 .25.25v1a.25.25 0 0 1-.25.25h-1.5a.25.25 0 0 1-.25-.25v-1Zm3.75-.25a.25.25 0 0 0-.25.25v3.5c0 .138.112.25.25.25h3.5a.25.25 0 0 0 .25-.25v-3.5a.25.25 0 0 0-.25-.25h-3.5ZM6 8.75a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.5a.25.25 0 0 1-.25.25h-3.5a.25.25 0 0 1-.25-.25v-3.5Zm5.75-5.25a.25.25 0 0 0-.25.25v1c0 .138.112.25.25.25h1.5a.25.25 0 0 0 .25-.25v-1a.25.25 0 0 0-.25-.25h-1.5ZM2.5 11.25a.25.25 0 0 1 .25-.25h1.5a.25.25 0 0 1 .25.25v1a.25.25 0 0 1-.25.25h-1.5a.25.25 0 0 1-.25-.25v-1Zm9.25-.25a.25.25 0 0 0-.25.25v1c0 .138.112.25.25.25h1.5a.25.25 0 0 0 .25-.25v-1a.25.25 0 0 0-.25-.25h-1.5ZM2.5 8.75a.25.25 0 0 1 .25-.25h1.5a.25.25 0 0 1 .25.25v1a.25.25 0 0 1-.25.25h-1.5a.25.25 0 0 1-.25-.25v-1Zm9.25-.25a.25.25 0 0 0-.25.25v1c0 .138.112.25.25.25h1.5a.25.25 0 0 0 .25-.25v-1a.25.25 0 0 0-.25-.25h-1.5ZM2.5 6.25A.25.25 0 0 1 2.75 6h1.5a.25.25 0 0 1 .25.25v1a.25.25 0 0 1-.25.25h-1.5a.25.25 0 0 1-.25-.25v-1ZM11.75 6a.25.25 0 0 0-.25.25v1c0 .138.112.25.25.25h1.5a.25.25 0 0 0 .25-.25v-1a.25.25 0 0 0-.25-.25h-1.5Z" clip-rule="evenodd" />
                </svg>
                <span class="ml-3 text-sm text-slate-700 dark:text-slate-200">${truncatedName}</span>
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
        if (fileList) fileList.appendChild(fileElement);
    });

    document.querySelectorAll('.delete-file-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            const indexToDelete = parseInt(e.currentTarget.dataset.index);
            deleteFile(indexToDelete);
        });
    });
}

function deleteFile(index) {
    if (index > -1 && index < uploadedFiles.length) {
        const deletedFile = uploadedFiles.splice(index, 1)[0];
        renderFileList();
        const fileElement = document.querySelector(`.file-item[data-path="${deletedFile.name}"]`);
        if (fileElement) {
            fileElement.classList.remove('font-bold');
        }
    }
}

function truncateMiddle(text, maxLength) {
    if (text.length <= maxLength) {
        return text;
    }
    const half = Math.floor(maxLength / 2) - 2; // -2 for the ellipsis
    return `${text.substring(0, half)}...${text.substring(text.length - half)}`;
}

// --- Fetch Languages ---
const fetchLanguages = async () => {
    try {
        const response = await fetch('/userLanguages');
        if (!response.ok) {
            throw new Error(`Language fetching failed: ${response.statusText}`);
        }
        languages = await response.json();
    } catch (error) {
        console.error("Failed to fetch languages:", error);
    }
};

const fetchIsoCodes = async () => {
    try {
        const response = await fetch('/isoCodes');
        if (!response.ok) {
            throw new Error(`Iso Codes fetching failed: ${response.statusText}`);
        }

        allIsoCodes = await response.json();
    } catch (error) {
        console.error("Failed to fetch Iso Codes:", error);
    }
}

const createLanguageSelect = (name, all_langs = false) => {
    const select = document.createElement('select');
    select.name = name;
    select.className = "w-full sm:w-auto flex-1 px-3 py-1.5 border border-slate-300 dark:border-slate-600 rounded-md bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500";
    var langs;

    if (all_langs) {
        langs = allIsoCodes;
    } else {
        langs = languages;
    }

    langs.forEach((code) => {
        const option = document.createElement('option');
        option.value = code;
        option.textContent = code;
        select.appendChild(option);
    });
    return select;
};

const addMappingRow = () => {
    // TODO: fix padding
    const row = document.createElement('div');
    row.className = 'flex items-center gap-2 animate-fade-in';

    const insteadOfText = document.createElement('span');
    insteadOfText.textContent = t('Instead of');
    insteadOfText.className = 'text-slate-600 dark:text-slate-300';

    const fromSelect = createLanguageSelect('from_lang', true);

    const useText = document.createElement('span');
    useText.textContent = t('use');
    useText.className = 'text-slate-600 dark:text-slate-300';

    const toSelect = createLanguageSelect('to_lang');

    const deleteBtn = document.createElement('button');
    deleteBtn.type = 'button';
    deleteBtn.className = 'p-1 text-slate-400 hover:text-red-500 dark:hover:text-red-400 rounded-full hover:bg-slate-200 dark:hover:bg-slate-700';
    deleteBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" /></svg>';
    deleteBtn.onclick = () => {
        if (languageMappingRows.children.length > 1) {
            row.remove();
            showOrHideDelButtons(Array.from(languageMappingRows.children));
        }
    }

    row.append(insteadOfText, fromSelect, useText, toSelect, deleteBtn);
    languageMappingRows.appendChild(row);

    showOrHideDelButtons(Array.from(languageMappingRows.children));
};

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
        useDiffLang: document.getElementById('use-different-languages').checked,
        diffLangs: Array.from(document.querySelectorAll('#language-mapping-rows > div')).map(row => {
            const fromLang = row.querySelector('select[name="from_lang"]').value;
            const toLang = row.querySelector('select[name="to_lang"]').value;
            return { from: fromLang, to: toLang };
        })
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

function applyTranslations() {
    document.querySelectorAll('[i18n]').forEach(element => {
        const key = element.getAttribute('i18n');
        element.textContent = t(key);
    });
}

function showOrHideDelButtons(rows) {
    rows.forEach((row) => {
        const deleteBtn = row.querySelector('button');
        if (rows.length === 1) {
            deleteBtn.classList.add('hidden');
        } else {
            deleteBtn.classList.remove('hidden');
        }
    });
}

const fetchVideos = async () => {
    try {
        const response = await fetch('/files');
        if (!response.ok) {
            throw new Error(`File fetching failed: ${response.statusText}`);
        }
        const data = await response.json();
        if (data && typeof data === 'object' && !Array.isArray(data)) {
            availableVideos = data;
            if (availableVideosContainer) {
                renderAvailableVideos(availableVideos, availableVideosContainer);
            }
        } else {
            console.error("Unexpected data structure for videos:", data);
            availableVideos = {};
        }
    } catch (error) {
        console.error("Failed to fetch videos:", error);
        availableVideos = {};
    }
};

function renderAvailableVideos(node, container, path = '') {
    container.innerHTML = '';
    const ul = document.createElement('ul');
    ul.className = 'space-y-1';
    for (const key in node) {
        const fullPath = path ? `${path}/${key}` : key;
        const li = document.createElement('li');
        const isDirectory = typeof node[key] === 'object' && node[key] !== null && !node[key].size;
        if (isDirectory) {
            li.innerHTML = `
                <div class="flex items-center cursor-pointer folder-toggle p-1 rounded-md hover:bg-slate-200 dark:hover:bg-slate-700">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" class="size-5 text-slate-500 dark:text-slate-400 mr-2 flex-shrink-0">
                        <path d="M3.5 2A1.5 1.5 0 0 0 2 3.5v9A1.5 1.5 0 0 0 3.5 14h9a1.5 1.5 0 0 0 1.5-1.5v-7A1.5 1.5 0 0 0 12.5 4H9.379a1.5 1.5 0 0 1-1.06-.44L7.257 2.5A1.5 1.5 0 0 0 6.197 2H3.5Z" />
                    </svg>
                    <span class="font-medium text-slate-800 dark:text-slate-200">${key}</span>
                </div>
            `;
            const subContainer = document.createElement('div');
            subContainer.className = 'ml-4 pl-2 border-l border-slate-200 dark:border-slate-700 hidden';
            li.appendChild(subContainer);
            li.querySelector('.folder-toggle').addEventListener('click', (e) => {
                e.stopPropagation();
                const isHidden = subContainer.classList.toggle('hidden');
                if (!isHidden && subContainer.innerHTML === '') {
                    renderAvailableVideos(node[key], subContainer, fullPath);
                }
            });
        } else {
            const fileData = node[key];
            li.innerHTML = `
                <div class="flex items-center cursor-pointer file-item p-1 rounded-md hover:bg-slate-200 dark:hover:bg-slate-700" data-path="${fullPath}">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" class="size-5 text-slate-500 dark:text-slate-400 mr-2 flex-shrink-0">
                        <path fill-rule="evenodd" d="M1 3.5A1.5 1.5 0 0 1 2.5 2h11A1.5 1.5 0 0 1 15 3.5v9a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 1 12.5v-9Zm1.5.25a.25.25 0 0 1 .25-.25h1.5a.25.25 0 0 1 .25.25v1a.25.25 0 0 1-.25.25h-1.5a.25.25 0 0 1-.25-.25v-1Zm3.75-.25a.25.25 0 0 0-.25.25v3.5c0 .138.112.25.25.25h3.5a.25.25 0 0 0 .25-.25v-3.5a.25.25 0 0 0-.25-.25h-3.5ZM6 8.75a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.5a.25.25 0 0 1-.25.25h-3.5a.25.25 0 0 1-.25-.25v-3.5Zm5.75-5.25a.25.25 0 0 0-.25.25v1c0 .138.112.25.25.25h1.5a.25.25 0 0 0 .25-.25v-1a.25.25 0 0 0-.25-.25h-1.5ZM2.5 11.25a.25.25 0 0 1 .25-.25h1.5a.25.25 0 0 1 .25.25v1a.25.25 0 0 1-.25.25h-1.5a.25.25 0 0 1-.25-.25v-1Zm9.25-.25a.25.25 0 0 0-.25.25v1c0 .138.112.25.25.25h1.5a.25.25 0 0 0 .25-.25v-1a.25.25 0 0 0-.25-.25h-1.5ZM2.5 8.75a.25.25 0 0 1 .25-.25h1.5a.25.25 0 0 1 .25.25v1a.25.25 0 0 1-.25.25h-1.5a.25.25 0 0 1-.25-.25v-1Zm9.25-.25a.25.25 0 0 0-.25.25v1c0 .138.112.25.25.25h1.5a.25.25 0 0 0 .25-.25v-1a.25.25 0 0 0-.25-.25h-1.5ZM2.5 6.25A.25.25 0 0 1 2.75 6h1.5a.25.25 0 0 1 .25.25v1a.25.25 0 0 1-.25.25h-1.5a.25.25 0 0 1-.25-.25v-1ZM11.75 6a.25.25 0 0 0-.25.25v1c0 .138.112.25.25.25h1.5a.25.25 0 0 0 .25-.25v-1a.25.25 0 0 0-.25-.25h-1.5Z" clip-rule="evenodd" />
                    </svg>
                    <span class="truncate flex-grow text-sm text-slate-700 dark:text-slate-300">${key}</span>
                    <span class="text-xs text-slate-500 dark:text-slate-400 flex-shrink-0 ml-2">${filesize(fileData.size)}</span>
                </div>
            `;
            li.querySelector('.file-item').addEventListener('click', (e) => {
                e.stopPropagation();
                const target = e.currentTarget;
                const isSelected = target.classList.contains('font-bold');

                if (isSelected) {
                    // Deselect
                    const indexToDeselect = uploadedFiles.findIndex(f => f.name === fullPath);
                    if (indexToDeselect > -1) {
                        deleteFile(indexToDeselect);
                    }
                } else {
                    // Select
                    const file = { name: fullPath, size: fileData.size };
                    handleFiles([file]);
                    target.classList.add('font-bold');
                }
            });
        }
        ul.appendChild(li);
    }
    container.appendChild(ul);
}
