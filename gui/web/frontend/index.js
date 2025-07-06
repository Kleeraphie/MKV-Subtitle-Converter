import { filesize } from "https://esm.sh/filesize";

document.addEventListener('DOMContentLoaded', () => {
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
        
        uploadedFiles = [...uploadedFiles, ...files]; // Store file objects
        if(fileList) fileList.innerHTML = ''; 
        if(uploadPrompt) uploadPrompt.classList.add('hidden');
        if(fileList) fileList.classList.remove('hidden');

        uploadedFiles.forEach(file => {
            const fileElement = document.createElement('div');
            // TODO: Make icon color change with darkmode like in initial commit
            fileElement.className = 'flex items-center justify-between bg-white dark:bg-slate-700 p-2 rounded-md border border-slate-200 dark:border-slate-600 mb-2';
            fileElement.innerHTML = `
                <div class="flex items-center overflow-hidden">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" class="size-4">
                        <path fill-rule="evenodd" d="M1 3.5A1.5 1.5 0 0 1 2.5 2h11A1.5 1.5 0 0 1 15 3.5v9a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 1 12.5v-9Zm1.5.25a.25.25 0 0 1 .25-.25h1.5a.25.25 0 0 1 .25.25v1a.25.25 0 0 1-.25.25h-1.5a.25.25 0 0 1-.25-.25v-1Zm3.75-.25a.25.25 0 0 0-.25.25v3.5c0 .138.112.25.25.25h3.5a.25.25 0 0 0 .25-.25v-3.5a.25.25 0 0 0-.25-.25h-3.5ZM6 8.75a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 .25.25v3.5a.25.25 0 0 1-.25.25h-3.5a.25.25 0 0 1-.25-.25v-3.5Zm5.75-5.25a.25.25 0 0 0-.25.25v1c0 .138.112.25.25.25h1.5a.25.25 0 0 0 .25-.25v-1a.25.25 0 0 0-.25-.25h-1.5ZM2.5 11.25a.25.25 0 0 1 .25-.25h1.5a.25.25 0 0 1 .25.25v1a.25.25 0 0 1-.25.25h-1.5a.25.25 0 0 1-.25-.25v-1Zm9.25-.25a.25.25 0 0 0-.25.25v1c0 .138.112.25.25.25h1.5a.25.25 0 0 0 .25-.25v-1a.25.25 0 0 0-.25-.25h-1.5ZM2.5 8.75a.25.25 0 0 1 .25-.25h1.5a.25.25 0 0 1 .25.25v1a.25.25 0 0 1-.25.25h-1.5a.25.25 0 0 1-.25-.25v-1Zm9.25-.25a.25.25 0 0 0-.25.25v1c0 .138.112.25.25.25h1.5a.25.25 0 0 0 .25-.25v-1a.25.25 0 0 0-.25-.25h-1.5ZM2.5 6.25A.25.25 0 0 1 2.75 6h1.5a.25.25 0 0 1 .25.25v1a.25.25 0 0 1-.25.25h-1.5a.25.25 0 0 1-.25-.25v-1ZM11.75 6a.25.25 0 0 0-.25.25v1c0 .138.112.25.25.25h1.5a.25.25 0 0 0 .25-.25v-1a.25.25 0 0 0-.25-.25h-1.5Z" clip-rule="evenodd" />
                    </svg>
                    <span class="ml-3 text-sm text-slate-700 dark:text-slate-200 truncate">${file.name}</span>
                </div>
                <span class="text-xs text-slate-500 dark:text-slate-400 flex-shrink-0 ml-2">${filesize(file.size)}</span>`;
            if(fileList) fileList.appendChild(fileElement);
        });
    }

    // --- Slider Logic ---
    if (brightnessSlider) {
        brightnessSlider.addEventListener('input', (e) => {
            if(brightnessValue) brightnessValue.textContent = `${e.target.value}%`;
        });
    }

    // Fetch the version when the page loads
    getVersion();
});

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
