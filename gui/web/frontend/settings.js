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