document.getElementById('open-help').addEventListener('click', function(e) {
    e.preventDefault();
    document.getElementById('help-modal').classList.remove('hidden');
    document.getElementById('help-tab-general').focus();
});
document.getElementById('close-help').addEventListener('click', function() {
    document.getElementById('help-modal').classList.add('hidden');
});