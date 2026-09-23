// Dashboard adapter: fetches live data and hands it to the shared renderer.
// All drawing logic lives in tree-core.js so the export can reuse it verbatim.
(function () {
  'use strict';

  let currentView = 'layered';
  let fieldMeta = [];

  function draw() {
    const container = document.getElementById('tree-container');
    if (!container) return;
    fetch('/api/tree-data')
      .then((res) => res.json())
      .then((data) => {
        FamilyTree.render({ container, data, view: currentView, fieldMeta });
      })
      .catch((err) => console.error('Failed to load tree data', err));
  }

  window.setTreeView = function (view) {
    currentView = view;
    document.querySelectorAll('[data-view-btn]').forEach((btn) => {
      const active = btn.dataset.viewBtn === view;
      btn.classList.toggle('view-active', active);
      btn.setAttribute('aria-pressed', String(active));
    });
    draw();
  };

  window.refreshFamilyTree = draw;

  document.addEventListener('DOMContentLoaded', () => {
    const metaEl = document.getElementById('field-meta');
    if (metaEl) fieldMeta = JSON.parse(metaEl.textContent);

    // Wire the layout toggle. Without this the buttons are just decor.
    document.querySelectorAll('[data-view-btn]').forEach((btn) => {
      btn.addEventListener('click', () => window.setTreeView(btn.dataset.viewBtn));
    });

    draw();
    ['refreshPeople', 'refreshRelationships'].forEach((evt) =>
      document.body.addEventListener(evt, draw)
    );
    window.addEventListener('resize', () => {
      clearTimeout(window._ftResizeTimer);
      window._ftResizeTimer = setTimeout(draw, 250);
    });
  });
})();
