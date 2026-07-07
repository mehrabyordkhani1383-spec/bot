"""
موتور 1 - Market Regime Engine v3.2 Pro
ADX + ATR + EMA Slope + Range Width + Choppiness + Volume + Volatility
Regimes: TREND / WEAK_TREND / RANGE / VOLATILE / ACCUMULATION / DISTRIBUTION
"""
import pandas as pd
import numpy as np
from .base_engine import BaseEngine, EngineResult


class MarketRegimeEngine(BaseEngine):
    def __init__(self):
        super().__init__("Market Regime", weight=2.0)

    def _choppiness(self, df, period=14):
        high = df['high'].rolling(period).max()
        low = df['low'].rolling(period).min()
        tr = pd.concat([
            df['high'] - df['low'],
            (df['high'] - df['close'].shift()).abs(),
            (df['low'] - df['close'].shift()).abs()
        ], axis=1).max(axis=1)
        atr_sum = tr.rolling(period).sum()
        hh_ll = (high - low).replace(0, np.nan)
        chop = 100 * np.log10(atr_sum / hh_ll) / np.log10(period)
        return chop

    def analyze(self, df, symbol, timeframes=None):
        if df is None or len(df) < 50:
            return EngineResult(self.name, 0, "NEUTRAL", {"regime": "unknown"}, ["Insufficient data"])

        close = df["close"]
        high, low = df["high"], df["low"]
        reasons = []
        details = {}

        # ATR
        tr = pd.concat([high-low, (high-close.shift()).abs(), (low-close.shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        atr_pct = (atr / close).iloc[-1] * 100
        details["atr_pct"] = round(atr_pct, 2)

        # ADX
        up = high - high.shift()
        dn = low.shift() - low
        tr14 = tr.rolling(14).mean()
        pdi = 100 * (up.where((up > dn) & (up > 0), 0).rolling(14).mean() / tr14)
        ndi = 100 * (dn.where((dn > up) & (dn > 0), 0).rolling(14).mean() / tr14)
        dx = 100 * (abs(pdi - ndi) / (pdi + ndi).replace(0, np.nan))
        adx = dx.rolling(14).mean().iloc[-1]
        adx = adx if not pd.isna(adx) else 20
        details["adx"] = round(adx, 1)

        # EMA Slope
        ema20 = close.ewm(span=20).mean()
        ema_slope = (ema20.iloc[-1] - ema20.iloc[-5]) / ema20.iloc[-5] * 100
        details["ema_slope"] = round(ema_slope, 2)

        # Range Width
        lookback = 30
        hh = high.iloc[-lookback:].max()
        ll = low.iloc[-lookback:].min()
        range_width = (hh - ll) / ll * 100
        details["range_width"] = round(range_width, 2)

        # Choppiness Index
        chop_series = self._choppiness(df, 14)
        chop = chop_series.iloc[-1] if not pd.isna(chop_series.iloc[-1]) else 50
        details["choppiness"] = round(chop, 1)

        # Volume
        vol_ratio = 1.0
        if "volume" in df.columns:
            vol = df["volume"]
            vol_sma = vol.rolling(20).mean()
            vol_ratio = vol.iloc[-1] / vol_sma.iloc[-1] if vol_sma.iloc[-1] > 0 else 1
            details["vol_ratio"] = round(vol_ratio, 2)

        # Volatility (std dev returns)
        returns = close.pct_change()
        volatility = returns.rolling(20).std().iloc[-1] * 100
        details["volatility"] = round(volatility * np.sqrt(365), 1) if not pd.isna(volatility) else 0

        # ===== Regime Classification =====
        regime = "RANGE"
        score = 50

        # Accumulation: low ADX, low volatility, range narrow, volume increasing
        is_accumulation = (adx < 22 and range_width < 8 and chop > 55 and vol_ratio > 1.1 and abs(ema_slope) < 0.3)
        # Distribution: similar but price near top, volume high
        is_distribution = (adx < 22 and range_width < 8 and chop > 55 and vol_ratio > 1.2 and close.iloc[-1] > (hh + ll) / 2)

        if is_accumulation:
            regime = "ACCUMULATION"
            score = 60
            reasons.append(f"📦 Accumulation (ADX {adx:.0f}, Range {range_width:.1f}%)")
        elif is_distribution:
            regime = "DISTRIBUTION"
            score = 40
            reasons.append(f"📦 Distribution (ADX {adx:.0f}, Range {range_width:.1f}%)")
        elif adx > 30 and atr_pct > 3.5:
            regime = "VOLATILE"
            score = 45
            reasons.append(f"⚡ Volatile (ADX={adx:.0f}, ATR={atr_pct:.1f}%)")
        elif adx > 25 and abs(ema_slope) > 0.4 and chop < 45:
            regime = "TREND"
            score = 75
            reasons.append(f"📈 Strong Trend (ADX={adx:.0f}, Slope={ema_slope:.2f}%)")
        elif adx > 20 and chop < 55:
            regime = "WEAK_TREND"
            score = 55
            reasons.append(f"📊 Weak Trend (ADX={adx:.0f})")
        else:
            regime = "RANGE"
            score = 35
            reasons.append(f"📉 Ranging (ADX={adx:.0f}, CHOP={chop:.0f})")

        details["regime"] = regime

        # Signal
        sma50 = close.rolling(50).mean().iloc[-1]
        signal = "NEUTRAL"
        if regime in ["TREND", "WEAK_TREND", "ACCUMULATION"] and vol_ratio > 1.0:
            signal = "BULLISH" if close.iloc[-1] > sma50 else "BEARISH"

        return EngineResult(self.name, score, signal, details, reasons)
