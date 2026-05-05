/* Corpus Index — JS runtime (grid / timeline / table views, search, filtering) */

const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

function fmtDate(d) {
  if (!d) return '—';
  const p = d.split('-');
  if (p.length === 3 && p[2]) return `${months[+p[1]-1]} ${+p[2]}, ${p[0]}`;
  if (p.length >= 2 && p[1]) return `${months[+p[1]-1]} ${p[0]}`;
  return p[0];
}

function elink(href, text, cls) {
  cls = cls || 'elink';
  return href ? `<a href="${href}" target="_blank" rel="noopener" class="${cls}">${text}</a>` : `<span>${text}</span>`;
}

function filtered() {
  const q = (document.getElementById('q').value || '').toLowerCase();
  return DATA.filter(function (a) {
    var tm = activeTheme === 'all' || a.theme === activeTheme;
    var sr = !q || [a.title, a.publisher, a.author, a.desc].concat(a.tags || []).some(function (s) { return s.toLowerCase().indexOf(q) !== -1; });
    return tm && sr;
  });
}

function renderGrid() {
  var items = filtered();
  var g = document.getElementById('grid');
  var nr = document.getElementById('nores');
  g.innerHTML = '';
  nr.style.display = items.length ? 'none' : 'block';
  items.forEach(function (a, i) {
    var col = THEMES[a.theme] ? THEMES[a.theme].color : '#6366F1';
    var card = document.createElement('div');
    card.className = 'card';
    card.style.animationDelay = (i * 0.05) + 's';
    card.onmouseenter = function () { card.style.borderColor = col; };
    card.onmouseleave = function () { card.style.borderColor = ''; };
    var titleHtml = a.file ? '<div class="ctitle"><a href="' + a.file + '">' + escapeHTML(a.title) + '</a></div>' : '<div class="ctitle">' + escapeHTML(a.title) + '</div>';
    var footerHTML = a.file ? '<div class="cfoot-links"><a class="src" href="' + a.file + '" style="color:' + col + '">Open →</a></div>' : '<span style="opacity:.4">Local</span>';
    card.innerHTML =
      '<div class="card-top"><div class="dot" style="background:' + col + '"></div>' + titleHtml + '</div>' +
      '<div class="cmeta"><span style="color:' + col + '">' + escapeHTML(a.publisher || '') + '</span></div>' +
      '<div class="cdesc">' + escapeHTML(a.desc || '') + '</div>' +
      (a.tags ? '<div class="tags">' + a.tags.slice(0,4).map(function (t) { return '<span class="tag">' + escapeHTML(t) + '</span>'; }).join('') + (a.tags.length > 4 ? '<span class="tag">+' + (a.tags.length - 4) + '</span>' : '') + '</div>' : '') +
      '<div class="cfoot"><span>&#128197; ' + fmtDate(a.date) + '</span>' + footerHTML + '</div>';
    g.appendChild(card);
  });
}

function renderTimeline() {
  var items = filtered().slice().sort(function (a, b) { return String(b.date || '').localeCompare(String(a.date || '')); });
  var tv = document.getElementById('tv');
  tv.innerHTML = '';
  items.forEach(function (a, i) {
    var col = THEMES[a.theme] ? THEMES[a.theme].color : '#6366F1';
    var p = a.date.split('-');
    var mo = p[1] ? months[+p[1] - 1] : '';
    var yr = p[0];
    var div = document.createElement('div');
    div.className = 'ti';
    div.style.animationDelay = (i * 0.06) + 's';
    var titleHtml = a.file ? '<a href="' + a.file + '" style="color:inherit;text-decoration:none">' + escapeHTML(a.title) + '</a>' : escapeHTML(a.title);
    div.innerHTML =
      '<div class="tdot" style="background:' + col + ';box-shadow:0 0 0 2px ' + col + '"></div>' +
      '<div class="tcard">' +
        '<div class="tdate"><div class="tmo">' + mo + '</div><div class="tyr">' + yr + '</div></div>' +
        '<div class="tdiv"></div>' +
        '<div class="tcnt">' +
          '<div class="ttitle">' + titleHtml + '</div>' +
          '<div class="tmeta"><span class="tbadge" style="background:' + col + '">' + (THEMES[a.theme] ? THEMES[a.theme].label : a.theme) + '</span>' + escapeHTML(a.publisher || '') + '</div>' +
          '<div class="tdesc">' + escapeHTML(a.desc || '') + '</div>' +
        '</div>' +
        (a.file ? '<a class="tlink" href="' + a.file + '" style="color:' + col + '" title="Open">↗</a>' : '') +
      '</div>';
    tv.appendChild(div);
  });
}

function renderTable() {
  var items = filtered();
  if (sortCol) {
    items = items.slice().sort(function (a, b) {
      var va = a[sortCol] || '', vb = b[sortCol] || '';
      return sortAsc ? va.localeCompare(vb) : vb.localeCompare(va);
    });
  }
  var tb = document.getElementById('tbody');
  tb.innerHTML = '';
  items.forEach(function (a) {
    var col = THEMES[a.theme] ? THEMES[a.theme].color : '#6366F1';
    var tr = document.createElement('tr');
    tr.innerHTML =
      '<td style="font-weight:600;max-width:260px">' + (a.file ? '<a href="' + a.file + '" style="color:' + col + ';text-decoration:none">' + escapeHTML(a.title) + '</a>' : escapeHTML(a.title)) + '</td>' +
      '<td>' + escapeHTML(a.publisher || '') + '<br><span style="color:#94A3B8;font-size:.73rem">' + escapeHTML(a.author || '') + '</span></td>' +
      '<td style="white-space:nowrap;font-size:.8rem">' + fmtDate(a.date) + '</td>' +
      '<td><span class="tbadge2" style="background:' + col + '">' + (THEMES[a.theme] ? THEMES[a.theme].label : a.theme) + '</span></td>' +
      '<td style="max-width:200px">' + (a.tags ? a.tags.slice(0, 3).map(function (t) { return '<span class="tag">' + escapeHTML(t) + '</span>'; }).join(' ') : '') + '</td>' +
      '<td style="white-space:nowrap">' + (a.file ? '<a href="' + a.file + '" style="color:' + col + ';font-size:.78rem;font-weight:600">Open →</a>' : '<span style="color:#CBD5E1;font-size:.75rem">Local</span>') + '</td>';
    tb.appendChild(tr);
  });
}

function render() {
  if (activeView === 'grid') renderGrid();
  else if (activeView === 'timeline') renderTimeline();
  else renderTable();
}

function setTheme(t, btn) {
  activeTheme = t;
  document.querySelectorAll('.pill').forEach(function (p) { p.classList.remove('on'); });
  btn.classList.add('on');
  render();
}

function setView(v) {
  activeView = v;
  document.getElementById('gv').style.display = v === 'grid' ? 'block' : 'none';
  document.getElementById('tv').style.display = v === 'timeline' ? 'block' : 'none';
  document.getElementById('tbv').style.display = v === 'table' ? 'block' : 'none';
  ['g','t','tb'].forEach(function (id) {
    document.getElementById(id + 'Btn').className = 'vbtn' + ({ g: 'grid', t: 'timeline', tb: 'table' }[id] === v ? ' on' : '');
  });
  render();
}

function sortBy(col) {
  if (sortCol === col) sortAsc = !sortAsc;
  else { sortCol = col; sortAsc = true; }
  renderTable();
}

function escapeHTML(str) {
  var div = document.createElement('div');
  div.textContent = str || '';
  return div.innerHTML;
}

/* ── Dynamic directory scanning ──────────────────────────────────── */

function scanDirectory() {
  return new Promise(function (resolve) {
    // Try cached data first
    try {
      var cached = JSON.parse(localStorage.getItem('_idx_cache'));
      if (cached && cached.ts && (Date.now() - cached.ts < 60000)) {
        // Use cache if < 60s old and user hasn't triggered refresh
        if (!sessionStorage.getItem('_idx_force')) {
          resolve(cached.data);
          return;
        }
      }
    } catch(e) {}

    sessionStorage.removeItem('_idx_force');

    // Derive directory URL from the page's own location
    var pageUrl = location.href;
    var dirUrl = pageUrl.substring(0, pageUrl.lastIndexOf('/') + 1);

    fetch(dirUrl)
      .then(function(r) { return r.text(); })
      .then(function(html) {
        var doc = new DOMParser().parseFromString(html, 'text/html');
        var rows = doc.querySelectorAll('table tr');
        var entries = [];
        var THEME_PALETTE = ['#6366F1','#F59E0B','#10B981','#EF4444','#8B5CF6','#06B6D4','#EC4899','#F97316','#14B8A6','#E11D48'];

        rows.forEach(function(tr) {
          var link = tr.querySelector('a');
          if (!link) return;
          var href = link.getAttribute('href') || '';
          // Skip parent dir, hidden files, sort links
          if (href === '../' || /^\?C=/.test(href)) return;
          var name = decodeURIComponent(href.replace(/\/$/, ''));
          if (!name || name.startsWith('._') || name === 'index.html') return;

          var cells = tr.querySelectorAll('td');
          var isDir = href.endsWith('/');
          var sizeStr = cells[1] ? cells[1].textContent.trim() : '';
          var dateStr = cells[2] ? cells[2].textContent.trim() : '';

          // Derive title from filename
          var title = name.replace(/\.html?$/i, '').replace(/[-_]/g, ' ');
          // Capitalize words
          title = title.replace(/\b\w/g, function(c) { return c.toUpperCase(); });

          // Derive theme from first keyword-ish segment
          var parts = name.toLowerCase().replace(/\.html?$/i, '').split(/[-_]/);
          var theme = (parts[0] === 'about' && parts[1]) ? parts[1] : parts[0];

          entries.push({
            title: title,
            publisher: '',
            author: '',
            date: dateStr ? new Date(dateStr).toISOString().split('T')[0] : '',
            theme: theme,
            desc: '',
            tags: [],
            file: name,
            isDir: isDir
          });
        });

        if (entries.length === 0) return;

        // Sort: dirs first, then date desc
        entries.sort(function(a, b) {
          if (a.isDir && !b.isDir) return -1;
          if (!a.isDir && b.isDir) return 1;
          return String(b.date || '').localeCompare(String(a.date || ''));
        });

        // Build dynamic theme map
        var themeMap = { all: { label: 'All', color: '#6366F1', count: entries.length }};
        entries.forEach(function(e) {
          var t = e.theme || 'general';
          if (!themeMap[t]) themeMap[t] = { label: t.replace(/\b\w/g, function(c){return c.toUpperCase();}), color: THEME_PALETTE[Object.keys(themeMap).length % THEME_PALETTE.length], count: 0 };
          themeMap[t].count++;
        });

        // Cache
        try {
          localStorage.setItem('_idx_cache', JSON.stringify({ ts: Date.now(), data: entries, themes: themeMap }));
        } catch(e) {}

        resolve({ entries: entries, themes: themeMap });
      })
      .catch(function() {
        resolve(null); // fallback to static DATA
      });
  });
}

function applyDynamicData(result) {
  if (!result) return;
  DATA = result.entries;
  THEMES = result.themes;

  // Rebuild theme pills
  var pillsContainer = document.querySelector('.pills');
  if (pillsContainer) {
    var html = '<button class="pill on" data-t="all" onclick="setTheme(\'all\',this)">All</button>';
    Object.keys(THEMES).forEach(function(t) {
      if (t === 'all') return;
      html += '<button class="pill" data-t="' + t + '" onclick="setTheme(\'' + t + '\',this)">' + THEMES[t].label + ' (' + THEMES[t].count + ')</button>';
    });
    pillsContainer.innerHTML = html;
  }

  // Update stats
  var dates = DATA.map(function(e) { return e.date; }).filter(Boolean).sort();
  var statNum = document.querySelector('.stat-num');
  var statLbls = document.querySelectorAll('.stat-lbl');
  if (statNum) statNum.textContent = DATA.length;
  if (statLbls.length > 1 && dates.length > 1) statLbls[1].parentNode.querySelector('.stat-num').textContent = dates.length > 1 ? (dates[0] + ' to ' + dates[dates.length-1]) : '—';

  activeTheme = 'all';
  render();
}

document.addEventListener('visibilitychange', function () {
  if (!document.hidden) {
    sessionStorage.setItem('_idx_force', '1');
    location.reload();
  }
});

// Init: scan directory then render
scanDirectory().then(applyDynamicData).then(function() {
  // If scan failed, render static DATA
  if (!DATA || DATA.length === 0) return;
  render();
});
