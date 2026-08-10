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
- **`data/trades.json`** — one object per trade: a `direction` (`"long"`/`"short"`), an `entryPrice`/`latestPrice`/`changePct`, and a `checkpoints` array of `{date, price, label}` points used to draw the performance chart. See [How prices and `changePct` work](#how-prices-and-changepct-work).

### Adding a new episode + trade
1. Add a new object to `episodes.json` following the existing pattern.
2. Add a matching object to `trades.json` (same `episode` number) with a `direction` and an `Entry` checkpoint. The daily-close checkpoints after it are generated from a market-data feed, so only the `Entry` point needs to be authored by hand.
3. Re-deploy (if using drag-and-drop, just drag the folder again; if using Git, just push).

## How prices and `changePct` work

### Checkpoints are real daily closes
Each trade's `checkpoints` array is the original `Entry` point (date and price as
recorded from the episode) followed by one `{date, price, label: "Daily close"}`
entry per trading day since entry. These are **unadjusted** end-of-day closes, so
they are not dividend- or distribution-adjusted and are not total-return figures.
Non-trading days are simply absent, so weekends and market holidays leave gaps —
that is expected, not missing data.

### `changePct` is the underlying's move, not position P&L
> **Known simplification, not a bug.** `changePct` is the signed percentage move
> of the **underlying** since entry. It is *not* the profit or loss on the actual
> position.

Every trade carries a `direction` field, `"long"` or `"short"`, and `changePct` is
signed against it so that **positive always means the thesis is working**:

| `direction` | formula |
|---|---|
| `long`  | `(latestPrice - entryPrice) / entryPrice * 100` |
| `short` | `(entryPrice - latestPrice) / entryPrice * 100` |

Without that flip, episode 543 (TLT, a *bear* put spread) would show a gain while
losing money, because a bearish position profits when the underlying falls.

The number still diverges from real P&L wherever the structure doesn't move
dollar-for-dollar with the underlying:

- **Debit spreads** (bull/bear call/put spreads — DBA, VLO, TLT) risk only the net
  debit and cap the gain at the spread width, so percentage moves are geared and
  bounded, not linear.
- **Collars and protective puts** (PAVE, XLV, XLE, LNG, GLD, BOTZ) truncate the
  payoff at the put floor and the call cap, so moves beyond a strike stop
  contributing.
- Behaviour is least linear **near strikes and close to expiry**, where an option's
  delta shifts fastest.

Read `changePct` as "which way, and roughly how far, has the underlying gone" —
consult `structure` for what the position would actually be worth.

## File structure
```
index.html          — shell page, loads app.js
assets/style.css     — all styling
assets/app.js        — router, rendering, Chart.js chart logic
data/episodes.json   — episode content
data/trades.json     — trade content + chart checkpoints
netlify.toml         — Netlify config (no build step needed)
```
