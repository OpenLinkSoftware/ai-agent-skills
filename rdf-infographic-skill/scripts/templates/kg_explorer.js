(function(global) {
'use strict';

function initKGExplorer(config) {
  var kgData = config.kgData;
  var options = config.options || {};
  var NODE_COLORS = { Class: '#ea580c', Property: '#0ea5e9', Instance: '#059669' };

  // Build degree-based density bridge at runtime
  var KGDATA = (function() {
    var degMap = {};
    kgData.nodes.forEach(function(n) { degMap[n.id] = 0; });
    kgData.links.forEach(function(l) {
      var src = typeof l.source === 'object' ? l.source.id : l.source;
      var tgt = typeof l.target === 'object' ? l.target.id : l.target;
      degMap[src] = (degMap[src] || 0) + 1;
      degMap[tgt] = (degMap[tgt] || 0) + 1;
    });
    var sorted = kgData.nodes.slice().sort(function(a, b) { return (degMap[b.id] || 0) - (degMap[a.id] || 0); });
    var coreNodes = sorted.slice(0, 30);
    var coreIds = new Set(coreNodes.map(function(n) { return n.id; }));
    var coreLinks = kgData.links.filter(function(l) {
      var src = typeof l.source === 'object' ? l.source.id : l.source;
      var tgt = typeof l.target === 'object' ? l.target.id : l.target;
      return coreIds.has(src) && coreIds.has(tgt);
    });
    return {
      core: { nodes: coreNodes, links: coreLinks },
      full: kgData
    };
  })();

  var kgMode = 'basic';
  var kgDensity = 'core';
  var activePredicates = {};
  var activeNodeTypes = { Class: true, Property: true, Instance: true };
  var literalFilter = '';
  var resolverPref = options.resolver || 'uriburner';
  var arrowStyle = 'directed';
  var kgCharge = -300;
  var kgLinkDist = 120;
  var kgPhysics = true;
  var baseIRI = options.baseIRI || 'https://www.linkedin.com/pulse/china-built-super-app-us-may-build-super-agent-jaya-gupta-3ncoc/';
  var resolverPattern = options.resolverPattern || 'https://linkeddata.uriburner.com/describe/?url=';

  function resolveIRI(iri) {
    if (resolverPref === 'none') return null;
    var url;
    if (resolverPref === 'custom') {
      var customPat = document.getElementById('kgResolverCustom');
      var pat = customPat ? customPat.value : resolverPattern;
      url = pat.replace('{uri}', encodeURIComponent(iri));
    } else {
      url = resolverPattern + encodeURIComponent(iri);
    }
    return url;
  }

  function openInResolver(iri) {
    var url = resolveIRI(iri);
    if (url) window.open(url, '_blank', 'noopener,noreferrer');
  }

  function getPredMap() {
    var m = {};
    m['a'] = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type';
    m['type'] = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type';
    m['label'] = 'http://www.w3.org/2000/01/rdf-schema#label';
    m['subClassOf'] = 'http://www.w3.org/2000/01/rdf-schema#subClassOf';
    m['domain'] = 'http://www.w3.org/2000/01/rdf-schema#domain';
    m['range'] = 'http://www.w3.org/2000/01/rdf-schema#range';
    m['seeAlso'] = 'http://www.w3.org/2000/01/rdf-schema#seeAlso';
    m['author'] = 'http://schema.org/author';
    m['hasPart'] = 'http://schema.org/hasPart';
    m['isPartOf'] = 'http://schema.org/isPartOf';
    m['about'] = 'http://schema.org/about';
    m['publisher'] = 'http://schema.org/publisher';
    m['owl:sameAs'] = 'http://www.w3.org/2002/07/owl#sameAs';
    m['rdf:type'] = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type';
    m['rdfs:label'] = 'http://www.w3.org/2000/01/rdf-schema#label';
    return m;
  }

  function resolvePredicateIRI(label) {
    var predMap = getPredMap();
    if (predMap[label]) return predMap[label];
    if (label.indexOf(':') !== -1) {
      var parts = label.split(':');
      var prefix = parts[0];
      var local = parts.slice(1).join(':');
      var prefixMap = {
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
        'owl': 'http://www.w3.org/2002/07/owl#',
        'schema': 'http://schema.org/',
        'xsd': 'http://www.w3.org/2001/XMLSchema#',
        'skos': 'http://www.w3.org/2004/02/skos/core#',
        'dcterms': 'http://purl.org/dc/terms/',
        'foaf': 'http://xmlns.com/foaf/0.1/'
      };
      if (prefixMap[prefix]) return prefixMap[prefix] + local;
    }
    return baseIRI + label;
  }

  function renderKG() {
    var svg = document.getElementById('kgSvg');
    if (!svg) return;
    var container = svg.parentElement;
    var width = container.clientWidth || 800;
    var height = 500;
    svg.setAttribute('width', width);
    svg.setAttribute('height', height);
    svg.setAttribute('viewBox', '0 0 ' + width + ' ' + height);

    var sourceData = kgDensity === 'core' ? KGDATA.core : KGDATA.full;
    var activeNodeIds = new Set();
    var filteredNodes = sourceData.nodes.filter(function(n) {
      if (!activeNodeTypes[n.group]) return false;
      if (literalFilter && n.label && n.label.toLowerCase().indexOf(literalFilter) === -1 && n.id.toLowerCase().indexOf(literalFilter) === -1) return false;
      activeNodeIds.add(n.id);
      return true;
    });

    var filteredLinks = sourceData.links.filter(function(l) {
      if (!activePredicates[l.predicate]) return false;
      var src = typeof l.source === 'object' ? l.source.id : l.source;
      var tgt = typeof l.target === 'object' ? l.target.id : l.target;
      return activeNodeIds.has(src) && activeNodeIds.has(tgt);
    });

    var nodeCount = document.getElementById('kgNodeCount');
    var linkCount = document.getElementById('kgLinkCount');
    if (nodeCount) nodeCount.textContent = 'Nodes: ' + filteredNodes.length;
    if (linkCount) linkCount.textContent = 'Links: ' + filteredLinks.length;

    svg.innerHTML = '';
    var defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');

    function createMarker(id, refX, color) {
      var m = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
      m.setAttribute('id', id);
      m.setAttribute('viewBox', '0 -5 10 10');
      m.setAttribute('refX', refX);
      m.setAttribute('refY', 0);
      m.setAttribute('markerWidth', 8);
      m.setAttribute('markerHeight', 8);
      m.setAttribute('orient', 'auto');
      var p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      p.setAttribute('d', 'M0,-5L10,0L0,5');
      p.setAttribute('fill', color || '#94A3B8');
      m.appendChild(p);
      return m;
    }
    defs.appendChild(createMarker('arrow-end', 20));
    svg.appendChild(defs);

    var g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    window._kgG = g;

    var linkGroups = filteredLinks.map(function(l) {
      var src = typeof l.source === 'object' ? l.source.id : l.source;
      var tgt = typeof l.target === 'object' ? l.target.id : l.target;
      return { source: src, target: tgt, predicate: l.predicate, label: l.label || l.predicate };
    });

    var d3 = global.d3;
    if (!d3) return;

    var sim = d3.forceSimulation(filteredNodes)
      .force('link', d3.forceLink(linkGroups).id(function(d) { return d.id; }).distance(kgLinkDist))
      .force('charge', d3.forceManyBody().strength(kgCharge))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide(30));
    window._kgSim = sim;

    var linkLines = d3.select(g).selectAll('line.link-line').data(linkGroups).join('line')
      .attr('stroke', '#94A3B8').attr('stroke-width', 1.5).attr('stroke-opacity', 0.5)
      .attr('marker-end', function(d) { return arrowStyle === 'none' ? null : 'url(#arrow-end)'; });

    var linkGs = d3.select(g).selectAll('g.link-label-group').data(linkGroups).join('g').attr('class', 'link-label-group');
    linkGs.append('text')
      .text(function(d) { return d.label; })
      .attr('font-size', '9').attr('fill', '#94A3B8')
      .attr('text-anchor', 'middle').attr('dy', '-4')
      .style('cursor','pointer')
      .on('click', function(e, d) {
        e.stopPropagation();
        openInResolver(resolvePredicateIRI(d.label));
      });

    linkLines.on('click', function(e, d) {
      e.stopPropagation();
      openInResolver(resolvePredicateIRI(d.label));
    });

    var nodesG = d3.select(g).selectAll('g.node-group').data(filteredNodes).join('g').attr('class', 'node-group')
      .call(d3.drag().clickDistance(6)
        .on('start', function(e, d) {
          if (!e.active) sim.alphaTarget(0.3).restart();
          d.fx = d.x; d.fy = d.y;
        })
        .on('drag', function(e, d) { d.fx = e.x; d.fy = e.y; })
        .on('end', function(e, d) {
          if (!e.active) sim.alphaTarget(0);
        })
      )
      .on('dblclick', function(e, d) {
        if (d.fx != null) { d.fx = null; d.fy = null; }
        else { d.fx = d.x; d.fy = d.y; }
      });

    nodesG.on('click', function(e, d) {
      e.stopPropagation();
      openInResolver(d.id);
    });

    nodesG.append('circle')
      .attr('r', function(d) { return d.group === 'Class' ? 12 : d.group === 'Property' ? 8 : 10; })
      .attr('fill', function(d) { return NODE_COLORS[d.group] || '#94A3B8'; })
      .attr('stroke', '#fff').attr('stroke-width', 2);

    nodesG.append('text')
      .text(function(d) { return d.label; })
      .attr('font-size', '10')
      .attr('dx', 15).attr('dy', 4)
      .attr('fill', 'var(--text)')
      .style('pointer-events', 'none');

    svg.appendChild(g);

    sim.on('tick', function() {
      linkLines.attr('x1', function(d) { return d.source.x; }).attr('y1', function(d) { return d.source.y; })
        .attr('x2', function(d) { return d.target.x; }).attr('y2', function(d) { return d.target.y; });
      linkGs.select('text').attr('x', function(d) { return (d.source.x + d.target.x) / 2; }).attr('y', function(d) { return (d.source.y + d.target.y) / 2; });
      nodesG.attr('transform', function(d) { return 'translate(' + d.x + ',' + d.y + ')'; });
    });

    function activateZoom() {
      var svgEl = document.getElementById('kgSvg');
      var explorer = document.getElementById('kg-explorer');
      if (!window._kgZoom) {
        window._kgZoom = d3.zoom().scaleExtent([0.2, 4]).on('zoom', function(e) {
          if (window._kgG) d3.select(window._kgG).attr('transform', e.transform);
        });
      }
      d3.select(svgEl).call(window._kgZoom);
      explorer.classList.add('kg-active');
    }
    function deactivateZoom() {
      var svgEl = document.getElementById('kgSvg');
      var explorer = document.getElementById('kg-explorer');
      d3.select(svgEl).on('.zoom', null);
      explorer.classList.remove('kg-active');
    }

    svg.addEventListener('click', function(e) {
      if (e.target === svg || e.target.tagName === 'svg') activateZoom();
    });
    document.addEventListener('click', function(e) {
      var explorer = document.getElementById('kg-explorer');
      if (!explorer.contains(e.target) && explorer.classList.contains('kg-active')) deactivateZoom();
    });
  }

  function init() {
    var predSet = {};
    KGDATA.full.links.forEach(function(l) { predSet[l.predicate] = true; });
    Object.keys(predSet).forEach(function(p) { activePredicates[p] = true; });

    var predFilters = document.getElementById('pred-filters');
    if (predFilters) {
      predFilters.innerHTML = '';
      Object.keys(predSet).forEach(function(p) {
        var lbl = document.createElement('label');
        var cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.checked = true;
        cb.addEventListener('change', function() {
          activePredicates[p] = cb.checked;
          renderKG();
        });
        lbl.appendChild(cb);
        lbl.appendChild(document.createTextNode(p));
        predFilters.appendChild(lbl);
      });
    }

    function wireAllNone(setObj, containerId, checked) {
      document.querySelectorAll('#' + containerId + ' input[type=checkbox]').forEach(function(cb) {
        cb.checked = checked;
      });
      Object.keys(setObj).forEach(function(k) { setObj[k] = checked; });
      renderKG();
    }

    var setPredAll = document.getElementById('setPredAll');
    if (setPredAll) setPredAll.addEventListener('click', function() { wireAllNone(activePredicates, 'pred-filters', true); });
    var setPredNone = document.getElementById('setPredNone');
    if (setPredNone) setPredNone.addEventListener('click', function() { wireAllNone(activePredicates, 'pred-filters', false); });

    var chipContainer = document.getElementById('node-type-chips');
    if (chipContainer) {
      chipContainer.innerHTML = '';
      ['Class', 'Property', 'Instance'].forEach(function(t) {
        var btn = document.createElement('button');
        btn.textContent = t;
        btn.setAttribute('aria-pressed', 'true');
        btn.setAttribute('data-type', t);
        btn.style.borderColor = NODE_COLORS[t];
        btn.style.background = NODE_COLORS[t];
        btn.style.color = '#fff';
        btn.addEventListener('click', function() {
          var pressed = btn.getAttribute('aria-pressed') === 'true';
          activeNodeTypes[t] = !pressed;
          btn.setAttribute('aria-pressed', String(!pressed));
          btn.style.background = activeNodeTypes[t] ? NODE_COLORS[t] : 'transparent';
          btn.style.color = activeNodeTypes[t] ? '#fff' : NODE_COLORS[t];
          renderKG();
        });
        chipContainer.appendChild(btn);
      });
    }

    function setNodeTypeAll(val) {
      document.querySelectorAll('#node-type-chips button').forEach(function(btn) {
        var t = btn.getAttribute('data-type');
        activeNodeTypes[t] = val;
        btn.setAttribute('aria-pressed', String(val));
        btn.style.background = val ? NODE_COLORS[t] : 'transparent';
        btn.style.color = val ? '#fff' : NODE_COLORS[t];
      });
      renderKG();
    }
    var ntAll = document.getElementById('setNodeTypeAllBtn');
    if (ntAll) ntAll.addEventListener('click', function() { setNodeTypeAll(true); });
    var ntNone = document.getElementById('setNodeTypeNoneBtn');
    if (ntNone) ntNone.addEventListener('click', function() { setNodeTypeAll(false); });

    var litFilter = document.getElementById('literal-filter');
    if (litFilter) {
      litFilter.addEventListener('input', function() {
        literalFilter = this.value.toLowerCase();
        renderKG();
      });
    }

    var chargeSlider = document.getElementById('kgCharge');
    if (chargeSlider) {
      chargeSlider.addEventListener('input', function() {
        kgCharge = +this.value;
        if (window._kgSim) {
          window._kgSim.force('charge').strength(kgCharge);
          window._kgSim.alpha(0.3).restart();
        }
      });
    }
    var distSlider = document.getElementById('kgLinkDist');
    if (distSlider) {
      distSlider.addEventListener('input', function() {
        kgLinkDist = +this.value;
        if (window._kgSim) {
          window._kgSim.force('link').distance(kgLinkDist);
          window._kgSim.alpha(0.3).restart();
        }
      });
    }
    var physSelect = document.getElementById('kgPhysics');
    if (physSelect) {
      physSelect.addEventListener('change', function() {
        kgPhysics = this.value === '1';
        if (window._kgSim) {
          if (kgPhysics) window._kgSim.alpha(0.3).restart();
          else window._kgSim.stop();
        }
      });
    }
    var resolverSelect = document.getElementById('kgResolver');
    if (resolverSelect) {
      resolverSelect.addEventListener('change', function() {
        resolverPref = this.value;
        var customInput = document.getElementById('kgResolverCustom');
        if (customInput) customInput.disabled = this.value !== 'custom';
      });
    }
    var arrowSelect = document.getElementById('kgArrowStyle');
    if (arrowSelect) {
      arrowSelect.addEventListener('change', function() { arrowStyle = this.value; renderKG(); });
    }

    var settingsBtn = document.getElementById('kgSettingsBtn');
    var settingsPanel = document.getElementById('kgSettingsPanel');
    var settingsClose = document.getElementById('kgSettingsClose');
    var settingsWrapper = document.getElementById('settings-panel');
    if (settingsBtn && settingsPanel) {
      settingsBtn.addEventListener('click', function() {
        if (settingsWrapper) settingsWrapper.style.display = 'block';
        settingsPanel.classList.toggle('open');
        settingsBtn.setAttribute('aria-expanded', settingsPanel.classList.contains('open'));
      });
    }
    if (settingsClose && settingsPanel) {
      settingsClose.addEventListener('click', function() {
        settingsPanel.classList.remove('open');
        if (settingsBtn) settingsBtn.setAttribute('aria-expanded', 'false');
        if (settingsBtn) settingsBtn.focus();
      });
    }

    var basicBtn = document.getElementById('kgModeBasic');
    var advBtn = document.getElementById('kgModeAdvanced');
    if (basicBtn) {
      basicBtn.addEventListener('click', function() {
        kgMode = 'basic';
        basicBtn.className = 'active';
        basicBtn.style.background = 'var(--primary)';
        basicBtn.style.color = '#fff';
        if (advBtn) { advBtn.className = ''; advBtn.style.background = 'var(--card-bg)'; advBtn.style.color = 'var(--text)'; }
        document.querySelectorAll('[data-advanced-control]').forEach(function(el) { el.hidden = true; });
        if (settingsPanel) settingsPanel.classList.remove('open');
        if (settingsWrapper) settingsWrapper.style.display = 'none';
        renderKG();
      });
    }
    if (advBtn) {
      advBtn.addEventListener('click', function() {
        kgMode = 'advanced';
        advBtn.className = 'active';
        advBtn.style.background = 'var(--primary)';
        advBtn.style.color = '#fff';
        if (basicBtn) { basicBtn.className = ''; basicBtn.style.background = 'var(--card-bg)'; basicBtn.style.color = 'var(--text)'; }
        document.querySelectorAll('[data-advanced-control]').forEach(function(el) { el.hidden = false; });
        if (settingsWrapper) settingsWrapper.style.display = 'block';
        renderKG();
      });
    }

    var coreBtn = document.getElementById('kgDensityCore');
    var fullBtn = document.getElementById('kgDensityFull');
    function setDensity(d) {
      kgDensity = d;
      if (coreBtn && fullBtn) {
        if (d === 'core') {
          coreBtn.style.background = 'var(--primary)'; coreBtn.style.color = '#fff';
          fullBtn.style.background = 'var(--card-bg)'; fullBtn.style.color = 'var(--text)';
        } else {
          fullBtn.style.background = 'var(--primary)'; fullBtn.style.color = '#fff';
          coreBtn.style.background = 'var(--card-bg)'; coreBtn.style.color = 'var(--text)';
        }
      }
      renderKG();
    }
    if (coreBtn) coreBtn.addEventListener('click', function() { setDensity('core'); });
    if (fullBtn) fullBtn.addEventListener('click', function() { setDensity('full'); });

    var ctrlBtn = document.getElementById('kgControlsBtn');
    if (ctrlBtn) {
      ctrlBtn.addEventListener('click', function() {
        document.getElementById('kgToolbar').classList.toggle('open');
      });
    }

    var fullscreenBtn = document.getElementById('kgFullscreenBtn');
    if (fullscreenBtn) {
      fullscreenBtn.addEventListener('click', function() {
        var el = document.getElementById('kg-explorer');
        if (document.fullscreenElement) document.exitFullscreen();
        else el.requestFullscreen().catch(function() {});
      });
    }

    var centerBtn = document.getElementById('kgCenterBtn');
    if (centerBtn) {
      centerBtn.addEventListener('click', function() {
        if (window._kgSim) {
          var s = document.getElementById('kgSvg');
          var w = +s.getAttribute('width'), h = +s.getAttribute('height');
          if (window._kgG) window._kgG.setAttribute('transform', 'translate(' + w / 2 + ',' + h / 2 + ')');
          window._kgSim.alpha(0.3).restart();
        }
      });
    }

    renderKG();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
}

global.initKGExplorer = initKGExplorer;
})(typeof window !== 'undefined' ? window : this);
