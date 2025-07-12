// An object to store our loaded translations
const translations = {};
let currentLanguage = 'en';

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
    // Fallback to 'en' if the current language isn't loaded for some reason
    // const lang = translations[currentLanguage] ? currentLanguage : 'en';
    return translations[lang]?.[key] || "Test";
}

// Export the functions so we can use them in other files
export { loadTranslations, setLanguage, t };