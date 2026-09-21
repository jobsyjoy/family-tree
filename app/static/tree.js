// Interactive family tree using D3 force-directed graph.
// Nodes = people, links = parent/spouse relationships.
// Supports pan/zoom, drag, and click-to-view details.

(function () {
  const WM_BLUE = '#0053e2';
  const SPARK = '#ffc220';
  const GRAY = '#c9ccd1';

  let simulation = null;

  function colorForGender(gender) {
    if (gender === 'female') return '#e91e8c';
    if (gender === 'male') return WM_BLUE;
    return '#767676';
  }

  function calcAge(dob, dod) {
    if (!dob) return null;
    const start = new Date(dob);
    const end = dod ? new Date(dod) : new Date();
    let age = end.getFullYear() - start.getFullYear();
    const m = end.getMonth() - start.getMonth();
    if (m < 0 || (m === 0 && end.getDate() < start.getDate())) age--;
    return age;
  }

  function showPersonDetail(node) {
    const age = calcAge(node.dob, node.dod);
    const panel = document.getElementById('person-detail-panel');
    if (!panel) return;
    panel.innerHTML = `
      <div class="flex justify-between items-start mb-2">
        <h3 class="font-semibold text-lg">${node.name}</h3>
        <button onclick="document.getElementById('person-detail-panel').classList.add('hidden')"
          class="text-gray-100 hover:text-gray-160">&times;</button>
      </div>
      ${node.dob ? `<p class="text-sm text-gray-100">Born: ${node.dob}${age !== null ? ` (age ${age})` : ''}</p>` : ''}
      ${node.dod ? `<p class="text-sm text-gray-100">Died: ${node.dod}</p>` : ''}
      ${node.gender ? `<p class="text-sm text-gray-100 capitalize">${node.gender}</p>` : ''}
      ${node.notes ? `<p class="text-sm text-gray-160 mt-2 italic">${node.notes}</p>` : ''}
    `;
    panel.classList.remove('hidden');
  }

  function renderTree(data) {
    const container = document.getElementById('tree-container');
    container.innerHTML = '';

    if (!data.nodes || data.nodes.length === 0) {
      container.innerHTML = `
        <div class="flex items-center justify-center h-full text-gray-100 text-sm">
          Add some family members to see the tree grow! 🌱
        </div>`;
      return;
    }

    const width = container.clientWidth || 800;
    const height = container.clientHeight || 600;

    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', [0, 0, width, height]);

    const g = svg.append('g');

    svg.call(
      d3.zoom()
        .scaleExtent([0.3, 3])
        .on('zoom', (event) => g.attr('transform', event.transform))
    );

    // Detail panel overlay
    const detailDiv = document.createElement('div');
    detailDiv.id = 'person-detail-panel';
    detailDiv.className = 'hidden absolute top-3 right-3 bg-white border border-gray-50 shadow-lg rounded-lg p-4 w-64 z-10';
    container.appendChild(detailDiv);

    const nodes = data.nodes.map((d) => ({ ...d }));
    const links = data.links.map((d) => ({ ...d }));

    simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id((d) => d.id).distance((l) => (l.type === 'spouse' ? 60 : 120)))
      .force('charge', d3.forceManyBody().strength(-350))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(45));

    const link = g.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', (d) => (d.type === 'spouse' ? SPARK : GRAY))
      .attr('stroke-width', (d) => (d.type === 'spouse' ? 3 : 2))
      .attr('stroke-dasharray', (d) => (d.type === 'spouse' ? '4,2' : null));

    const node = g.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .attr('class', 'node-card')
      .call(
        d3.drag()
          .on('start', dragStarted)
          .on('drag', dragged)
          .on('end', dragEnded)
      )
      .on('click', (event, d) => showPersonDetail(d));

    node.append('circle')
      .attr('r', 28)
      .attr('fill', (d) => colorForGender(d.gender))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2);

    node.append('text')
      .text((d) => (d.first_name ? d.first_name[0] : '?').toUpperCase())
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('fill', '#fff')
      .attr('font-size', '18px')
      .attr('font-weight', 'bold')
      .attr('pointer-events', 'none');

    node.append('text')
      .text((d) => d.name)
      .attr('text-anchor', 'middle')
      .attr('dy', 44)
      .attr('font-size', '12px')
      .attr('fill', '#2e2f32')
      .attr('pointer-events', 'none');

    simulation.on('tick', () => {
      link
        .attr('x1', (d) => d.source.x)
        .attr('y1', (d) => d.source.y)
        .attr('x2', (d) => d.target.x)
        .attr('y2', (d) => d.target.y);
      node.attr('transform', (d) => `translate(${d.x},${d.y})`);
    });

    function dragStarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }
    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }
    function dragEnded(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
  }

  window.refreshFamilyTree = function () {
    fetch('/api/tree-data')
      .then((res) => res.json())
      .then((data) => renderTree(data))
      .catch((err) => console.error('Failed to load tree data', err));
  };

  document.addEventListener('DOMContentLoaded', () => {
    window.refreshFamilyTree();
    document.body.addEventListener('refreshPeople', () => window.refreshFamilyTree());
    document.body.addEventListener('refreshRelationships', () => window.refreshFamilyTree());
  });
})();
