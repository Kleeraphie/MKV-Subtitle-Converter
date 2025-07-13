// An object to store our loaded translations
const translations = {};
let currentLanguage = 'de';

async function loadTranslations(lang) {
    if (translations[lang]) {
        return; // Already loaded
    }
    try {
        const response = await fetch(`/locales/${lang}.json`);
        if (!response.ok) {
            throw new Error(`Could not load ${lang}.json`);
        }
        translations[lang] = await response.json();
        console.log(`Language '${lang}' loaded.`);
    } catch (error) {
        console.error(`Failed to load translations for ${lang}:`, error);
        // Fallback to English if the desired language fails to load
        if (lang !== 'en') {
            await loadTranslations('en');
        }
    }
}

function setLanguage(lang) {
    currentLanguage = lang;
}

// The translation function "t"
function t(key, lang = currentLanguage) {
    return translations[lang]?.[key] || "TODO: " + key;
}

// Export the functions so we can use them in other files
export { loadTranslations, setLanguage, t };