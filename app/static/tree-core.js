/**
 * FamilyTree rendering engine.
 *
 * One renderer, two layouts:
 *   - 'layered': classic top-down generational tree
 *   - 'force':   collapsible force-directed graph
 *
 * Used by BOTH the live dashboard and the exported standalone file, so this
 * file must never assume a server exists. Data in, SVG out.
 */
(function (global) {
  'use strict';

  const COLORS = {
    female: '#e91e8c',
    male: '#0053e2',
    other: '#7c3aed',
    unknown: '#767676',
    spouse: '#ffc220',
    parent: '#9aa0a6',
    text: '#2e2f32',
  };

  const NODE_R = 26;
  const COL_W = 170;
  const ROW_H = 150;

  function colorFor(gender) {
    return COLORS[gender] || COLORS.unknown;
  }

  function initials(node) {
    const first = (node.first_name || '?')[0];
    const last = (node.last_name || '')[0] || '';
    return (first + last).toUpperCase();
  }

  function calcAge(dob, dod) {
    if (!dob) return null;
    const start = new Date(dob);
    if (isNaN(start)) return null;
    const end = dod ? new Date(dod) : new Date();
    let age = end.getFullYear() - start.getFullYear();
    const m = end.getMonth() - start.getMonth();
    if (m < 0 || (m === 0 && end.getDate() < start.getDate())) age--;
    return age >= 0 ? age : null;
  }

  /** Index links once so every layout can ask "who are X's relatives?". */
  function buildIndex(data) {
    const childrenOf = new Map();
    const parentsOf = new Map();
    const spousesOf = new Map();
    const id = (v) => (v && typeof v === 'object' ? v.id : v);
    const push = (map, key, value) => {
      if (!map.has(key)) map.set(key, []);
      map.get(key).push(value);
    };
    data.links.forEach((l) => {
      const source = id(l.source), target = id(l.target);
      if (l.type === 'parent') {
        push(childrenOf, source, target);
        push(parentsOf, target, source);
      } else {
        push(spousesOf, source, target);
        push(spousesOf, target, source);
      }
    });
    return { childrenOf, parentsOf, spousesOf };
  }

  /**
   * Layered layout: group by generation, then order each row so that
   * children sit near their parents instead of scattering randomly.
   */
  function layeredPositions(nodes, index) {
    const rows = new Map();
    nodes.forEach((n) => {
      const gen = n.generation || 0;
      if (!rows.has(gen)) rows.set(gen, []);
      rows.get(gen).push(n);
    });

    const sortedGens = [...rows.keys()].sort((a, b) => a - b);
    const placed = new Map();

    sortedGens.forEach((gen) => {
      const row = rows.get(gen);
      // Sort by average parent x so lines cross as little as possible.
      row.sort((a, b) => {
        const key = (n) => {
          const parents = index.parentsOf.get(n.id) || [];
          const xs = parents.map((p) => placed.get(p)).filter((x) => x !== undefined);
          return xs.length ? xs.reduce((s, x) => s + x, 0) / xs.length : Infinity;
        };
        const diff = key(a) - key(b);
        return diff !== 0 && isFinite(diff) ? diff : a.name.localeCompare(b.name);
      });
      const width = (row.length - 1) * COL_W;
      row.forEach((n, i) => {
        n.x = i * COL_W - width / 2;
        n.y = gen * ROW_H;
        placed.set(n.id, n.x);
      });
    });
    return nodes;
  }

  function renderDetail(panel, node, fieldMeta) {
    if (!panel) return;
    const age = calcAge(node.dob, node.dod);
    const rows = fieldMeta
      .filter((f) => node[f.name] && f.name !== 'first_name' && f.name !== 'last_name')
      .map((f) => `<div class="ft-row"><dt>${f.label}</dt><dd>${escapeHtml(String(node[f.name]))}</dd></div>`)
      .join('');
    panel.innerHTML = `
      <div class="ft-detail-head">
        <div>
          <h3>${escapeHtml(node.name)}</h3>
          ${age !== null ? `<p class="ft-sub">${node.dod ? 'Lived' : 'Age'} ${age} years</p>` : ''}
        </div>
        <button type="button" class="ft-close" aria-label="Close details">&times;</button>
      </div>
      <dl class="ft-detail-body">${rows || '<p class="ft-sub">No extra details recorded yet.</p>'}</dl>`;
    panel.hidden = false;
    panel.querySelector('.ft-close').onclick = () => { panel.hidden = true; };
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function emptyState(container, message) {
    container.innerHTML = `<div class="ft-empty">${message}</div>`;
  }

  /**
   * Draw the tree.
   * @param {Object} opts
   * @param {HTMLElement} opts.container
   * @param {Object} opts.data  {nodes, links}
   * @param {'layered'|'force'} opts.view
   * @param {Array} opts.fieldMeta  [{name,label}] for the detail panel
   * @param {Function} [opts.onSelect] called with the clicked node
   */
  function render(opts) {
    const { container, data, fieldMeta = [], onSelect } = opts;
    const view = opts.view || 'layered';
    container.innerHTML = '';

    if (!data.nodes || !data.nodes.length) {
      emptyState(container, 'Add some family members to see the tree grow! \u{1F331}');
      return;
    }

    const width = container.clientWidth || 900;
    const height = container.clientHeight || 600;
    const index = buildIndex(data);

    const svg = d3.select(container).append('svg')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('viewBox', [0, 0, width, height]);
    const g = svg.append('g');

    const zoom = d3.zoom().scaleExtent([0.15, 3])
      .on('zoom', (e) => g.attr('transform', e.transform));
    svg.call(zoom);

    const panel = document.createElement('div');
    panel.className = 'ft-detail';
    panel.hidden = true;
    container.appendChild(panel);

    const nodes = data.nodes.map((d) => ({ ...d }));
    const byId = new Map(nodes.map((n) => [n.id, n]));
    // Copy links too. d3.forceSimulation rewrites source/target into node
    // objects in place, so handing it the caller's array would corrupt the
    // saved data. Renderers must never mutate what they are given.
    const linkId = (v) => (v && typeof v === 'object' ? v.id : v);
    const links = data.links
      .filter((l) => byId.has(linkId(l.source)) && byId.has(linkId(l.target)))
      .map((l) => ({ source: linkId(l.source), target: linkId(l.target), type: l.type }));

    const linkSel = g.append('g').attr('class', 'ft-links')
      .selectAll('path').data(links).join('path')
      .attr('fill', 'none')
      .attr('stroke', (d) => (d.type === 'spouse' ? COLORS.spouse : COLORS.parent))
      .attr('stroke-width', (d) => (d.type === 'spouse' ? 3 : 2))
      .attr('stroke-dasharray', (d) => (d.type === 'spouse' ? '5,4' : null));

    const nodeSel = g.append('g').attr('class', 'ft-nodes')
      .selectAll('g').data(nodes).join('g')
      .attr('class', 'ft-node')
      .attr('tabindex', 0)
      .attr('role', 'button')
      .attr('aria-label', (d) => `${d.name}. Show details.`)
      .on('click', (e, d) => select(d))
      .on('keydown', (e, d) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); select(d); }
      });

    function select(d) {
      renderDetail(panel, d, fieldMeta);
      if (onSelect) onSelect(d);
    }

    nodeSel.append('circle')
      .attr('r', NODE_R)
      .attr('fill', (d) => colorFor(d.gender))
      .attr('stroke', (d) => (d.dod ? '#2e2f32' : '#fff'))
      .attr('stroke-width', (d) => (d.dod ? 3 : 2));

    nodeSel.append('text').text(initials)
      .attr('text-anchor', 'middle').attr('dy', '0.35em')
      .attr('fill', '#fff').attr('font-size', '15px')
      .attr('font-weight', '700').attr('pointer-events', 'none');

    nodeSel.append('text').text((d) => d.name)
      .attr('text-anchor', 'middle').attr('dy', NODE_R + 16)
      .attr('font-size', '12px').attr('font-weight', '600')
      .attr('fill', COLORS.text).attr('pointer-events', 'none');

    nodeSel.append('text')
      .text((d) => (d.dob ? d.dob.slice(0, 4) + (d.dod ? '\u2013' + d.dod.slice(0, 4) : '') : ''))
      .attr('text-anchor', 'middle').attr('dy', NODE_R + 30)
      .attr('font-size', '10px').attr('fill', COLORS.unknown)
      .attr('pointer-events', 'none');

    if (view === 'layered') {
      runLayered();
    } else {
      runForce();
    }

    function elbow(d) {
      const s = byId.get(d.source) || d.source;
      const t = byId.get(d.target) || d.target;
      if (d.type === 'spouse') return `M${s.x},${s.y} L${t.x},${t.y}`;
      const mid = (s.y + t.y) / 2;
      return `M${s.x},${s.y} V${mid} H${t.x} V${t.y}`;
    }

    function runLayered() {
      layeredPositions(nodes, index);
      linkSel.attr('d', elbow);
      nodeSel.attr('transform', (d) => `translate(${d.x},${d.y})`);
      fitToScreen();
    }

    function runForce() {
      const sim = d3.forceSimulation(nodes)
        .force('link', d3.forceLink(links).id((d) => d.id)
          .distance((l) => (l.type === 'spouse' ? 70 : 130)))
        .force('charge', d3.forceManyBody().strength(-420))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collide', d3.forceCollide().radius(NODE_R + 18));

      nodeSel.call(d3.drag()
        .on('start', (e, d) => {
          if (!e.active) sim.alphaTarget(0.3).restart();
          d.fx = d.x; d.fy = d.y;
        })
        .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y; })
        .on('end', (e, d) => {
          if (!e.active) sim.alphaTarget(0);
          d.fx = null; d.fy = null;
        }));

      sim.on('tick', () => {
        linkSel.attr('d', (d) => `M${d.source.x},${d.source.y} L${d.target.x},${d.target.y}`);
        nodeSel.attr('transform', (d) => `translate(${d.x},${d.y})`);
      });
    }

    function fitToScreen() {
      // Pad by the actual drawn extent, not just node centres: each node
      // carries a name and a date label below it, which is why the bottom
      // row used to get clipped.
      const PAD_X = NODE_R + 60;   // half a name label either side
      const PAD_TOP = NODE_R + 12;
      const PAD_BOTTOM = NODE_R + 40;  // circle + name + dates
      const xs = nodes.map((n) => n.x);
      const ys = nodes.map((n) => n.y);
      const minX = Math.min(...xs) - PAD_X, maxX = Math.max(...xs) + PAD_X;
      const minY = Math.min(...ys) - PAD_TOP, maxY = Math.max(...ys) + PAD_BOTTOM;
      const spanX = Math.max(maxX - minX, 1);
      const spanY = Math.max(maxY - minY, 1);
      // Never scale up past 1:1 -- a two-person tree blown up to fill the
      // panel looks absurd. Do allow shrinking as far as needed so a large
      // family still fits instead of running off the canvas.
      const scale = Math.min(1, width / spanX, height / spanY);
      const tx = width / 2 - scale * (minX + maxX) / 2;
      const ty = height / 2 - scale * (minY + maxY) / 2;
      svg.call(zoom.transform, d3.zoomIdentity.translate(tx, ty).scale(scale));
    }

    return { fitToScreen };
  }

  global.FamilyTree = { render, calcAge, colorFor, escapeHtml, buildIndex };
})(window);
