# Workflow: Adding New Episodes to the MacroVoices Site

This is the standing process for updating macrovoices-desk with new episode content. Point Claude to this file (or paste its contents) at the start of a future session to skip re-explaining the process.

## Trigger
The person uploads either:
- Raw episode transcript(s) (PDF), possibly with a Big Picture Trading chart book, **or**
- An updated copy of `MacroVoices_Summaries_and_Portfolio_Watch.md` with new episode sections already written in

## Steps

**1. Identify what's actually new**
- If given an updated `.md` file, `diff` it against the canonical version already known (the live site's content) rather than assuming the whole file is new — past uploads have been built from stale base copies missing episodes already added (e.g. an upload once started from before 535/536 were added). Only extract episodes not already reflected in the live `data/episodes.json`.
- Check for copy/paste artifacts at episode boundaries (stray duplicated `**Guest:**` lines, missing `---` separators). Confirmed to happen at least once — inspect a few lines around each new episode's start/end before parsing.

**2. If given raw transcripts instead of pre-written summaries**
Write the summary following the established format: numbered `###` sections under `## I. Feature Interview: [Guest]`, a `## II. Market Desk Summary` (or a note that none was included), and a `## III. Weekly Trade Idea` with the trade structure if one exists. Match the tone/depth of existing episode summaries in the doc.

**3. Determine recording dates precisely**
If a dated "Trade of the Week" chart book (Big Picture Trading branded, dated Thursday of that week) is provided, treat that date as authoritative for confirming the actual recording date — chart books are typically dated the day after recording. Use the recording date (not the chart book's publish date) as `dateRec` / `recorded`.

**4. Build two JSON snippet files** (not a full replacement of the live files):
- `new_episodes.json` — array of new episode objects, matching the exact shape of existing entries in `data/episodes.json` (episode, guest, guestRole, hosts, recorded, interviewTitle, interviewBody, marketDeskTitle, marketDeskBody, tradeTitle, tradeBody)
- `new_trades.json` — array of new trade objects for any episode with an actual "Where's the Trade" pick, matching the shape in `data/trades.json` (episode, ticker, name, dateRec, structure, thesis, notes, direction ["long" or "short"], checkpoints [{date, price, label}], entryPrice, latestPrice, changePct)
  - New trades get **one checkpoint only** (the Entry) with `changePct: 0.0` as a placeholder — the automated daily price pipeline (see below) fills in real data on its next scheduled run, no manual backfill needed.
  - Episodes with no trade (guest-only weeks, holiday breaks, etc.) get no trades.json entry — confirm this from the source doc's own explicit "no trade" note rather than assuming a parsing gap.

**5. Hand off to Claude Code for the actual merge + push**, since it has real git/filesystem access this chat environment doesn't. Prompt template:

```
Merge new episode and trade data into the repo.

1. new_episodes.json (attached) contains new episode objects in the exact 
   shape already used in data/episodes.json. Append them to the end of 
   that array, in episode-number order.

2. new_trades.json (attached) contains new trade objects, same shape as 
   data/trades.json, each with a single "Entry" checkpoint and changePct 
   set to 0.0 as a placeholder. Append them to the end of that array.

3. Validate both files are still valid JSON after the merge, with no 
   duplicate episode numbers.

4. Do NOT run the price-fetch/rebuild scripts manually — the scheduled 
   GitHub Action already derives its ticker list from trades.json, so 
   any new tickers get picked up automatically on the next run.

5. Commit as "Add episode(s) [numbers] and new trades ([tickers])" and 
   push to main.
```

**6. Flag anything unusual to the person before/after the push:**
- Any ticker that might not be covered by the price data source (exotic ETFs, crypto trusts like IBIT, thinly-traded names) — worth a note to double check coverage on the next automated run.
- Any episode where the trade structure is unusual (e.g. a single-leg option position rather than stock+hedge) — `entryPrice`/`checkpoints` still track the *underlying's* price for charting purposes; the `structure` field carries the actual position detail.

**7. After push:** Netlify auto-deploys on the git push (no separate deploy step). The next scheduled price-update Action run will backfill real checkpoints for any new tickers.

## Known gotchas encountered so far
- GitHub's web-based drag-and-drop file uploader has, at least once, scrambled file contents/names entirely — prefer Claude Code or GitHub Desktop for any bulk file operations over the raw web uploader.
- `netlify.toml` failures show as "Reading and parsing configuration files" — if that error reappears, check the file wasn't corrupted (curly quotes, wrong content) rather than assuming a real TOML syntax issue.
- `changePct` reflects the **underlying's signed % move**, not true position P&L — collars cap upside, debit spreads don't move dollar-for-dollar with the underlying. A `direction` field ("long"/"short") flips the sign correctly for bearish theses (e.g. TLT bear put spread), but magnitude is still underlying-based, not P&L-based. This is documented in the site's own README as a known simplification.
