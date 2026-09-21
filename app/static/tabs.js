// Simple tab switcher, no framework needed - keep it YAGNI simple.
function showTab(name) {
  const tabs = ['tree', 'people', 'relationships', 'reminders'];
  tabs.forEach((t) => {
    document.getElementById(`tab-${t}`).classList.toggle('hidden', t !== name);
    document.getElementById(`tab-btn-${t}`).classList.toggle('tab-active', t === name);
  });
  if (name === 'tree' && window.refreshFamilyTree) {
    window.refreshFamilyTree();
  }
}
