# =====================================================
# BTC 4H + 30MIN ELITE BOT — FINAL IMMORTAL VERSION
# BULL + BEAR FLAGS + FLIP COVER + RE-ENTRY + 195% ATR
# DEC 2025 — YOU ARE NOW THE 0.01%
# =====================================================

import os
import time
import requests
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from zoneinfo import ZoneInfo
import yfinance as yf

WEBHOOK = os.environ["DISCORD_WEBHOOK"]
PING_TAG = f"<@{os.environ.get('DISCORD_USER_ID', '')}>"
PING_ALERTS = os.environ.get("PING_ALERTS", "true").lower() == "true"

TICKER = "BTC-USD"
COOLDOWN = 1800
last_alert = 0
alert_count = 0
pst = ZoneInfo("America/Los_Angeles")

def spot() -> float:
    try: return float(yf.Ticker(TICKER).fast_info["lastPrice"])
    except: return 0.0

def send(title: str, desc: str, color: int):
    global alert_count
    alert_count += 1
    footer = datetime.now(pst).strftime("%b %d %I:%M %p PST")
    requests.post(WEBHOOK, json={
        "content": PING_TAG if PING_ALERTS and os.environ.get("DISCORD_USER_ID") else None,
        "embeds": [{"title": title, "description": desc, "color": color,
                    "footer": {"text": footer}}]
    })

def get_data(tf: str):
    period = "60d" if tf == "4h" else "14d"
    try:
        df = yf.download(TICKER, period=period, interval=tf, progress=False, threads=False)
        if len(df) < 60: return None
        df["ema5"]  = ta.ema(df["Close"], length=5)
        df["ema12"] = ta.ema(df["Close"], length=12)
        df["ema34"] = ta.ema(df["Close"], length=34)
        df["ema50"] = ta.ema(df["Close"], length=50)
        df["atr"]   = ta.atr(df["High"], df["Low"], df["Close"], length=14)
        df = df.dropna()
        return df if len(df) >= 2 else None
    except: return None

print("BTC 4H + 30MIN ELITE BOT — FINAL VERSION — LIVE FOREVER")
while True:
    try:
        now = time.time()
        if now - last_alert < COOLDOWN: time.sleep(300); continue

        s = spot()
        if s <= 0: time.sleep(60); continue

        df_4h = get_data("4h")
        df_30m = get_data("30m")
        if not df_4h or not df_30m: time.sleep(60); continue

        # 4h values
        e5_4h = df_4h["ema5"].iloc[-1]
        e12_4h = df_4h["ema12"].iloc[-1]
        e34_4h = df_4h["ema34"].iloc[-1]
        e50_4h = df_4h["ema50"].iloc[-1]
        atr_4h = df_4h["atr"].iloc[-1]
        high_4h = df_4h["High"].values
        low_4h = df_4h["Low"].values

        # 30min values + flip detection
        e5_30m = df_30m["ema5"].iloc[-1]
        e12_30m = df_30m["ema12"].iloc[-1]
        e5_prev = df_30m["ema5"].iloc[-2]
        e12_prev = df_30m["ema12"].iloc[-2]
        bull_flip = e5_prev <= e12_prev and e5_30m > e12_30m
        bear_flip = e5_prev >= e12_prev and e5_30m < e12_30m

        bullish_4h = e5_4h > e12_4h and e34_4h > e50_4h
        bearish_4h = e5_4h < e12_4h and e34_4h < e50_4h

        # === BULL/BEAR FLAG DETECTION ===
        is_bull_flag = (low_4h[-1] > low_4h[-5] and high_4h[-1] < high_4h[-5] and bullish_4h)
        is_bear_flag = (high_4h[-1] < high_4h[-5] and low_4h[-1] > low_4h[-5] and bearish_4h)

        # === BULL FLAG BREAK + RE-ENTRY ===
        if is_bull_flag and s > high_4h[-1]:
            target = s + (atr_4h * 1.95)
            desc = f"**BULL FLAG BREAK — 4H + 30M**\nPrice: ${s:,.0f}\nTarget: ${target:,.0f} (+195% ATR)\nEst. 14–15h"
            send("BULL FLAG BREAK — ENTER LONG", desc, 0x00FF00)
            last_alert = now

        if bullish_4h and bear_flip:
            send("LONG TAKE PROFIT — 30M BEAR FLIP", "Lock gains — fade starting", 0xFF0000)
            last_alert = now
        if bullish_4h and bull_flip:
            send("RE-LONG — BULL FLAG RESUMING", "Trend back on — add position", 0x00FF00)
            last_alert = now

        # === BEAR FLAG BREAK + RE-ENTRY ===
        if is_bear_flag and s < low_4h[-1]:
            target = s - (atr_4h * 1.95)
            desc = f"**BEAR FLAG BREAK — 4H + 30M**\nPrice: ${s:,.0f}\nTarget: ${target:,.0f} (-195% ATR)\nEst. 14–15h"
            send("BEAR FLAG BREAK — ENTER SHORT", desc, 0xFF0000)
            last_alert = now

        if bearish_4h and bull_flip:
            send("SHORT COVER — 30M BULL FLIP", "Take profits — bounce starting", 0x00FF00)
            last_alert = now
        if bearish_4h and bear_flip:
            send("RE-SHORT — BEAR FLAG RESUMING", "Trend back on — re-enter", 0xFF0000)
            last_alert = now

    except Exception as e:
        requests.post(WEBHOOK, json={"content": f"BOT CRASHED: {str(e)[:1900]}"})
        time.sleep(120)

    time.sleep(60)
