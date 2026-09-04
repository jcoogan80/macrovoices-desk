"""Rebuild trades.json checkpoints from daily closing price data.

Source-agnostic: reads one CSV per ticker from --prices, in the layout
Date,Open,High,Low,Close,Volume. Any vendor producing that shape works.

Idempotent - it keys off the "Entry" checkpoint and regenerates everything
after it, so re-running on an already-rebuilt file is a no-op when the
underlying price data has not changed. That is what lets the GitHub Action
use `git diff --quiet` to decide whether there is anything to commit.

Behaviour:
  - a trade whose expirationDate has passed is closed; its checkpoints are
    left untouched (no new daily closes appended) and it does not require a
    price CSV to be present
  - the existing "Entry" checkpoint is preserved byte-for-byte
  - every other pre-existing checkpoint is dropped; all fall inside the
    daily-data window, so keeping them would duplicate dates
  - one {"date","price","label":"Daily close"} appended per trading day, in
    chronological order, for dates strictly after the entry date
  - latestPrice = price of most recent checkpoint
  - direction   = "short" for bearish theses (episode 543, TLT bear put
                  spread), "long" otherwise
  - changePct   = signed by direction, 2dp:
                    long  -> (latestPrice - entryPrice) / entryPrice * 100
                    short -> (entryPrice - latestPrice) / entryPrice * 100
                  This is the UNDERLYING's signed move, not position P&L.
  - entryPrice untouched

Refuses to write a partial rebuild: if any trade cannot be resolved, nothing
is written and the exit status is non-zero.
"""
import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRADES = REPO_ROOT / "data" / "trades.json"
DEFAULT_PRICES = REPO_ROOT / ".price-cache"

SHORT_EPISODES = {543}          # 543 = TLT bear put spread (bearish thesis)
DIRECTION_AFTER = "structure"   # key order: direction sits next to structure


def is_closed(trade, today_iso):
    """A trade is closed once today has reached its expirationDate. Trades
    with no expirationDate (e.g. delta-one positions) never count as closed."""
    exp = trade.get("expirationDate")
    return bool(exp) and today_iso >= exp


def signed_change_pct(direction, entry_price, latest):
    """Underlying's signed % move, oriented so positive == thesis working."""
    if direction == "short":
        return round((entry_price - latest) / entry_price * 100, 2)
    return round((latest - entry_price) / entry_price * 100, 2)


def reorder(trade):
    """Return trade with 'direction' positioned right after 'structure'."""
    out = {}
    for k, v in trade.items():
        if k == "direction":
            continue
        out[k] = v
        if k == DIRECTION_AFTER:
            out["direction"] = trade["direction"]
    if "direction" not in out:      # no 'structure' key - fall back to append
        out["direction"] = trade["direction"]
    return out


def load_closes(csv_path):
    """Return sorted [(YYYY-MM-DD, close_float)] from a Stooq-layout CSV."""
    rows = []
    with open(csv_path, newline="", encoding="utf-8-sig") as fh:
        rdr = csv.DictReader(fh)
        missing = {"Date", "Close"} - set(rdr.fieldnames or [])
        if missing:
            raise ValueError(
                f"{csv_path.name}: missing column(s) {sorted(missing)}; "
                f"got header {rdr.fieldnames}"
            )
        for r in rdr:
            d, c = (r.get("Date") or "").strip(), (r.get("Close") or "").strip()
            if not d or not c or c in ("-", "N/A"):
                continue
            rows.append((d, float(c)))
    rows.sort(key=lambda t: t[0])
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trades", default=DEFAULT_TRADES, type=Path)
    ap.add_argument("--prices", default=DEFAULT_PRICES, type=Path,
                    help="directory holding <TICKER>.csv files")
    ap.add_argument("--today", default=date.today().isoformat())
    ap.add_argument("--write", action="store_true",
                    help="write changes; otherwise dry-run report only")
    args = ap.parse_args()

    trades = json.loads(args.trades.read_text(encoding="utf-8"))
    problems, report = [], []

    for t in trades:
        tk = t["ticker"]
        cps = t.get("checkpoints") or []

        if is_closed(t, args.today):
            report.append(f"  {tk:<5} closed (expired {t['expirationDate']}) - skipped, checkpoints untouched")
            continue

        entry = next((c for c in cps if c.get("label") == "Entry"), None)
        if entry is None:
            problems.append(f"{tk}: no checkpoint labelled 'Entry'")
            continue
        if cps[0] is not entry:
            problems.append(f"{tk}: 'Entry' is not the first checkpoint")
            continue

        csv_path = args.prices / f"{tk}.csv"
        if not csv_path.exists():
            problems.append(f"{tk}: no price file at {csv_path}")
            continue

        try:
            closes = load_closes(csv_path)
        except (ValueError, OSError) as exc:
            problems.append(f"{tk}: {exc}")
            continue

        entry_date = entry["date"]
        window = [(d, c) for d, c in closes if entry_date < d <= args.today]
        if not window:
            problems.append(
                f"{tk}: price file has no rows after entry {entry_date} "
                f"through {args.today} ({len(closes)} rows total)"
            )
            continue

        dropped = len(cps) - 1
        t["checkpoints"] = [entry] + [
            {"date": d, "price": round(c, 2), "label": "Daily close"}
            for d, c in window
        ]

        entry_price = t["entryPrice"]           # untouched
        latest = t["checkpoints"][-1]["price"]
        t["latestPrice"] = latest
        t["direction"] = "short" if t["episode"] in SHORT_EPISODES else "long"
        t["changePct"] = signed_change_pct(t["direction"], entry_price, latest)

        raw_move = round((latest - entry_price) / entry_price * 100, 2)
        flip = "  [sign flipped vs raw move " f"{raw_move:+.2f}%]" \
            if t["direction"] == "short" else ""
        report.append(
            f"  {tk:<5} {t['direction']:<5} {len(window):>3} daily closes  "
            f"{window[0][0]} -> {window[-1][0]}  "
            f"entry {entry_price} -> latest {latest}  "
            f"chg {t['changePct']:+.2f}%  "
            f"(dropped {dropped} old checkpoint(s)){flip}"
        )

    if problems:
        print("BLOCKED - refusing to write a partial rebuild:", file=sys.stderr)
        for p in problems:
            print("  " + p, file=sys.stderr)
        return 1

    print("\n".join(report))

    trades = [reorder(t) for t in trades]
    out = json.dumps(trades, indent=2, ensure_ascii=False) + "\n"
    json.loads(out)                             # validate before touching disk
    if args.write:
        args.trades.write_text(out, encoding="utf-8")
        print(f"\nwrote {args.trades} ({len(out)} chars), JSON validated")
    else:
        print(f"\ndry run - {len(out)} chars would be written, JSON validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
