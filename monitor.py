"""Read-only QMT market-data adapter. NEVER import trading modules."""
import argparse
import datetime as dt
import json
import time
from pathlib import Path
from zoneinfo import ZoneInfo
from signals import analyze

WATCHLIST = ["300394.SZ", "300502.SZ", "300308.SZ", "688012.SH", "002463.SZ"]
TZ = ZoneInfo("Asia/Shanghai")
SLOTS = {"09:40", "10:30", "13:30", "14:45", "15:30"}

def connect():
    from xtquant import xtdata
    return xtdata

def check(xtdata):
    print("xtdata import OK")
    for code in WATCHLIST[:1]:
        result = xtdata.get_full_tick([code])
        print(json.dumps({"code": code, "has_tick": bool(result and result.get(code))}, ensure_ascii=False))

def download(xtdata):
    for code in WATCHLIST:
        print("Downloading", code)
        xtdata.download_history_data(code, period="1d", start_time="20250101")

def read_bars(xtdata, code):
    result = xtdata.get_market_data_ex(
        field_list=["close", "volume"], stock_list=[code], period="1d",
        count=100, dividend_type="front", fill_data=False)
    frame = result.get(code)
    if frame is None or frame.empty:
        return [], None
    # Exclude today's daily bar while market is open: incomplete candles are not signals.
    now = dt.datetime.now(TZ)
    today = now.strftime("%Y%m%d")
    rows = []
    latest_day = None
    for idx, r in frame.iterrows():
        day = str(idx)[:10].replace("-", "").replace("/", "")
        if len(day) < 8 or not day[:8].isdigit():
            continue
        day = day[:8]
        if day >= today and now.strftime("%H:%M") < "15:05":
            continue
        rows.append({"close": r["close"], "volume": r["volume"]})
        latest_day = day
    return rows, latest_day

def run_once(xtdata):
    now = dt.datetime.now(TZ)
    out = Path("output/signals.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    records = []
    for code in WATCHLIST:
        try:
            rows, latest_day = read_bars(xtdata, code)
            signal = analyze(rows)
            # Staleness: no more than 7 calendar days; market holiday handling is pending.
            if not latest_day or (now.date() - dt.datetime.strptime(latest_day, "%Y%m%d").date()).days > 7:
                signal = {"signal": "NO_DATA", "reason": "missing/stale completed daily bar"}
        except Exception as exc:
            signal = {"signal": "NO_DATA", "reason": "QMT data read failed", "error_type": type(exc).__name__}
            latest_day = None
        record = {"checked_at": now.isoformat(), "bar_date": latest_day, "code": code, **signal}
        records.append(record)
    with out.open("a", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(json.dumps(record, ensure_ascii=False))
    return records

def main():
    p = argparse.ArgumentParser()
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--download", action="store_true")
    mode.add_argument("--once", action="store_true")
    mode.add_argument("--loop", action="store_true")
    args = p.parse_args()
    xtdata = connect()
    if args.check:
        check(xtdata)
    elif args.download:
        download(xtdata)
    elif args.once:
        run_once(xtdata)
    else:
        last = None
        while True:
            now = dt.datetime.now(TZ)
            key = now.strftime("%Y-%m-%d %H:%M")
            if now.weekday() < 5 and now.strftime("%H:%M") in SLOTS and key != last:
                run_once(xtdata)
                last = key
            time.sleep(10)

if __name__ == "__main__":
    main()
