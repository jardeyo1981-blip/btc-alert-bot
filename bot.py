# =====================================================
# BTC REVENANT TAPE — MINIMAL + IMMORTAL EDITION
# ONLY MTF FLUSH + REVENANT — ZERO PANDAS HELL
# =====================================================

import os
import time
import requests
import yfinance as yf
from datetime import datetime
from zoneinfo import ZoneInfo

WEBHOOK = os.environ["DISCORD_WEBHOOK"]
PING_TAG = f"<@{os.environ.get('DISCORD_USER_ID', '')}>"
PING_ALERTS = os.environ.get("PING_ALERTS", "true").lower() == "true"

TICKER = "BTC-USD"
COOLDOWN = 1800
last_alert = 0
alert_count = 0
tz_utc = ZoneInfo("UTC")

def spot() -> float:
    try:
        return float(yf.Ticker(TICKER).fast_info["lastPrice"])
    except:
        return 0.0

def mtf_flush() -> bool:
    try:
        daily = yf.download(TICKER, period="20d", interval="1d", progress=False, threads=False)
        h4    = yf.download(TICKER, period="6d",  interval="4h", progress=False, threads=False)
        if daily.empty or h4.empty:
            return False
        daily_low = float(daily["Low"].min())
        h4_prev   = float(h4["Close"].values[-2]) if len(h4) >= 2 else daily_low
        s = spot()
        return s > 0 and s < daily_low * 1.008 and s > h4_prev * 0.992
    except:
        return False

def send(title: str, desc: str = "", color: int = 0x00FF00):
    global alert_count
    alert_count += 1
    requests.post(WEBHOOK, json={
        "content": PING_TAG if PING_ALERTS and os.environ.get("DISCORD_USER_ID") else None,
        "embeds": [{
            "title": title,
            "description": f"{desc}\n\n**Alerts Today:** {alert_count}",
            "color": color,
            "footer": {"text": datetime.now(tz_utc).strftime("%b %d %H:%M UTC")}
        }]
    })

print("BTC REVENANT TAPE — MINIMAL + IMMORTAL — RUNNING FOREVER")
while True:
    try:
        now = time.time()
        if now - last_alert < COOLDOWN:
            time.sleep(300)
            continue

        s = spot()
        if s <= 0:
            time.sleep(60)
            continue

        df5 = yf.download(TICKER, period="3d", interval="5m", progress=False, threads=False)
        prev_close = float(df5["Close"].values[-2]) if len(df5) >= 2 else s

        if mtf_flush():
            direction = "LONG" if s > prev_close else "SHORT"
            color = 0x00FF00 if direction == "LONG" else 0xFF0000
            send(
                f"MTF REVENANT {direction} — {TICKER}",
                f"Price: ${s:,.0f}\nNear 20-day low + above prior 4h close\n{direction} setup active",
                color
            )
            last_alert = now

    except Exception as e:
        requests.post(WEBHOOK, json={"content": f"BOT CRASHED: {str(e)[:1900]}"})
        time.sleep(120)

    time.sleep(30)  # Check every 30 seconds
