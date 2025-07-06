import { filesize } from "../node_modules/filesize/dist/filesize.esm.js";

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
        
        uploadedFiles = [...files]; // Store file objects
        if(fileList) fileList.innerHTML = ''; 
        if(uploadPrompt) uploadPrompt.classList.add('hidden');
        if(fileList) fileList.classList.remove('hidden');

        uploadedFiles.forEach(file => {
            const fileElement = document.createElement('div');
            fileElement.className = 'flex items-center justify-between bg-white dark:bg-slate-700 p-2 rounded-md border border-slate-200 dark:border-slate-600 mb-2';
            fileElement.innerHTML = `
                <div class="flex items-center overflow-hidden">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-slate-500 dark:text-slate-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
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
