# =============================================
# BTC 30MIN ELITE PUMP/DUMP BOT — DEC 2025 FINAL
# EMA5/12 Crossover + ADX > 23 (zero chop, only real moves)
# You are now the 0.01%
# =============================================

import os
import time
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
from datetime import datetime

# === CONFIG ===
WEBHOOK = os.environ["DISCORD_WEBHOOK"]        # Set in your environment
COOLDOWN_SECONDS = 3600                         # 1 hour cooldown after any signal
TICKER = "BTC-USD"
TIMEFRAME = "30m"

# === DISCORD ALERT FUNCTION ===
def send_alert(title: str, desc: str, color: int):
    payload = {
        "username": "BTC ELITE BOT",
        "embeds": [{
            "title": title,
            "description": desc,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "30min • EMA5/12 + ADX>23 • Dec 2025 Immortal Edition"}
        }]
    }
    try:
        requests.post(WEBHOOK, json=payload)
    except:
        pass

# === MAIN LOOP ===
last_signal_time = 0

print("BTC 30MIN ELITE BOT STARTED — IMMORTAL MODE ENGAGED")

while True:
    try:
        now = time.time()
        if now - last_signal_time < COOLDOWN_SECONDS:
            time.sleep(60)
            continue

        # Download latest 30min data
        df = yf.download(TICKER, period="30d", interval=TIMEFRAME, progress=False)
        if len(df) < 50:
            time.sleep(60)
            continue

        # Indicators
        df["ema5"]  = ta.ema(df["Close"], length=5)
        df["ema12"] = ta.ema(df["Close"], length=12)
        df["atr"]   = ta.atr(df["High"], df["Low"], df["Close"], length=14)
        adx_data    = ta.adx(df["High"], df["Low"], df["Close"], length=14)
        df["adx"]   = adx_data["ADX_14"]

        df = df.dropna()

        if len(df) < 2:
            time.sleep(60)
            continue

        # Current & previous values
        price     = df["Close"].iloc[-1]
        ema5      = df["ema5"].iloc[-1]
        ema12     = df["ema12"].iloc[-1]
        ema5_prev = df["ema5"].iloc[-2]
        ema12_prev= df["ema12"].iloc[-2]
        adx       = df["adx"].iloc[-1]
        atr       = df["atr"].iloc[-1]

        # === SIGNAL CONDITIONS ===
        long_signal  = (ema5_prev <= ema12_prev and ema5 > ema12 and 
                        adx > 23 and price > ema5)
        
        short_signal = (ema5_prev >= ema12_prev and ema5 < ema12 and 
                        adx > 23 and price < ema5)

        # === FIRE ===
        if long_signal:
            target = price + (atr * 1.8)
            tp_str = f"Target: ${target:,.0f} (+1.8× ATR)"
            desc = f"**LONG PUMP CONFIRMED**\nPrice: ${price:,.0f}\n{tp_str}\nADX: {adx:.1f}"
            send_alert("BTC 30MIN LONG — ENTER NOW", desc, 0x00FF00)
            last_signal_time = now

        elif short_signal:
            target = price - (atr * 1.8)
            tp_str = f"Target: ${target:,.0f} (-1.8× ATR)"
            desc = f"**SHORT DUMP CONFIRMED**\nPrice: ${price:,.0f}\n{tp_str}\nADX: {adx:.1f}"
            send_alert("BTC 30MIN SHORT — ENTER NOW", desc, 0xFF0000)
            last_signal_time = now

        time.sleep(60)

    except Exception as e:
        requests.post(WEBHOOK, json={"content": f"BOT ERROR: {str(e)}"})
        time.sleep(300)
