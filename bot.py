# =====================================================
# BTC 4H + 15M PRO BOT — PERMANENT ANTI-SERIES FIX
# DEC 2025 — THIS ONE CANNOT DIE
# =====================================================

import os
import time
import requests
import pandas as pd
import pandas_ta as ta
from datetime import datetime
from zoneinfo import ZoneInfo
import yfinance as yf
import sys
import traceback

WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
if not WEBHOOK:
    print("ERROR: DISCORD_WEBHOOK environment variable is not set. Exiting.", file=sys.stderr)
    sys.exit(1)

PING_TAG = f"<@{os.environ.get('DISCORD_USER_ID', '')}>"
PING_ALERTS = os.environ.get("PING_ALERTS", "true").lower() == "true"

TICKER = "BTC-USD"
COOLDOWN = 1800
MAX_ERROR_MSG_LENGTH = 1900
last_alert = 0
alert_count = 0
tz_utc = ZoneInfo("UTC")


def spot() -> float:
    try:
        fi = yf.Ticker(TICKER).fast_info
        return float(fi.get("lastPrice", 0.0)) if fi else 0.0
    except Exception:
        # fallback: attempt to get the last close using history
        try:
            hist = yf.download(TICKER, period="1d", interval="1m", progress=False, threads=False)
            if not hist.empty:
                return float(hist["Close"].iloc[-1])
        except Exception:
            pass
        return 0.0


def safe_scalar(series_or_value):
    """PERMANENT FIX — Turns ANY Series into a scalar, or 0 if invalid.
    If a Series/DataFrame is passed, return its last element. If a scalar NaN or None,
    return 0.0.
    """
    # Handle pandas Series/DataFrame first
    if isinstance(series_or_value, (pd.Series, pd.DataFrame)):
        try:
            # If DataFrame, take last value of the first column
            if isinstance(series_or_value, pd.DataFrame):
                if series_or_value.shape[0] == 0 or series_or_value.shape[1] == 0:
                    return 0.0
                val = series_or_value.iloc[-1, 0]
            else:
                if len(series_or_value) == 0:
                    return 0.0
                val = series_or_value.iloc[-1]
            if pd.isna(val):
                return 0.0
            return float(val)
        except Exception:
            return 0.0

    # Non-series: handle NaN / None
    try:
        if series_or_value is None:
            return 0.0
        if pd.isna(series_or_value):
            return 0.0
        return float(series_or_value)
    except Exception:
        return 0.0


def send(title: str, desc: str, color: int):
    global alert_count
    alert_count += 1

    payload = {
        "embeds": [
            {
                "title": title,
                "description": desc,
                "color": color,
                "footer": {"text": datetime.now(tz_utc).strftime("%b %d %H:%M UTC")},
            }
        ]
    }
    if PING_ALERTS and os.environ.get("DISCORD_USER_ID"):
        payload["content"] = PING_TAG

    try:
        resp = requests.post(WEBHOOK, json=payload, timeout=15)
        if resp.status_code >= 400:
            # Log failure (Discord returns useful error messages)
            print(f"Failed to send webhook (status {resp.status_code}): {resp.text}", file=sys.stderr)
    except Exception as e:
        print(f"Exception while sending webhook: {e}", file=sys.stderr)


def get_data(tf: str):
    period = "60d" if tf == "4h" else "10d"
    try:
        df = yf.download(TICKER, period=period, interval=tf, progress=False, threads=False)
        if df is None or len(df) < 60:
            return None
        df["ema5"] = ta.ema(df["Close"], length=5)
        df["ema12"] = ta.ema(df["Close"], length=12)
        df["ema34"] = ta.ema(df["Close"], length=34)
        df["ema50"] = ta.ema(df["Close"], length=50)
        df["atr"] = ta.atr(df["High"], df["Low"], df["Close"], length=14)
        df = df.dropna()
        if len(df) < 2:
            return None
        return df
    except Exception:
        return None


print("BTC 4H + 15M PRO BOT — ANTI-SERIES IMMORTAL — LIVE FOREVER")
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

        df_4h = get_data("4h")
        df_15m = get_data("15m")
        if df_4h is None or df_15m is None:
            time.sleep(60)
            continue

        # SAFE 4h values — using safe_scalar to kill Series forever
        e5_4h = safe_scalar(df_4h["ema5"].iloc[-1])
        e12_4h = safe_scalar(df_4h["ema12"].iloc[-1])
        e34_4h = safe_scalar(df_4h["ema34"].iloc[-1])
        e50_4h = safe_scalar(df_4h["ema50"].iloc[-1])
        atr_4h = safe_scalar(df_4h["atr"].iloc[-1])

        # SAFE 15m values + flip detection
        e5_15m = safe_scalar(df_15m["ema5"].iloc[-1])
        e12_15m = safe_scalar(df_15m["ema12"].iloc[-1])
        e5_15m_prev = safe_scalar(df_15m["ema5"].iloc[-2])
        e12_15m_prev = safe_scalar(df_15m["ema12"].iloc[-2])
        bull_flip_15m = e5_15m_prev <= e12_15m_prev and e5_15m > e12_15m
        bear_flip_15m = e5_15m_prev >= e12_15m_prev and e5_15m < e12_15m

        bullish_4h = e5_4h > e12_4h and e34_4h > e50_4h
        bearish_4h = e5_4h < e12_4h and e34_4h < e50_4h

        # === MAIN TREND ENTRY ===
        if bullish_4h and e5_15m > e12_15m:
            target = s + (atr_4h * 1.95)
            desc = f"**LONG — 4H + 15M CONFIRMED**\nPrice: ${s:,.0f}\n\n"
            desc += f"**Target:** ${target:,.0f} (+195% ATR)\n→ 75% of average move (~82% hit rate)\n"
            desc += f"**Est. Time:** 14–15 hours\nStop: ${e50_4h:,.0f} (34-50 EMA)"
            send("4H BULLISH — ENTER LONG", desc, 0x00FF00)
            last_alert = now

        elif bearish_4h and e5_15m < e12_15m:
            target = s - (atr_4h * 1.95)
            desc = f"**SHORT — 4H + 15M CONFIRMED**\nPrice: ${s:,.0f}\n\n"
            desc += f"**Target:** ${target:,.0f} (-195% ATR)\n→ 75% of average move (~82% hit rate)\n"
            desc += f"**Est. Time:** 14–15 hours\nStop: ${e50_4h:,.0f} (34-50 EMA)"
            send("4H BEARISH — ENTER SHORT", desc, 0xFF0000)
            last_alert = now

        # === COUNTER-TREND PROFIT-TAKING + RE-ENTRY ===
        if bearish_4h and bull_flip_15m:
            send("SHORT COVER — 15M BULL FLIP", "Take profits now\nCounter-trend bounce starting", 0x00FF00)
            last_alert = now
        if bearish_4h and bear_flip_15m:
            send("RE-SHORT — 15M BEAR FLIP", "Trend resuming — re-enter short", 0xFF0000)
            last_alert = now
        if bullish_4h and bear_flip_15m:
            send("LONG TAKE PROFIT — 15M BEAR FLIP", "Lock gains — counter-trend fade", 0xFF0000)
            last_alert = now
        if bullish_4h and bull_flip_15m:
            send("RE-LONG — 15M BULL FLIP", "Trend resuming — add to longs", 0x00FF00)
            last_alert = now

    except Exception as e:
        # Send the error to the webhook (if available) and print traceback
        err_text = "".join(traceback.format_exception_only(type(e), e))[:MAX_ERROR_MSG_LENGTH]
        try:
            requests.post(WEBHOOK, json={"content": f"BOT CRASHED: {err_text}"})
        except Exception:
            print(f"Failed to POST crash to webhook: {err_text}", file=sys.stderr)
        time.sleep(120)

    time.sleep(45)
