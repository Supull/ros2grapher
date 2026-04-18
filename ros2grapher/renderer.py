import json
import os
from ros2grapher.graph import ROS2Graph

TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>ros2grapher</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #0d1117; color: #e6edf3; font-family: monospace; }

  #header {
    padding: 16px 24px;
    border-bottom: 1px solid #21262d;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  #header h1 { font-size: 16px; color: #58a6ff; }
  #header span { font-size: 12px; color: #8b949e; }

  #canvas { width: 100vw; height: calc(100vh - 53px); }

  .node circle {
    fill: #1f6feb;
    stroke: #388bfd;
    stroke-width: 2px;
    cursor: pointer;
    transition: fill 0.2s;
  }
  .node circle:hover { fill: #388bfd; }
  .node text {
    fill: #e6edf3;
    font-size: 12px;
    font-family: monospace;
    pointer-events: none;
  }

  .topic ellipse {
    fill: #1a3a1a;
    stroke: #3fb950;
    stroke-width: 2px;
    cursor: pointer;
    transition: fill 0.2s;
  }
  .topic ellipse:hover { fill: #223a22; }
  .topic text {
    fill: #3fb950;
    font-size: 11px;
    font-family: monospace;
    pointer-events: none;
  }

  /* AI resolved topics */
  .topic-ai-high ellipse {
    fill: #1a3a1a;
    stroke: #e3b341;
    stroke-width: 2px;
    cursor: pointer;
  }
  .topic-ai-high text { fill: #e3b341; font-size: 11px; font-family: monospace; pointer-events: none; }

  .topic-ai-medium ellipse {
    fill: #2a2a1a;
    stroke: #ff9800;
    stroke-width: 2px;
    cursor: pointer;
  }
  .topic-ai-medium text { fill: #ff9800; font-size: 11px; font-family: monospace; pointer-events: none; }

  .topic-ai-low ellipse {
    fill: #2a1a1a;
    stroke: #f85149;
    stroke-width: 1.5px;
    stroke-dasharray: 3;
    cursor: pointer;
  }
  .topic-ai-low text { fill: #f85149; font-size: 11px; font-family: monospace; pointer-events: none; }

  .orphan ellipse {
    fill: #2a1a1a;
    stroke: #f85149;
    stroke-width: 1.5px;
    stroke-dasharray: 4;
  }
  .orphan text { fill: #f85149; }

  .service rect {
    fill: #2a1f0a;
    stroke: #e3b341;
    stroke-width: 2px;
    cursor: pointer;
    transition: fill 0.2s;
  }
  .service rect:hover { fill: #3a2a0a; }
  .service text {
    fill: #e3b341;
    font-size: 11px;
    font-family: monospace;
    pointer-events: none;
  }

  .link {
    stroke: #30363d;
    stroke-width: 1.5px;
    fill: none;
    marker-end: url(#arrow);
  }

  .link-ai-high {
    stroke: #e3b341;
    stroke-width: 2px;
    fill: none;
    marker-end: url(#arrow);
  }

  .link-ai-medium {
    stroke: #ff9800;
    stroke-width: 2px;
    fill: none;
    marker-end: url(#arrow);
  }

  .link-ai-low {
    stroke: #f85149;
    stroke-width: 1.5px;
    stroke-dasharray: 4;
    fill: none;
    marker-end: url(#arrow);
  }

  .link-service {
    stroke: #e3b341;
    stroke-width: 1.5px;
    stroke-dasharray: 5 3;
    fill: none;
  }

  .group-box {
    stroke-width: 1.5px;
    stroke-dasharray: 6 3;
    fill-opacity: 0.04;
    pointer-events: none;
  }

  .group-label {
    font-size: 11px;
    font-family: monospace;
    fill-opacity: 0.5;
    pointer-events: none;
  }

  #tooltip {
    position: fixed;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 12px;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.15s;
    max-width: 260px;
    line-height: 1.6;
  }
  #tooltip .label { color: #8b949e; font-size: 11px; }
  #tooltip .value { color: #e6edf3; }

  #legend {
    position: fixed;
    bottom: 20px;
    left: 20px;
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 6px;
    padding: 12px 16px;
    font-size: 11px;
    line-height: 2;
  }
  .leg-node { color: #388bfd; }
  .leg-topic { color: #3fb950; }
  .leg-orphan { color: #f85149; }
  .leg-service { color: #e3b341; }
  .leg-group { color: #8b949e; }

  #stats {
    position: fixed;
    top: 70px;
    right: 20px;
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 6px;
    padding: 12px 16px;
    font-size: 11px;
    line-height: 2;
    color: #8b949e;
  }
  #stats span { color: #e6edf3; }
</style>
</head>
<body>

<div id="header">
  <h1>ros2grapher</h1>
  <span id="workspace-path"></span>
</div>

<svg id="canvas"></svg>
<div id="tooltip"></div>

<div id="legend">
  <div class="leg-node">● node</div>
  <div class="leg-topic">◎ topic (certain)</div>
  <div class="leg-orphan">◎ topic (orphan)</div>
  <div class="leg-service">▬ service</div>
  <div class="leg-group">- - package group</div>
  <div style="color:#e3b341">◎ AI resolved (high)</div>
  <div style="color:#ff9800">◎ AI resolved (medium)</div>
  <div style="color:#f85149">◎ AI resolved (low)</div>
</div>

<div id="stats">
  nodes: <span id="s-nodes">0</span><br>
  topics: <span id="s-topics">0</span><br>
  services: <span id="s-services">0</span><br>
  orphans: <span id="s-orphans">0</span><br>
  packages: <span id="s-packages">0</span>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script>
const data = __GRAPH_DATA__;

document.getElementById('workspace-path').textContent = data.workspace;
document.getElementById('s-nodes').textContent = data.nodes.length;
document.getElementById('s-topics').textContent = data.topics.length;
document.getElementById('s-services').textContent = data.services.length;
document.getElementById('s-orphans').textContent = data.orphans.length;

const width = window.innerWidth;
const height = window.innerHeight - 53;
const tooltip = document.getElementById('tooltip');

const svg = d3.select('#canvas')
  .attr('width', width)
  .attr('height', height);

svg.append('defs').append('marker')
  .attr('id', 'arrow')
  .attr('viewBox', '0 -5 10 10')
  .attr('refX', 25)
  .attr('refY', 0)
  .attr('markerWidth', 6)
  .attr('markerHeight', 6)
  .attr('orient', 'auto')
  .append('path')
  .attr('d', 'M0,-5L10,0L0,5')
  .attr('fill', '#30363d');

const g = svg.append('g');

svg.call(d3.zoom().scaleExtent([0.3, 3]).on('zoom', e => {
  g.attr('transform', e.transform);
}));

const packageColors = [
  '#388bfd', '#3fb950', '#e3b341', '#f85149',
  '#bc8cff', '#39d353', '#ff9800', '#00bcd4'
];

// build package map
const packageMap = {};
data.nodes.forEach(n => {
  const pkg = n.package || 'unknown';
  if (!packageMap[pkg]) packageMap[pkg] = [];
  packageMap[pkg].push(n.name);
});

const packages = Object.keys(packageMap);
document.getElementById('s-packages').textContent = packages.length;

const packageColor = {};
packages.forEach((pkg, i) => {
  packageColor[pkg] = packageColors[i % packageColors.length];
});

// build sim nodes
const simNodes = [];
const simLinks = [];
const serviceLinks = [];

data.nodes.forEach(n => {
  simNodes.push({
    id: n.name,
    type: 'node',
    file: n.file,
    package: n.package || 'unknown'
  });
});

data.topics.forEach(t => {
  let type = 'topic';
  if (t.ai_resolved) type = 'topic-ai-' + (t.ai_confidence || 'low');
  simNodes.push({ id: t.topic, type: type, msg_type: t.msg_type, ai_resolved: t.ai_resolved, ai_confidence: t.ai_confidence });
  t.publishers.forEach(pub => {
    const isAi = t.ai_publishers && t.ai_publishers.includes(pub);
    simLinks.push({ source: pub, target: t.topic, ai_resolved: isAi, ai_confidence: t.ai_confidence });
  });
  t.subscribers.forEach(sub => {
    const isAi = t.ai_subscribers && t.ai_subscribers.includes(sub);
    simLinks.push({ source: t.topic, target: sub, ai_resolved: isAi, ai_confidence: t.ai_confidence });
  });
});

data.orphans.forEach(t => {
  simNodes.push({ id: t.topic, type: 'orphan', msg_type: t.msg_type });
  t.publishers.forEach(pub => simLinks.push({ source: pub, target: t.topic }));
  t.subscribers.forEach(sub => simLinks.push({ source: t.topic, target: sub }));
});

data.services.forEach(s => {
  simNodes.push({ id: s.name, type: 'service', srv_type: s.srv_type });
  s.servers.forEach(server => serviceLinks.push({ source: server, target: s.name }));
  s.clients.forEach(client => serviceLinks.push({ source: client, target: s.name }));
});

const allLinks = [...simLinks, ...serviceLinks];

// custom clustering force — gently pulls same-package nodes together
function clusteringForce(alpha) {
  // compute centroid per package
  const centroids = {};
  packages.forEach(pkg => {
    const members = simNodes.filter(n => n.package === pkg && n.x != null);
    if (members.length === 0) return;
    centroids[pkg] = {
      x: members.reduce((s, n) => s + n.x, 0) / members.length,
      y: members.reduce((s, n) => s + n.y, 0) / members.length,
    };
  });

  // nudge each node toward its package centroid
  const strength = 0.08 * alpha;
  simNodes.forEach(n => {
    if (n.type !== 'node') return;
    const c = centroids[n.package];
    if (!c) return;
    n.vx += (c.x - n.x) * strength;
    n.vy += (c.y - n.y) * strength;
  });
}

const sim = d3.forceSimulation(simNodes)
  .force('link', d3.forceLink(allLinks).id(d => d.id).distance(130))
  .force('charge', d3.forceManyBody().strength(-400))
  .force('center', d3.forceCenter(width / 2, height / 2))
  .force('collision', d3.forceCollide(55))
  .force('cluster', clusteringForce);  // custom force

const groupLayer = g.append('g').attr('class', 'groups');

const link = g.append('g').selectAll('path')
  .data(simLinks).enter().append('path')
  .attr('class', d => {
    if (d.ai_resolved) return 'link-ai-' + (d.ai_confidence || 'low');
    return 'link';
  });

const serviceLink = g.append('g').selectAll('path')
  .data(serviceLinks).enter().append('path')
  .attr('class', 'link-service');

const node = g.append('g').selectAll('g')
  .data(simNodes).enter().append('g')
  .attr('class', d => d.type)
  .call(d3.drag()
    .on('start', (e, d) => {
      if (!e.active) sim.alphaTarget(0.3).restart();
      d.fx = d.x; d.fy = d.y;
      sim.force('cluster', null);  // pause clustering while dragging
    })
    .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y; })
    .on('end', (e, d) => {
      if (!e.active) sim.alphaTarget(0);
      d.fx = null; d.fy = null;
      sim.force('cluster', clusteringForce);  // resume clustering on release
    })
  );

node.each(function(d) {
  const el = d3.select(this);
  if (d.type === 'node') {
    el.append('circle').attr('r', 22);
    el.append('text').attr('text-anchor', 'middle').attr('dy', 36).text(d.id);
  } else if (d.type === 'service') {
    el.append('rect').attr('x', -55).attr('y', -14).attr('width', 110).attr('height', 28).attr('rx', 4);
    el.append('text').attr('text-anchor', 'middle').attr('dy', 4).text(d.id);
  } else {
    el.append('ellipse').attr('rx', 55).attr('ry', 18);
    const label = d.ai_resolved ? d.id + ' 🤖' : d.id;
    el.append('text').attr('text-anchor', 'middle').attr('dy', 4).text(label);
  }
});

node.on('mouseover', (e, d) => {
    let html = '';
    if (d.type === 'node') {
      html = `<div class="label">node</div><div class="value">${d.id}</div>
              <div class="label">package</div><div class="value">${d.package}</div>
              <div class="label">file</div><div class="value">${d.file.split('/').pop()}</div>`;
    } else if (d.type === 'service') {
      html = `<div class="label">service</div><div class="value">${d.id}</div>
              <div class="label">type</div><div class="value">${d.srv_type}</div>`;
    } else {
      const aiInfo = d.ai_resolved
        ? `<div class="label">resolved by</div><div class="value">AI (${d.ai_confidence} confidence)</div>`
        : '';
      html = `<div class="label">topic</div><div class="value">${d.id}</div>
              <div class="label">msg type</div><div class="value">${d.msg_type}</div>${aiInfo}`;
    }
    tooltip.innerHTML = html;
    tooltip.style.opacity = 1;
  })
  .on('mousemove', e => {
    tooltip.style.left = (e.clientX + 14) + 'px';
    tooltip.style.top = (e.clientY - 10) + 'px';
  })
  .on('mouseout', () => { tooltip.style.opacity = 0; });

function getNodePos(id) {
  return simNodes.find(n => n.id === id);
}

function updateGroups() {
  const padding = 45;
  const groupData = packages.map(pkg => {
    const members = packageMap[pkg]
      .map(name => getNodePos(name))
      .filter(n => n && n.x != null);

    if (members.length === 0) return null;

    const xs = members.map(n => n.x);
    const ys = members.map(n => n.y);
    const x = Math.min(...xs) - padding;
    const y = Math.min(...ys) - padding;
    const w = Math.max(...xs) - Math.min(...xs) + padding * 2;
    const h = Math.max(...ys) - Math.min(...ys) + padding * 2;
    return { pkg, x, y, w, h, color: packageColor[pkg] };
  }).filter(Boolean);

  const boxes = groupLayer.selectAll('g.group')
    .data(groupData, d => d.pkg);

  const entered = boxes.enter().append('g').attr('class', 'group');
  entered.append('rect').attr('class', 'group-box');
  entered.append('text').attr('class', 'group-label');

  const merged = entered.merge(boxes);

  merged.select('rect.group-box')
    .attr('x', d => d.x)
    .attr('y', d => d.y)
    .attr('width', d => d.w)
    .attr('height', d => d.h)
    .attr('rx', 12)
    .attr('stroke', d => d.color)
    .attr('fill', d => d.color);

  merged.select('text.group-label')
    .attr('x', d => d.x + 10)
    .attr('y', d => d.y + 16)
    .attr('fill', d => d.color)
    .text(d => d.pkg);

  boxes.exit().remove();
}

sim.on('tick', () => {
  function linkArc(d) {
    const dx = d.target.x - d.source.x;
    const dy = d.target.y - d.source.y;
    const dr = Math.sqrt(dx * dx + dy * dy) * 1.5;
    return `M${d.source.x},${d.source.y}A${dr},${dr} 0 0,1 ${d.target.x},${d.target.y}`;
  }

  link.attr('d', linkArc);
  serviceLink.attr('d', linkArc);

  node.attr('transform', d => `translate(${d.x},${d.y})`);

  updateGroups();
});
</script>
</body>
</html>"""

def build_graph_data(graph: ROS2Graph, workspace: str) -> dict:
    return {
        "workspace": workspace,
        "nodes": [
            {
                "name": n.name,
                "file": n.file,
                "package": _get_package(n.file)
            }
            for n in graph.nodes
        ],
        "topics": [
            {
                "topic": t.topic,
                "msg_type": t.msg_type,
                "publishers": t.publishers,
                "subscribers": t.subscribers,
                "ai_resolved": t.ai_resolved,
                "ai_confidence": t.ai_confidence,
                "ai_publishers": t.ai_publishers,
                "ai_subscribers": t.ai_subscribers
            }
            for t in graph.topics
        ],
        "orphans": [
            {
                "topic": t.topic,
                "msg_type": t.msg_type,
                "publishers": t.publishers,
                "subscribers": t.subscribers
            }
            for t in graph.orphan_topics
        ],
        "services": [
            {
                "name": s.name,
                "srv_type": s.srv_type,
                "servers": s.servers,
                "clients": s.clients
            }
            for s in graph.services
        ]
    }

def _get_package(filepath: str) -> str:
    parts = filepath.split(os.sep)
    for i in range(len(parts) - 1, 0, -1):
        candidate = os.sep.join(parts[:i])
        if os.path.exists(os.path.join(candidate, 'package.xml')):
            return parts[i - 1]
    return 'unknown'

def render(graph: ROS2Graph, workspace: str, output_path: str = "index.html"):
    data = build_graph_data(graph, workspace)
    graph_json = json.dumps(data, indent=2)
    html = TEMPLATE.replace("__GRAPH_DATA__", graph_json)

    with open(output_path, 'w') as f:
        f.write(html)

    print(f"  graph saved to {output_path}")
    return output_path
