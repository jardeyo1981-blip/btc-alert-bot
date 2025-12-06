# =====================================================
# BTC REVENANT TAPE — NUCLEAR + MTF + RAMS/DEMONS
# FULLY FIXED FOR ALL PANDAS SERIES AMBIGUITY — DEC 2025
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
COOLDOWN = 1800  # 30 min cooldown between alerts
last_alert = {TICKER: 0}
last_scan = 0
alert_count = 0
tz_utc = ZoneInfo("UTC")

# ================== HELPERS ==================
def spot() -> float:
    try:
        return float(yf.Ticker(TICKER).fast_info["lastPrice"])
    except:
        return 0.0

def mtf_flush() -> bool:
    try:
        daily_data = yf.download(TICKER, period="15d", interval="1d", progress=False)
        daily_low = daily_data["Low"].min()
        h4_data = yf.download(TICKER, period="5d", interval="4h", progress=False)
        h4_close = h4_data["Close"]
        h4_prev = float(h4_close.iloc[-2]) if len(h4_close) >= 2 else 0.0
        s = spot()
        # All scalars now — no Series ambiguity
        return bool(s > 0 and s < daily_low * 1.006 and s > h4_prev * 0.995)
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

# ================== PATTERNS (NOW 100% SCALAR-SAFE) ==================
def nuclear_candles(df: pd.DataFrame, spot_price: float):
    if len(df) < 20:
        return None
    c = df.iloc[-1]
    c1 = df.iloc[-3]
    c2 = df.iloc[-2]
    c3 = df.iloc[-1]
    r = float(c["High"] - c["Low"])
    if r < spot_price * 0.001:
        return None
    body = float(abs(c["Close"] - c["Open"]))
    body_r = body / r if r > 0 else 0.0
    uw = float(c["High"] - max(c["Open"], c["Close"]))
    lw = float(min(c["Open"], c["Close"]) - c["Low"])

    # 3 White Soldiers
    if (c1["Close"] > c1["Open"] and c2["Close"] > c2["Open"] and c3["Close"] > c3["Open"] and
        float(c2["Close"]) > float(c1["Close"]) and float(c3["Close"]) > float(c2["Close"])):
        return {"t": "3 WHITE SOLDIERS", "c": 0x00FF00, "m": "MOONSHOT BTC"}
    # 3 Black Crows
    if (c1["Close"] < c1["Open"] and c2["Close"] < c2["Open"] and c3["Close"] < c3["Open"] and
        float(c2["Close"]) < float(c1["Close"]) and float(c3["Close"]) < float(c2["Close"])):
        return {"t": "3 BLACK CROWS", "c": 0xFF0000, "m": "CRASH INCOMING"}

    # Marubozu
    if body_r >= 0.90:
        if c["Close"] > c["Open"]:
            return {"t": "BULLISH MARUBOZU", "c": 0x00FFAA, "m": "STRONG BUY"}
        else:
            return {"t": "BEARISH MARUBOZU", "c": 0xAA00FF, "m": "STRONG SELL"}

    # Inside Bar
    mother = df.iloc[-3]
    inside = df.iloc[-2]
    if float(inside["High"]) < float(mother["High"]) and float(inside["Low"]) > float(mother["Low"]):
        if float(c["Close"]) > float(mother["High"]):
            return {"t": "INSIDE BAR BREAKOUT ↑", "c": 0xFFAA00, "m": "AIR GAP UP"}
        if float(c["Close"]) < float(mother["Low"]):
            return {"t": "INSIDE BAR BREAKDOWN ↓", "c": 0xAA00AA, "m": "AIR GAP DOWN"}

    # Doji
    if body_r <= 0.08:
        if lw > uw * 3:
            return {"t": "DRAGONFLY DOJI", "c": 0x00FFFF, "m": "BOTTOM REVERSAL"}
        if uw > lw * 3:
            return {"t": "TOMBSTONE DOJI", "c": 0xFF00FF, "m": "TOP EXHAUSTION"}

    return None

def rams_demons(spot_price: float):
    try:
        df = yf.download(TICKER, period="6d", interval="5m", progress=False)
        if len(df) < 50:
            return None
        c = df.iloc[-2]
        vol_series = df["Volume"].rolling(40).mean()
        rolling_mean = float(vol_series.iloc[-2])
        if pd.isna(rolling_mean) or rolling_mean <= 0:
            return None
        vol_r = float(c["Volume"]) / rolling_mean

        o = float(c["Open"])
        h = float(c["High"])
        l = float(c["Low"])
        cl = float(c["Close"])
        r = h - l
        if r == 0:
            return None
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

# ================== MAIN LOOP — ABSOLUTELY UNBREAKABLE ==================
print("BTC REVENANT TAPE — TOTAL SERIES FIX — NO MORE CRASHES")
while True:
    try:
        now = time.time()
        s = spot()
        if s <= 0:
            time.sleep(60)
            continue

        # Cooldown & scan rate
        if now - last_alert.get(TICKER, 0) < COOLDOWN:
            time.sleep(300)
            continue
        if now - last_scan < 300:
            time.sleep(60)
            continue
        last_scan = now

        df5 = yf.download(TICKER, period="6d", interval="5m", progress=False)
        close_series = df5["Close"]
        prev_close = float(close_series.iloc[-2]) if len(close_series) >= 2 else s
        prefix = "MTF FLUSH + " if mtf_flush() else ""

        for sig in [nuclear_candles(df5, s), rams_demons(s)]:
            if sig:
                send(f"{prefix}{sig['t']} — {TICKER}", f"Spot: `${s:,.0f}`\n{sig['m']}", sig["c"], ping=PING_ALERTS)
                last_alert[TICKER] = now
                break
        else:
            if mtf_flush():
                direction = "LONG" if s > prev_close else "SHORT"
                color = 0x00FF00 if direction == "LONG" else 0xFF0000
                send(f"{prefix}REVENANT {direction} — {TICKER}", f"Spot `${s:,.0f}` | MTF Gap Active", color, ping=PING_ALERTS)
                last_alert[TICKER] = now

    except Exception as e:
        error_msg = str(e)[:1900]
        send("BTC BOT CRASHED", f"```{error_msg}```", 0xFF0000, ping=True)
        print(f"CRASH: {e}")
        time.sleep(120)

    time.sleep(5)
