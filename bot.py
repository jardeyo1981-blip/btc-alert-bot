# =====================================================
# BTC REVENANT TAPE — NUCLEAR CANDLES + MTF FOR CRYPTO
# FIXED FOR GITHUB ACTIONS + NO MORE AMBIGUOUS SERIES CRASHES
# =====================================================

import os
import time
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import yfinance as yf
import feedparser

# ================== CONFIG ==================
WEBHOOK = os.environ["DISCORD_WEBHOOK"]
PING_TAG = f"<@{os.environ.get('DISCORD_USER_ID', '')}>"
PING_ALERTS = os.environ.get("PING_ALERTS", "true").lower() == "true"

TICKER = "BTC-USD"
COOLDOWN = 1800  # 30 min
last_alert = {TICKER: 0}
last_scan = last_heartbeat = 0
alert_count = 0
tz_utc = ZoneInfo("UTC")

# ================== HELPERS ==================
def spot():
    try:
        return float(yf.Ticker(TICKER).fast_info['lastPrice'])
    except:
        return 0.0

def mtf_flush():
    try:
        daily_low = yf.download(TICKER, period="15d", interval="1d", progress=False)["Low"].min()
        h4 = yf.download(TICKER, period="5d", interval="4h", progress=False)["Close"]
        h4_prev = float(h4.iloc[-2]) if len(h4) >= 2 else 0
        s = spot()
        return s < daily_low * 1.006 and s > h4_prev * 0.995
    except:
        return False

def get_crypto_catalysts():
    try:
        feed = feedparser.parse("https://cointelegraph.com/rss")
        high = []
        for e in feed.entries[:5]:
            title = e.title.lower()
            if any(k in title for k in ["bitcoin", "btc", "etf", "halving", "regulation"]):
                high.append(e.title.strip()[:70] + "..." if len(e.title) > 70 else e.title)
        return high or ["Quiet on the crypto front"]
    except:
        return ["News feed down"]

def send(title, desc="", color=0x00AAFF, ping=True):
    global alert_count
    alert_count += 1
    requests.post(WEBHOOK, json={
        "content": PING_TAG if ping and os.environ.get('DISCORD_USER_ID') else None,
        "embeds": [{
            "title": title,
            "description": f"{desc}\n**Total Alerts Today:** {alert_count}",
            "color": color,
            "thumbnail": {"url": "https://i.imgur.com/5k7tcI3.png"},
            "footer": {"text": datetime.now(tz_utc).strftime("%b %d %H:%M UTC")}
        }]
    })

# ================== CANDLE PATTERNS (unchanged, already safe) ==================
def nuclear_candles(df, spot):
    if len(df) < 20: return None
    c = df.iloc[-1]
    c1, c2, c3 = df.iloc[-3], df.iloc[-2], df.iloc[-1]
    r = c.High - c.Low
    if r < spot * 0.001: return None
    body = abs(c.Close - c.Open)
    body_r = body / r
    uw = c.High - max(c.Open, c.Close)
    lw = min(c.Open, c.Close) - c.Low

    if all(x.Close > x.Open for x in [c1, c2, c3]) and c2.Close > c1.Close and c3.Close > c2.Close:
        return {"t": "3 WHITE SOLDIERS", "c": 0x00FF00, "m": "MOONSHOT BTC"}
    if all(x.Close < x.Open for x in [c1, c2, c3]) and c2.Close < c1.Close and c3.Close < c2.Close:
        return {"t": "3 BLACK CROWS", "c": 0xFF0000, "m": "CRASH DUMP"}
    if body_r >= 0.90:
        return {"t": "BULLISH MARUBOZU", "c": 0x00FFAA, "m": "LONG BTC"} if c.Close > c.Open else {"t": "BEARISH MARUBOZU", "c": 0xAA00FF, "m": "SHORT BTC"}

    mother, inside = df.iloc[-3], df.iloc[-2]
    if inside.High < mother.High and inside.Low > mother.Low:
        if c.Close > mother.High:
            return {"t": "INSIDE BAR BREAKOUT", "c": 0xFFAA00, "m": "AIR GAP UP"}
        if c.Close < mother.Low:
            return {"t": "INSIDE BAR BREAKDOWN", "c": 0xAA00AA, "m": "AIR GAP DOWN"}

    if body_r <= 0.08:
        if lw > uw * 3: return {"t": "DRAGONFLY DOJI", "c": 0x00FFFF, "m": "BOTTOM REVERSAL"}
        if uw > lw * 3: return {"t": "TOMBSTONE DOJI", "c": 0xFF00FF, "m": "TOP EXHAUSTION"}

    return None

def rams_demons(spot_price):
    try:
        df = yf.download(TICKER, period="6d", interval="5m", progress=False)
        if len(df) < 50: return None
        c = df.iloc[-2]
        o, h, l, cl = c.Open, c.High, c.Low, c.Close
        r = h - l
        if r == 0: return None
        body = abs(cl - o)
        uw = h - max(o, cl)
        lw = min(o, cl) - l
        body_pct = body / r
        vol_r = c.Volume / df.Volume.rolling(40).mean().iloc[-2] if df.Volume.rolling(40).mean().iloc[-2] > 0 else 1

        if lw >= 3 * body and body_pct <= 0.12 and uw <= r * 0.08 and vol_r >= 1.5:
            return {"t": "RAM'S HEAD", "c": 0xFFD700, "m": "BULLISH HAMMER"}
        if uw >= 3 * body and body_pct <= 0.12 and lw <= r * 0.08 and vol_r >= 1.5:
            return {"t": "DEMON HORNS", "c": 0x8B0000, "m": "BEARISH SHOOTING STAR"}
        return None
    except:
        return None

# ================== MAIN LOOP (NOW 100% SAFE) ==================
print("BTC REVENANT TAPE — NUCLEAR + MTF RUNNING – FIXED VERSION")
while True:
    try:
        now = time.time()
        now_utc = datetime.now(tz_utc)
        s = spot()
        if s <= 0:
            time.sleep(60)
            continue

        # Hourly heartbeat
        if now - last_heartbeat > 3600:
            cats = get_crypto_catalysts()
            desc = f"**Spot:** ${s:,.0f}\n**News:** {', '.join(cats[:2])}"
            send("BTC HEARTBEAT", desc, 0x00FF00, ping=False)
            last_heartbeat = now

        if now - last_alert.get(TICKER, 0) < COOLDOWN:
            time.sleep(300)
            continue
        if now - last_scan < 300:
            time.sleep(60)
            continue
        last_scan = now

        df5 = yf.download(TICKER, period="6d", interval="5m", progress=False)

        # FIX 1: Extract scalar values safely
        prev_close = float(df5["Close"].iloc[-2]) if len(df5) >= 2 else s

        prefix = "MTF FLUSH + " if mtf_flush() else ""

        for sig in [nuclear_candles(df5, s), rams_demons(s)]:
            if sig:
                send(f"{prefix}{sig['t']} — {TICKER}", f"Spot: ${s:,.0f}\n{sig['m']}", sig["c"], ping=PING_ALERTS)
                last_alert[TICKER] = now
                break
        else:
            # FIX 2: This line is now safe
            if mtf_flush():
                direction = "LONG" if s > prev_close else "SHORT"
                color = 0x00FF00 if direction == "LONG" else 0xFF0000
                send(f"{prefix}REVENANT {direction} — {TICKER}", f"Spot ${s:,.0f} | MTF Gap Active", color, ping=PING_ALERTS)
                last_alert[TICKER] = now

    except Exception as e:
        send("BTC BOT CRASHED", f"```{str(e)[:1900]}```", 0xFF0000, ping=True)
        print(f"ERROR: {e}")
        time.sleep(60)  # longer sleep on crash

    time.sleep(5)
