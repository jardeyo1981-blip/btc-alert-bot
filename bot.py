   # =====================================================
# BTC REVENANT TAPE — FINAL UNKILLABLE VERSION
# ZERO SERIES → SCALAR CONVERSIONS EVERYWHERE
# =====================================================

import os
import time
import requests
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import yfinance as yf

# ================== CONFIG ==================
WEBHOOK = os.environ["DISCORD_WEBHOOK"]
PING_TAG = f"<@{os.environ.get('DISCORD_USER_ID', '')}>"
PING_ALERTS = os.environ.get("PING_ALERTS", "true").lower() == "true"

TICKER = "BTC-USD"
COOLDOWN = 1800
last_alert = {TICKER: 0}
last_scan = 0
alert_count = 0
tz_utc = ZoneInfo("UTC")

def spot() -> float:
    try:
        return float(yf.Ticker(TICKER).fast_info["lastPrice"])
    except:
        return 0.0

def mtf_flush() -> bool:
    try:
        daily = yf.download(TICKER, period="15d", interval="1d", progress=False, threads=False)
        h4    = yf.download(TICKER, period="5d",  interval="4h", progress=False, threads=False)
        daily_low = float(daily["Low"].min())
        h4_prev   = float(h4["Close"].iloc[-2]) if len(h4) >= 2 else 0.0
        s = spot()
        return s > 0 and s < daily_low * 1.006 and s > h4_prev * 0.995
    except:
        return False

def send(title: str, desc: str = "", color: int = 0x00AAFF, ping: bool = True):
    global alert_count
    alert_count += 1
    requests.post(WEBHOOK, json={
        "content": PING_TAG if ping and os.environ.get("DISCORD_USER_ID") else None,
        "embeds": [{
            "title": title,
            "description": f"{desc}\n\n**Total Alerts Today:** {alert_count}",
            "color": color,
            "thumbnail": {"url": "https://i.imgur.com/5k7tcI3.png"},
            "footer": {"text": datetime.now(tz_utc).strftime("%b %d %H:%M UTC")}
        }]
    })

# ================== 100% SCALAR-SAFE PATTERNS ==================
def nuclear_candles(df: pd.DataFrame, spot_price: float):
    if len(df) < 20: return None

    # Force everything to plain float — no Series left alive
    def scalar(row):
        return {k: float(v) for k, v in row.to_dict().items()}

    c  = scalar(df.iloc[-1])
    c1 = scalar(df.iloc[-3])
    c2 = scalar(df.iloc[-2])
    c3 = scalar(df.iloc[-1])
    mother = scalar(df.iloc[-3])
    inside = scalar(df.iloc[-2])

    r = c["High"] - c["Low"]
    if r < spot_price * 0.001: return None
    body = abs(c["Close"] - c["Open"])
    body_r = body / r if r > 0 else 0

    # 3 White Soldiers / 3 Black Crows
    if (c1["Close"] > c1["Open"] and c2["Close"] > c2["Open"] and c3["Close"] > c3["Open"] and
        c2["Close"] > c1["Close"] and c3["Close"] > c2["Close"]):
        return {"t": "3 WHITE SOLDIERS", "c": 0x00FF00, "m": "MOONSHOT BTC"}
    if (c1["Close"] < c1["Open"] and c2["Close"] < c2["Open"] and c3["Close"] < c3["Open"] and
        c2["Close"] < c1["Close"] and c3["Close"] < c2["Close"]):
        return {"t": "3 BLACK CROWS", "c": 0xFF0000, "m": "CRASH INCOMING"}

    # Marubozu
    if body_r >= 0.90:
        return {"t": "BULLISH MARUBOZU", "c": 0x00FFAA, "m": "STRONG BUY"} if c["Close"] > c["Open"] else \
               {"t": "BEARISH MARUBOZU", "c": 0xAA00FF, "m": "STRONG SELL"}

    # Inside Bar
    if inside["High"] < mother["High"] and inside["Low"] > mother["Low"]:
        if c["Close"] > mother["High"]:
            return {"t": "INSIDE BAR BREAKOUT UP", "c": 0xFFAA00, "m": "AIR GAP UP"}
        if c["Close"] < mother["Low"]:
            return {"t": "INSIDE BAR BREAKDOWN DOWN", "c": 0xAA00AA, "m": "AIR GAP DOWN"}

    # Doji
    uw = c["High"] - max(c["Open"], c["Close"])
    lw = min(c["Open"], c["Close"]) - c["Low"]
    if body_r <= 0.08:
        if lw > uw * 3: return {"t": "DRAGONFLY DOJI", "c": 0x00FFFF, "m": "BOTTOM REVERSAL"}
        if uw > lw * 3: return {"t": "TOMBSTONE DOJI", "c": 0xFF00FF, "m": "TOP EXHAUSTION"}

    return None

def rams_demons(_):
    try:
        df = yf.download(TICKER, period="6d", interval="5m", progress=False, threads=False)
        if len(df) < 50: return None
        c = df.iloc[-2]
        vol_mean = float(df["Volume"].rolling(40).mean().iloc[-2])
        if pd.isna(vol_mean) or vol_mean <= 0: return None
        vol_r = float(c["Volume"]) / vol_mean

        o, h, l, cl = float(c["Open"]), float(c["High"]), float(c["Low"]), float(c["Close"])
        r = h - l
        if r == 0: return None
        body = abs(cl - o)
        uw = h - max(o, cl)
        lw = min(o, cl) - l
        body_pct = body / r

        if lw >= 3 * body and body_pct <= 0.12 and uw <= r * 0.08 and vol_r >= 1.5:
            return {"t": "RAM'S HEAD", "c": 0xFFD700, "m": "BULLISH HAMMER – VOLUME CONFIRMED"}
        if uw >= 3 * body and body_pct <= 0.12 and lw <= r * 0.08 and vol_r >= 1.5:
            return {"t": "DEMON HORNS", "c": 0x8B0000, "m": "BEARISH SHOOTING STAR – VOLUME CONFIRMED"}
        return None
    except:
        return None

# ================== MAIN LOOP ==================
print("BTC REVENANT TAPE — FINAL UNKILLABLE BUILD")
while True:
    try:
        now = time.time()
        s = spot()
        if s <= 0:
            time.sleep(60); continue

        if now - last_alert.get(TICKER, 0) < COOLDOWN:
            time.sleep(300); continue
        if now - last_scan < 300:
            time.sleep(60); continue
        last_scan = now

        df5 = yf.download(TICKER, period="6d", interval="5m", progress=False, threads=False)
        prev_close = float(df5["Close"].iloc[-2]) if len(df5) >= 2 else s
        prefix = "MTF FLUSH + " if mtf_flush() else ""

        for sig in [nuclear_candles(df5, s), rams_demons(s)]:
            if sig:
                send(f"{prefix}{sig['t']} — {TICKER}", f"Spot `${s:,.0f}`\n{sig['m']}", sig["c"], ping=PING_ALERTS)
                last_alert[TICKER] = now
                break
        else:
            if mtf_flush():
                direction = "LONG" if s > prev_close else "SHORT"
                color = 0x00FF00 if direction == "LONG" else 0xFF0000
                send(f"{prefix}REVENANT {direction} — {TICKER}", f"Spot `${s:,.0f}` | MTF Gap Active", color, ping=PING_ALERTS)
                last_alert[TICKER] = now

    except Exception as e:
        send("BTC BOT CRASHED", f"```{str(e)[:1900]}```", 0xFF0000, ping=True)
        print("CRASH:", e)
        time.sleep(120)

    time.sleep(5)
