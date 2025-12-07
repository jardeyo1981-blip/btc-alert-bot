import os
import time
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests

WEBHOOK = os.environ["DISCORD_WEBHOOK"]
COOLDOWN = 3600
last_signal = 0

print("BTC 30MIN ELITE BOT — FINAL IMMORTAL VERSION — DEC 2025")

while True:
    try:
        if time.time() - last_signal < COOLDOWN:
            time.sleep(60)
            continue

        # Get data
        df = yf.download("BTC-USD", period="30d", interval="30m", progress=False)
        if len(df) < 100:
            time.sleep(60)
            continue

        # Indicators
        df["ema5"]  = ta.ema(df["Close"], length=5)
        df["ema12"] = ta.ema(df["Close"], length=12)
        df["atr"]   = ta.atr(df["High"], df["Low"], df["Close"], length=14)
        adx_df      = ta.adx(df["High"], df["Low"], df["Close"], length=14)

        df = pd.concat([df, adx_df], axis=1).dropna()

        if len(df) < 2:                     # safety
            time.sleep(60)
            continue

        # Values
        price      = df["Close"].iloc[-1]
        ema5       = df["ema5"].iloc[-1]
        ema12      = df["ema12"].iloc[-1]
        ema5_prev  = df["ema5"].iloc[-2]
        ema12_prev = df["ema12"].iloc[-2]
        adx        = df["ADX_14"].iloc[-1]
        atr        = df["atr"].iloc[-1]

        # Signals
        long  = ema5_prev <= ema12_prev and ema5 > ema12 and adx > 23 and price > ema5
        short = ema5_prev >= ema12_prev and ema5 < ema12 and adx > 23 and price < ema5

        if long:
            target = price + atr * 1.8
            requests.post(WEBHOOK, json={"content": f"Long | ${price:,.0f} → ${target:,.0f} (+1.8×ATR) | ADX {adx:.1f}"})
            last_signal = time.time()

        if short:
            target = price - atr * 1.8
            requests.post(WEBHOOK, json={"content": f"Short | ${price:,.0f} → ${target:,.0f} (-1.8×ATR) | ADX {adx:.1f}"})
            last_signal = time.time()

        time.sleep(60)

    except Exception as e:
        requests.post(WEBHOOK, json={"content": f"Bot auto-restarted — {str(e)}"})
        time.sleep(300)
