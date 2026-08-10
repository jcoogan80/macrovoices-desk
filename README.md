# MacroVoices Desk

A static site: an episode log with full summaries, and a "Trades of the Week" tracker with an interactive performance chart.

## Deploy to Netlify

**Easiest — drag and drop:**
1. Go to https://app.netlify.com/drop
2. Drag this whole folder onto the page
3. Done — you'll get a live URL immediately (you can rename it in Site settings → Domain management)

**Via Git (recommended for ongoing updates):**
1. Push this folder to a GitHub/GitLab repo
2. In Netlify: "Add new site" → "Import an existing project" → connect the repo
3. Build command: leave blank. Publish directory: `.`
4. Every push to the repo auto-deploys

No build step is required — this is plain HTML/CSS/JS, so either method works with zero configuration.

## Updating content

All content lives in two JSON files under `data/`:

- **`data/episodes.json`** — one object per episode (guest, date, interview summary, market desk summary, trade write-up). Add a new episode by appending a new object in the same shape.
- **`data/trades.json`** — one object per trade, including a `checkpoints` array of `{date, price, label}` points used to draw the performance chart.

### Adding a new episode + trade
1. Add a new object to `episodes.json` following the existing pattern.
2. Add a matching object to `trades.json` (same `episode` number) with at least an entry checkpoint. Add more checkpoints over time (e.g. weekly closes) to make the chart show real daily/weekly movement instead of a straight interpolated line.
3. Re-deploy (if using drag-and-drop, just drag the folder again; if using Git, just push).

### Important caveat on the performance chart
The chart currently interpolates a straight line between whatever price checkpoints are in `trades.json` — it is **not** pulling live daily closes. Each trade only has the checkpoints that were confirmed in the source transcripts/chart books (usually just an entry price and one later spot-check). To get a true daily-close chart, either:
- Manually add more `{date, price}` checkpoints to `trades.json` as you gather them, or
- Wire up a client-side fetch to a market-data API (e.g. a paid endpoint with CORS support) inside `assets/app.js`'s `drawChart()` function, replacing the `checkpoints` array with real daily OHLC data at render time.

## File structure
```
index.html          — shell page, loads app.js
assets/style.css     — all styling
assets/app.js        — router, rendering, Chart.js chart logic
data/episodes.json   — episode content
data/trades.json     — trade content + chart checkpoints
netlify.toml         — Netlify config (no build step needed)
```
