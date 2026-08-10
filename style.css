// ---------- tiny markdown-ish renderer (subset: ### headings, **bold**, paragraphs) ----------
function renderBody(md) {
  if (!md) return '';
  const lines = md.split('\n');
  let html = '';
  let para = [];

  function flushPara() {
    if (para.length) {
      const text = para.join(' ').trim();
      if (text) html += `<p>${inline(text)}</p>`;
      para = [];
    }
  }
  function inline(t) {
    return t.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  }

  for (const raw of lines) {
    const line = raw.trim();
    if (line === '' || line === '---') { flushPara(); continue; }
    if (line.startsWith('### ')) {
      flushPara();
      html += `<h3>${inline(line.slice(4))}</h3>`;
    } else if (line.startsWith('*Note:') || line.startsWith('*This')) {
      flushPara();
      html += `<p class="note-line"><em>${inline(line.replace(/^\*|\*$/g, ''))}</em></p>`;
    } else {
      para.push(line);
    }
  }
  flushPara();
  return html;
}

// ---------- data ----------
let EPISODES = [];
let TRADES = [];

async function loadData() {
  if (EPISODES.length && TRADES.length) return;
  const [epRes, trRes] = await Promise.all([
    fetch('data/episodes.json'),
    fetch('data/trades.json')
  ]);
  EPISODES = await epRes.json();
  TRADES = await trRes.json();
}

// ---------- helpers ----------
function fmtDate(iso) {
  const d = new Date(iso + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}
function pctClass(pct) { return pct >= 0 ? 'up' : 'down'; }
function pctStr(pct) { return (pct >= 0 ? '+' : '') + pct.toFixed(1) + '%'; }

function tradeForEpisode(epNum) {
  return TRADES.find(t => t.episode === epNum);
}

// ---------- ticker tape ----------
function renderTape() {
  const items = TRADES.map(t => {
    const cls = pctClass(t.changePct);
    return `<span class="tape-item"><span class="tk">${t.ticker}</span><span class="val ${cls}">${pctStr(t.changePct)}</span></span>`;
  }).join('');
  document.getElementById('tape').innerHTML = items;
  document.getElementById('tape2').innerHTML = items;
}

// ---------- views ----------
function viewEpisodeList() {
  const rows = EPISODES.map(ep => {
    const trade = tradeForEpisode(ep.episode);
    const chip = trade
      ? `<span class="ep-trade-chip"><span class="tk">${trade.ticker}</span> <span class="${pctClass(trade.changePct)}" style="color:inherit">${pctStr(trade.changePct)}</span></span>`
      : `<span class="ep-trade-chip">no trade logged</span>`;
    return `
      <a class="ep-row" href="#/episode/${ep.episode}">
        <span class="ep-num">${ep.episode}</span>
        <span class="ep-info">
          <span class="ep-guest">${ep.guest}</span>
          <span class="ep-role">${ep.guestRole || ''}</span>
        </span>
        <span class="ep-date">${ep.recorded.replace(/\s*\(.*\)$/, '')}</span>
        ${chip}
      </a>`;
  }).join('');

  return `
    <div class="page-head">
      <span class="page-eyebrow">Episode log</span>
      <h1 class="page-title">MacroVoices, tracked weekly</h1>
      <p class="page-desc">Every episode's feature interview, market desk read, and "Where's the Trade" pick — click through for the full writeup, or jump straight to the trade tracker.</p>
    </div>
    <div class="ep-list">${rows}</div>
  `;
}

function viewEpisodeDetail(epNum) {
  const ep = EPISODES.find(e => e.episode === epNum);
  if (!ep) return `<p>Episode not found.</p>`;
  const trade = tradeForEpisode(epNum);

  const tradeCardHtml = trade ? `
    <div class="card trade-card">
      <span class="card-label">Where's the trade</span>
      <div class="trade-ticker-line">
        <span class="trade-ticker-badge">${trade.ticker}</span>
        <span class="trade-change ${pctClass(trade.changePct)}">${pctStr(trade.changePct)} since entry</span>
        <a href="#/trades" style="margin-left:auto; font-family: var(--mono); font-size: 12.5px; color: var(--ink-dim);">View on trade tracker →</a>
      </div>
      ${renderBody(ep.tradeBody)}
    </div>
  ` : `
    <div class="card">
      <span class="card-label">Where's the trade</span>
      <p>No official trade-of-the-week recommendation is available for this episode.</p>
    </div>
  `;

  return `
    <a class="back-link" href="#/episodes">← All episodes</a>
    <div class="ep-detail-head">
      <span class="ep-detail-num">EP ${ep.episode}</span>
      <h1 class="ep-detail-title">${ep.guest}</h1>
    </div>
    <div class="ep-detail-meta">
      ${ep.guestRole ? ep.guestRole + '<span class="sep">·</span>' : ''}${ep.hosts}<span class="sep">·</span>Recorded ${ep.recorded}
    </div>

    <div class="card">
      <span class="card-label">Feature interview${ep.interviewTitle ? ': ' + ep.interviewTitle.replace(/^Feature Interview:\s*/, '') : ''}</span>
      ${renderBody(ep.interviewBody)}
    </div>

    <div class="card">
      <span class="card-label">Market desk</span>
      ${renderBody(ep.marketDeskBody)}
    </div>

    ${tradeCardHtml}
  `;
}

let chartInstance = null;
let selectedTicker = null;

function viewTrades() {
  selectedTicker = selectedTicker || TRADES[0].ticker;

  const stats = TRADES.map(t => `
    <div class="mini-stat ${t.ticker === selectedTicker ? 'selected' : ''}" data-ticker="${t.ticker}" tabindex="0" role="button">
      <span class="tk">${t.ticker}</span>
      <span class="chg ${pctClass(t.changePct)}">${pctStr(t.changePct)}</span>
      <span class="ep">EP ${t.episode}</span>
    </div>
  `).join('');

  const tableRows = TRADES.map(t => `
    <tr>
      <td class="tk-cell">${t.ticker}<br><span style="font-weight:400;color:var(--ink-faint);font-size:12px;">${t.name}</span></td>
      <td><a class="ep-link" href="#/episode/${t.episode}">EP ${t.episode} →</a></td>
      <td class="num-cell">${fmtDate(t.dateRec)}</td>
      <td class="num-cell">$${t.entryPrice.toFixed(2)}</td>
      <td class="num-cell">$${t.latestPrice.toFixed(2)}</td>
      <td class="chg-cell ${pctClass(t.changePct)}">${pctStr(t.changePct)}</td>
      <td class="structure-cell">${t.structure}</td>
    </tr>
  `).join('');

  return `
    <div class="page-head">
      <span class="page-eyebrow">Trade tracker</span>
      <h1 class="page-title">Trades of the Week</h1>
      <p class="page-desc">Every "Where's the Trade" pick, in one place. Click a ticker to see its performance since the entry date.</p>
    </div>

    <div class="trade-summary-grid" id="trade-stats">${stats}</div>

    <div class="chart-panel">
      <div class="chart-panel-head">
        <div>
          <div class="chart-panel-title" id="chart-title"></div>
          <div class="chart-panel-sub" id="chart-sub"></div>
        </div>
        <div class="chart-panel-stat">
          <div class="big" id="chart-big"></div>
          <div class="small" id="chart-small"></div>
        </div>
      </div>
      <div class="chart-canvas-wrap"><canvas id="perf-chart"></canvas></div>
      <div class="chart-note" id="chart-note"></div>
    </div>

    <div class="card" style="padding:0;">
      <div class="trade-table-wrap">
        <table class="trade-table">
          <thead>
            <tr>
              <th>Ticker</th><th>Episode</th><th>Entry date</th><th>Entry</th><th>Latest</th><th>Change</th><th>Structure</th>
            </tr>
          </thead>
          <tbody>${tableRows}</tbody>
        </table>
      </div>
    </div>
  `;
}

function drawChart() {
  const t = TRADES.find(x => x.ticker === selectedTicker);
  if (!t) return;

  document.getElementById('chart-title').textContent = `${t.ticker} — ${t.name}`;
  document.getElementById('chart-sub').textContent = `${t.structure}`;
  const big = document.getElementById('chart-big');
  big.textContent = pctStr(t.changePct);
  big.className = 'big ' + pctClass(t.changePct);
  document.getElementById('chart-small').textContent =
    `$${t.entryPrice.toFixed(2)} → $${t.latestPrice.toFixed(2)}`;

  const hasApprox = t.checkpoints.some(c => c.approx);
  document.getElementById('chart-note').textContent =
    `Plotted from ${t.checkpoints.length} confirmed price checkpoint${t.checkpoints.length > 1 ? 's' : ''} pulled from episode chart books / desk notes` +
    (hasApprox ? ' (one or more dates are approximate where the source quote was undated)' : '') +
    `. Line is interpolated between checkpoints, not a true daily close feed — connect a market-data API to replace with real end-of-day series.`;

  const labels = t.checkpoints.map(c => fmtDate(c.date));
  const data = t.checkpoints.map(c => c.price);
  const isUp = t.changePct >= 0;
  const lineColor = isUp ? '#3ecf8e' : '#f0655a';

  const canvas = document.getElementById('perf-chart');
  if (chartInstance) chartInstance.destroy();
  chartInstance = new Chart(canvas, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: t.ticker,
        data,
        borderColor: lineColor,
        backgroundColor: isUp ? 'rgba(62,207,142,0.08)' : 'rgba(240,101,90,0.08)',
        borderWidth: 2.5,
        pointRadius: 5,
        pointBackgroundColor: lineColor,
        pointBorderColor: '#0b0e12',
        pointBorderWidth: 2,
        fill: true,
        tension: 0.15,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { intersect: false, mode: 'index' },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#161b22',
          borderColor: '#232a34',
          borderWidth: 1,
          titleFont: { family: 'IBM Plex Mono' },
          bodyFont: { family: 'IBM Plex Mono' },
          callbacks: {
            label: (ctx) => `$${ctx.parsed.y.toFixed(2)}  (${t.checkpoints[ctx.dataIndex].label})`
          }
        }
      },
      scales: {
        x: { grid: { color: '#1b212a' }, ticks: { color: '#8b96a5', font: { family: 'IBM Plex Mono', size: 11 } } },
        y: { grid: { color: '#1b212a' }, ticks: { color: '#8b96a5', font: { family: 'IBM Plex Mono', size: 11 } } }
      }
    }
  });
}

function bindTradeStatClicks() {
  document.querySelectorAll('.mini-stat').forEach(el => {
    el.addEventListener('click', () => {
      selectedTicker = el.dataset.ticker;
      document.querySelectorAll('.mini-stat').forEach(x => x.classList.remove('selected'));
      el.classList.add('selected');
      drawChart();
    });
    el.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') el.click();
    });
  });
}

// ---------- router ----------
async function render() {
  await loadData();
  renderTape();

  const hash = window.location.hash || '#/episodes';
  const app = document.getElementById('app');
  const navLinks = document.querySelectorAll('.main-nav a');

  let match;
  if ((match = hash.match(/^#\/episode\/(\d+)/))) {
    app.innerHTML = viewEpisodeDetail(parseInt(match[1], 10));
    navLinks.forEach(l => l.classList.remove('active'));
  } else if (hash.startsWith('#/trades')) {
    app.innerHTML = viewTrades();
    navLinks.forEach(l => l.classList.toggle('active', l.dataset.route === 'trades'));
    bindTradeStatClicks();
    drawChart();
  } else {
    app.innerHTML = viewEpisodeList();
    navLinks.forEach(l => l.classList.toggle('active', l.dataset.route === 'episodes'));
  }

  window.scrollTo({ top: 0, behavior: 'instant' in window ? 'instant' : 'auto' });
}

window.addEventListener('hashchange', render);
window.addEventListener('DOMContentLoaded', render);
