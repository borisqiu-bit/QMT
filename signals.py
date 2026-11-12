"""Pure deterministic signal engine. No brokerage or network dependencies."""
from statistics import mean

def analyze(rows):
    """rows: oldest-first dictionaries with close, volume. Last bar must be completed."""
    if len(rows) < 61:
        return {"signal": "NO_DATA", "reason": "need at least 61 completed daily bars"}
    try:
        closes = [float(x["close"]) for x in rows]
        vols = [float(x["volume"]) for x in rows]
    except (KeyError, TypeError, ValueError):
        return {"signal": "NO_DATA", "reason": "invalid OHLCV"}
    if any(v <= 0 for v in closes) or any(v < 0 for v in vols):
        return {"signal": "NO_DATA", "reason": "nonpositive price or negative volume"}
    c = closes[-1]
    ma20, ma60 = mean(closes[-20:]), mean(closes[-60:])
    prior20max = max(closes[-21:-1])
    prior20volume = mean(vols[-21:-1])
    if c > prior20max and prior20volume > 0 and vols[-1] >= 1.5 * prior20volume:
        sig, reason = "BREAKOUT_WATCH", "close broke previous 20-day closing high with >=1.5x prior average volume"
    elif c < ma20:
        sig, reason = "WEAKNESS", "close below MA20"
    elif c > ma20 > ma60 and c > ma60:
        sig, reason = "UPTREND", "close above MA20/MA60 and MA20 above MA60"
    else:
        sig, reason = "HOLD_WATCH", "no qualified breakout or weakness"
    return {"signal": sig, "reason": reason, "close": round(c, 4),
            "ma20": round(ma20, 4), "ma60": round(ma60, 4),
            "prior20_high": round(prior20max, 4),
            "volume_ratio": round(vols[-1] / prior20volume, 3) if prior20volume else None}
