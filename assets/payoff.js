// ---------- options payoff & trade lifecycle helpers (shared by app.js) ----------

// Standard payoff at expiration for a position built from stock/call/put legs.
// Returns P&L per share/contract (already nets entry price / premium per leg).
function payoff(legs, netCostBasis, S) {
  let total = 0;
  for (const leg of legs) {
    if (leg.type === 'stock') {
      total += leg.side === 'long' ? (S - leg.entryPrice) : (leg.entryPrice - S);
    } else if (leg.type === 'call') {
      const intrinsic = Math.max(S - leg.strike, 0);
      total += leg.side === 'long' ? (intrinsic - leg.premium) : (leg.premium - intrinsic);
    } else if (leg.type === 'put') {
      const intrinsic = Math.max(leg.strike - S, 0);
      total += leg.side === 'long' ? (intrinsic - leg.premium) : (leg.premium - intrinsic);
    }
  }
  return total;
}

// A trade is closed once today has reached its expiration date. Trades with
// no expirationDate (delta-one positions like UNL) stay open indefinitely.
function isTradeClosed(trade, todayISO) {
  return !!trade.expirationDate && todayISO >= trade.expirationDate;
}

// Latest checkpoint on or before targetISO. Checkpoints are assumed sorted
// ascending by date, as they are throughout trades.json.
function checkpointOnOrBefore(checkpoints, targetISO) {
  let best = null;
  for (const cp of checkpoints) {
    if (cp.date <= targetISO) best = cp;
    else break;
  }
  return best;
}

// Whole-day distance from todayISO to targetISO (positive = in the future).
function daysUntil(targetISO, todayISO) {
  const target = new Date(targetISO + 'T00:00:00');
  const today = new Date(todayISO + 'T00:00:00');
  return Math.round((target - today) / 86400000);
}
