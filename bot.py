import os
import time
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
from datetime import datetime

WEBHOOK = os.environ["DISCORD_WEBHOOK"]
COOLDOWN = 3600
last_signal = 0

print("BTC 30MIN ELITE BOT — IMMORTAL FIXED EDITION — RUNNING")

while True:
    try:
        if time.time() - last_signal < COOLDOWN:
            time.sleep(60)
            continue

        df = yf.download("BTC-USD", period="30d", interval="30m", progress=False, threads=False)
        if len(df) < 50:
            time.sleep(60)
            continue

        df["ema5"]  = ta.ema(df["Close"], length=5)
        df["ema12"] = ta.ema(df["Close"], length=12)
        df["atr"]   = ta.atr(df["High"], df["Low"], df["Close"], length=14)
        adx_df      = ta.adx(df["High"], df["Low"], df["Close"], length=14)
        
        df = df.join(adx_df).dropna()

        if len(df) < 2:
            time.sleep(60)
            continue

        price     = df["Close"].iloc[-1]
        ema5      = df["ema5"].iloc[-1]
        ema12     = df["ema12"].iloc[-1]
        ema5_prev = df["ema5"].iloc[-2]
        ema12_prev= df["ema12"].iloc[-2]
        adx       = df["ADX_14"].iloc[-1]      # ← this was the bug (was a Series before)
        atr       = df["atr"].iloc[-1]

        long  = ema5_prev <= ema12_prev and ema5 > ema12 and adx > 23 and price > ema5
        short = ema5_prev >= ema12_prev and ema5
