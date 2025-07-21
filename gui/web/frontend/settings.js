document.getElementById('open-settings').addEventListener('click', function(e) {
    e.preventDefault();
    document.getElementById('settings-modal').classList.remove('hidden');
    document.getElementById('tab-general').focus();
});
document.getElementById('close-settings').addEventListener('click', function() {
    document.getElementById('settings-modal').classList.add('hidden');
});
document.getElementById('close-settings-2').addEventListener('click', function() {
    document.getElementById('settings-modal').classList.add('hidden');
});
// Tab switching logic for settings modal
const tabs = document.querySelectorAll('.settings-tab');
const contents = document.querySelectorAll('.settings-content');
tabs.forEach(tab => {
    tab.addEventListener('click', function() {
        tabs.forEach(t => t.classList.remove('bg-slate-100', 'font-semibold'));
        contents.forEach(c => c.classList.add('hidden'));
        tab.classList.add('bg-slate-100', 'font-semibold');
        document.getElementById('settings-content-' + tab.dataset.tab).classList.remove('hidden');
    });
});
document.getElementById('open-settings-help').addEventListener('click', function(e) {
    e.preventDefault();
    document.getElementById('settings-help-modal').classList.remove('hidden');
    document.getElementById('tab-general').focus();
});
document.getElementById('close-settings-help').addEventListener('click', function() {
    document.getElementById('settings-help-modal').classList.add('hidden');
});
document.getElementById('close-settings-help-2').addEventListener('click', function() {
    document.getElementById('settings-help-modal').classList.add('hidden');
});

function getUserConfig() {
    fetch('/userSettings')
        .then(response => response.json())
        .then(config => {
            console.log('User config loaded.');
            // Apply user config settings to the UI
            document.getElementById('popup-language').value = config.General.sLanguage;
            document.getElementById('popup-updates').checked = config.General.bUpdates;
            document.getElementById('popup-theme').value = config.General.sTheme;
        })
        .catch(error => console.error('Error loading user config:', error));
}

getUserConfig();

document.getElementById('save-settings').addEventListener('click', function() {
    const settings = {
        General: {
            sLanguage: document.getElementById('popup-language').value,
            bUpdates: document.getElementById('popup-updates').checked,
            sTheme: document.getElementById('popup-theme').value
        }
    };

    fetch('/userSettings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
    })
    .then(() => {
        document.getElementById('settings-modal').classList.add('hidden');
    })
    .catch(error => console.error('Error saving settings:', error));
});