"""Fetch daily closing prices from Alpha Vantage into per-ticker CSVs.

Writes Date,Open,High,Low,Close,Volume ascending - the layout
rebuild_checkpoints.py consumes - so the vendor can be swapped without
touching the rebuild step.

The ticker list is derived from data/trades.json rather than hardcoded, so a
trade added to that file is picked up automatically on the next run.

API key resolution order:
  1. $ALPHA_VANTAGE_API_KEY   (how GitHub Actions supplies it)
  2. --key-file <path>        (local convenience)
The key is never printed, and is redacted from any upstream error message.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRADES = REPO_ROOT / "data" / "trades.json"
DEFAULT_OUT = REPO_ROOT / ".price-cache"
ENV_VAR = "ALPHA_VANTAGE_API_KEY"
SERIES_KEY = "Time Series (Daily)"
API = "https://www.alphavantage.co/query"


def resolve_key(key_file):
    """Return the API key from the environment, else from a file."""
    env_key = (os.environ.get(ENV_VAR) or "").strip()
    if env_key:
        return env_key, f"${ENV_VAR}"
    if key_file:
        path = Path(key_file)
        if not path.exists():
            sys.exit(f"key file not found: {path}")
        file_key = path.read_text(encoding="utf-8").strip()
        if file_key:
            return file_key, str(path)
    sys.exit(
        f"no API key found. Set ${ENV_VAR} (in GitHub Actions, expose the "
        f"repository secret as an env var on the step) or pass --key-file."
    )


def tickers_from_trades(trades_path):
    """Unique tickers in trades.json, first-seen order."""
    try:
        trades = json.loads(Path(trades_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit(f"cannot read tickers from {trades_path}: {exc}")
    seen, out = set(), []
    for t in trades:
        tk = t.get("ticker")
        if not tk:
            sys.exit(f"trade for episode {t.get('episode')!r} has no ticker")
        if tk not in seen:
            seen.add(tk)
            out.append(tk)
    if not out:
        sys.exit(f"no tickers found in {trades_path}")
    return out


def fetch_series(ticker, key):
    """Return {date: bar} for a ticker, or raise RuntimeError with a reason."""
    url = API + "?" + urllib.parse.urlencode({
        "function": "TIME_SERIES_DAILY",
        "symbol": ticker,
        "outputsize": "compact",
        "datatype": "json",
        "apikey": key,
    })
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            payload = json.load(resp)
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as exc:
        raise RuntimeError(f"request failed: {type(exc).__name__}: {exc}") from exc

    if SERIES_KEY not in payload:
        # Alpha Vantage reports bad symbols, rate limits and premium gates as a
        # 200 with an explanatory key rather than an HTTP error.
        msg = (payload.get("Information") or payload.get("Note")
               or payload.get("Error Message") or json.dumps(payload)[:300])
        raise RuntimeError(f"no series returned: {msg}")
    return payload[SERIES_KEY]


def write_csv(out_path, series):
    rows = []
    for d in sorted(series):
        bar = series[d]
        try:
            rows.append((d, bar["1. open"], bar["2. high"], bar["3. low"],
                         bar["4. close"], bar["5. volume"]))
        except KeyError as exc:
            raise RuntimeError(f"bar {d} missing field {exc}") from exc
    if not rows:
        raise RuntimeError("series present but empty")
    with open(out_path, "w", encoding="utf-8", newline="") as fh:
        fh.write("Date,Open,High,Low,Close,Volume\n")
        for r in rows:
            fh.write(",".join(r) + "\n")
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trades", default=DEFAULT_TRADES, type=Path,
                    help="trades.json to read the ticker list from")
    ap.add_argument("--out", default=DEFAULT_OUT, type=Path,
                    help="directory to write <TICKER>.csv into")
    ap.add_argument("--key-file", default=None,
                    help=f"file holding the API key (ignored if ${ENV_VAR} is set)")
    ap.add_argument("--sleep", type=float, default=13.0,
                    help="seconds between requests; the free tier allows 5/min")
    args = ap.parse_args()

    key, source = resolve_key(args.key_file)
    tickers = tickers_from_trades(args.trades)
    args.out.mkdir(parents=True, exist_ok=True)
    print(f"key from {source}; {len(tickers)} ticker(s) from {args.trades}")

    failures = []
    for i, tk in enumerate(tickers):
        try:
            rows = write_csv(args.out / f"{tk}.csv", fetch_series(tk, key))
        except RuntimeError as exc:
            failures.append(f"{tk}: {str(exc).replace(key, '<REDACTED>')}")
        else:
            print(f"  {tk:<6} {len(rows):>3} bars  {rows[0][0]} -> {rows[-1][0]}  "
                  f"last close {rows[-1][4]}")
        if i < len(tickers) - 1:
            time.sleep(args.sleep)

    if failures:
        print("\nFAILURES:", file=sys.stderr)
        for f in failures:
            print("  " + f, file=sys.stderr)
        return 1
    print(f"\nall {len(tickers)} ticker(s) fetched into {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
