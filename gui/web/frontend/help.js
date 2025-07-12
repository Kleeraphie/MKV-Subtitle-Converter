document.getElementById('open-help').addEventListener('click', function(e) {
    e.preventDefault();
    document.getElementById('help-modal').classList.remove('hidden');
    document.getElementById('tab-general').focus();
});
document.getElementById('close-help').addEventListener('click', function() {
    document.getElementById('help-modal').classList.add('hidden');
});
document.getElementById('check-update-button').addEventListener('click', async () => {
    try {
        const response = await fetch('/checkForUpdate');
        const { updateAvailable, latestVersion } = await response.json();
        if (updateAvailable) {
            alert(`Ein Update ist verfügbar! Die neueste Version ist ${latestVersion}.`);
        } else {
            alert('Sie haben die neueste Version installiert.');
        }
    } catch (error) {
        console.error('Fehler beim Überprüfen auf Updates:', error);
        alert('Fehler beim Überprüfen auf Updates. Bitte versuchen Sie es später erneut.');
    }
});