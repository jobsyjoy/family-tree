/**
 * Standalone export editor.
 *
 * Runs with zero backend: the family data lives in memory, is mirrored to
 * localStorage so a refresh doesn't lose work, and is saved by downloading a
 * fresh copy of this very file with the new data baked in. That is what makes
 * the export re-shareable: whoever edits it can pass the new file along.
 */
(function () {
  'use strict';

  const BOOT = JSON.parse(document.getElementById('ft-payload').textContent);
  const STORAGE_KEY = 'familyTree:' + (BOOT.title || 'default');
  const FIELDS = BOOT.fields;

  let state = load();
  let view = 'layered';
  let dirty = false;

  function load() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed && Array.isArray(parsed.nodes)) return parsed;
      }
    } catch (e) { /* corrupt cache, fall through to the baked-in data */ }
    return structuredClone(BOOT.data);
  }

  function persist() {
    dirty = true;
    recomputeGenerations();
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) { /* private browsing / quota: in-memory still works */ }
    draw();
    renderList();
    updateStatus();
  }

  function nextId() {
    return state.nodes.reduce((max, n) => Math.max(max, n.id), 0) + 1;
  }

  function displayName(n) {
    return ((n.first_name || '') + ' ' + (n.last_name || '')).trim() || 'Unnamed';
  }

  /** Mirror of the server-side generation calculation in app/tree.py.
   *  Children go one row below their parents; spouses share a row. */
  function recomputeGenerations() {
    const depth = new Map(state.nodes.map((n) => [n.id, 0]));
    const parents = state.links.filter((l) => l.type === 'parent');
    const couples = state.links.filter((l) => l.type === 'spouse');
    for (let i = 0; i <= state.nodes.length; i++) {
      let changed = false;
      parents.forEach((l) => {
        if (!depth.has(l.source) || !depth.has(l.target)) return;
        if (depth.get(l.target) < depth.get(l.source) + 1) {
          depth.set(l.target, depth.get(l.source) + 1);
          changed = true;
        }
      });
      couples.forEach((l) => {
        if (!depth.has(l.source) || !depth.has(l.target)) return;
        const deepest = Math.max(depth.get(l.source), depth.get(l.target));
        if (depth.get(l.source) !== deepest || depth.get(l.target) !== deepest) {
          depth.set(l.source, deepest);
          depth.set(l.target, deepest);
          changed = true;
        }
      });
      if (!changed) break;
    }
    state.nodes.forEach((n) => {
      n.generation = depth.get(n.id) || 0;
      n.name = displayName(n);
    });
  }

  // ---------- Rendering ----------

  function draw() {
    FamilyTree.render({
      container: document.getElementById('tree-container'),
      data: state,
      view,
      fieldMeta: FIELDS,
    });
  }

  function updateStatus() {
    const el = document.getElementById('status');
    el.textContent = dirty
      ? 'Unsaved changes \u2014 click "Save / Share file" to keep them.'
      : state.nodes.length + ' people \u00b7 ' + state.links.length + ' relationships';
    el.className = dirty ? 'status status-dirty' : 'status';
  }

  function renderList() {
    const host = document.getElementById('people-list');
    if (!state.nodes.length) {
      host.innerHTML = '<p class="muted">Nobody here yet. Click "Add person" to start.</p>';
      return;
    }
    const esc = FamilyTree.escapeHtml;
    host.innerHTML = state.nodes
      .slice()
      .sort((a, b) => displayName(a).localeCompare(displayName(b)))
      .map((n) => {
        const bits = [n.dob && 'b. ' + n.dob, n.occupation, n.birth_place]
          .filter(Boolean).map(esc).join(' \u00b7 ');
        return `<div class="card">
          <div>
            <strong>${esc(displayName(n))}</strong>
            ${bits ? `<div class="muted small">${bits}</div>` : ''}
          </div>
          <div class="card-actions">
            <button type="button" data-edit="${n.id}">Edit</button>
            <button type="button" data-del="${n.id}" class="danger">Delete</button>
          </div>
        </div>`;
      }).join('');
  }

  function personOptions(selected) {
    return '<option value="">-- choose --</option>' + state.nodes
      .map((n) => `<option value="${n.id}"${n.id === selected ? ' selected' : ''}>`
        + FamilyTree.escapeHtml(displayName(n)) + '</option>')
      .join('');
  }

  function renderRelationships() {
    const host = document.getElementById('rel-list');
    const byId = new Map(state.nodes.map((n) => [n.id, n]));
    document.getElementById('rel-a').innerHTML = personOptions();
    document.getElementById('rel-b').innerHTML = personOptions();
    if (!state.links.length) {
      host.innerHTML = '<p class="muted">No relationships linked yet.</p>';
      return;
    }
    const esc = FamilyTree.escapeHtml;
    host.innerHTML = state.links.map((l, i) => {
      const a = byId.get(l.source), b = byId.get(l.target);
      if (!a || !b) return '';
      const verb = l.type === 'parent' ? 'is parent of' : 'is married to';
      return `<div class="card">
        <span>${esc(displayName(a))} <em class="muted">${verb}</em> ${esc(displayName(b))}</span>
        <button type="button" data-unlink="${i}" class="danger">Remove</button>
      </div>`;
    }).join('');
  }

  // ---------- Person form ----------

  function openForm(person) {
    const esc = FamilyTree.escapeHtml;
    const groups = [...new Set(FIELDS.map((f) => f.group))];
    const body = groups.map((group) => {
      const inputs = FIELDS.filter((f) => f.group === group).map((f) => {
        const val = person && person[f.name] != null ? String(person[f.name]) : '';
        const id = 'f-' + f.name;
        let input;
        if (f.kind === 'textarea') {
          input = `<textarea id="${id}" name="${f.name}" rows="3">${esc(val)}</textarea>`;
        } else if (f.kind === 'select') {
          input = `<select id="${id}" name="${f.name}"><option value="">--</option>` +
            f.options.map((o) => `<option value="${o}"${o === val ? ' selected' : ''}>`
              + o.charAt(0).toUpperCase() + o.slice(1) + '</option>').join('') + '</select>';
        } else {
          const type = f.kind === 'date' ? 'date' : (f.kind === 'url' ? 'url' : 'text');
          input = `<input id="${id}" type="${type}" name="${f.name}" value="${esc(val)}"`
            + (f.required ? ' required' : '')
            + (f.placeholder ? ` placeholder="${esc(f.placeholder)}"` : '') + '>';
        }
        return `<label class="field"><span>${esc(f.label)}${f.required ? ' *' : ''}</span>${input}</label>`;
      }).join('');
      return `<fieldset><legend>${esc(group)}</legend><div class="grid">${inputs}</div></fieldset>`;
    }).join('');

    const dlg = document.getElementById('person-dialog');
    dlg.querySelector('h2').textContent = person ? 'Edit person' : 'Add person';
    dlg.querySelector('#form-body').innerHTML = body;
    dlg.querySelector('form').dataset.editing = person ? person.id : '';
    dlg.showModal();
    dlg.querySelector('input, select, textarea')?.focus();
  }

  function submitForm(event) {
    event.preventDefault();
    const form = event.target;
    const values = Object.fromEntries(new FormData(form).entries());
    FIELDS.forEach((f) => {
      values[f.name] = (values[f.name] || '').trim() || null;
    });
    const editingId = form.dataset.editing;
    if (editingId) {
      const person = state.nodes.find((n) => n.id === Number(editingId));
      Object.assign(person, values);
    } else {
      state.nodes.push({ ...values, id: nextId(), generation: 0 });
    }
    document.getElementById('person-dialog').close();
    persist();
  }

  function deletePerson(id) {
    const person = state.nodes.find((n) => n.id === id);
    if (!confirm('Remove ' + displayName(person) + ' and all their links?')) return;
    state.nodes = state.nodes.filter((n) => n.id !== id);
    state.links = state.links.filter((l) => l.source !== id && l.target !== id);
    persist();
  }

  function addRelationship(event) {
    event.preventDefault();
    const a = Number(document.getElementById('rel-a').value);
    const b = Number(document.getElementById('rel-b').value);
    const type = document.getElementById('rel-type').value;
    if (!a || !b || a === b) {
      alert('Pick two different people.');
      return;
    }
    const exists = state.links.some((l) =>
      l.type === type && ((l.source === a && l.target === b) ||
        (type === 'spouse' && l.source === b && l.target === a)));
    if (!exists) state.links.push({ source: a, target: b, type });
    persist();
    renderRelationships();
  }

  // ---------- Save / share ----------

  function saveFile() {
    // Rewrite the payload inside a clone of this document, then download it.
    const clone = document.documentElement.cloneNode(true);
    const payloadEl = clone.querySelector('#ft-payload');
    payloadEl.textContent = JSON.stringify({
      title: BOOT.title,
      exported_at: new Date().toLocaleString(),
      fields: FIELDS,
      data: state,
    }).replace(/<\//g, '<\\/');
    // Drop transient UI state so the file opens clean.
    clone.querySelectorAll('dialog[open]').forEach((d) => d.removeAttribute('open'));

    const html = '<!DOCTYPE html>\n' + clone.outerHTML;
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = (BOOT.title || 'family-tree').replace(/[^a-z0-9]+/gi, '-').toLowerCase()
      + '-' + new Date().toISOString().slice(0, 10) + '.html';
    a.click();
    URL.revokeObjectURL(a.href);
    dirty = false;
    updateStatus();
  }

  function exportJson() {
    const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'family-tree-data.json';
    a.click();
    URL.revokeObjectURL(a.href);
  }

  // ---------- Wiring ----------

  function setView(next) {
    view = next;
    document.querySelectorAll('[data-view-btn]').forEach((b) => {
      const active = b.dataset.viewBtn === next;
      b.classList.toggle('view-active', active);
      b.setAttribute('aria-pressed', String(active));
    });
    draw();
  }

  document.addEventListener('DOMContentLoaded', () => {
    recomputeGenerations();
    draw();
    renderList();
    renderRelationships();
    updateStatus();

    document.getElementById('add-person').onclick = () => openForm(null);
    document.getElementById('person-form').onsubmit = submitForm;
    document.getElementById('cancel-form').onclick =
      () => document.getElementById('person-dialog').close();
    document.getElementById('rel-form').onsubmit = addRelationship;
    document.getElementById('save-file').onclick = saveFile;
    document.getElementById('export-json').onclick = exportJson;
    document.querySelectorAll('[data-view-btn]').forEach((b) => {
      b.onclick = () => setView(b.dataset.viewBtn);
    });

    document.getElementById('people-list').addEventListener('click', (e) => {
      const edit = e.target.dataset.edit, del = e.target.dataset.del;
      if (edit) openForm(state.nodes.find((n) => n.id === Number(edit)));
      if (del) deletePerson(Number(del));
    });
    document.getElementById('rel-list').addEventListener('click', (e) => {
      const idx = e.target.dataset.unlink;
      if (idx === undefined) return;
      state.links.splice(Number(idx), 1);
      persist();
      renderRelationships();
    });
    document.querySelectorAll('.tab-btn').forEach((btn) => {
      btn.onclick = () => {
        document.querySelectorAll('.tab-btn').forEach((b) => b.classList.remove('tab-active'));
        document.querySelectorAll('.tab-panel').forEach((p) => { p.hidden = true; });
        btn.classList.add('tab-active');
        document.getElementById('panel-' + btn.dataset.tab).hidden = false;
        if (btn.dataset.tab === 'tree') draw();
      };
    });

    window.addEventListener('beforeunload', (e) => {
      if (dirty) { e.preventDefault(); e.returnValue = ''; }
    });
  });
})();
