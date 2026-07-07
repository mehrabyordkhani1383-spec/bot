"""
موتور 15 - Volatility Engine
ATR, Bollinger Width, Choppiness Index
"""
import pandas as pd
import numpy as np
from .base_engine import BaseEngine, EngineResult


class VolatilityEngine(BaseEngine):
    def __init__(self):
        super().__init__("Volatility", weight=1.0)

    def analyze(self, df, symbol, timeframes=None):
        if df is None or len(df) < 30:
            return EngineResult(self.name, 50, "NEUTRAL", {}, ["No data"])

        close, high, low = df["close"], df["high"], df["low"]
        reasons = []
        details = {}

        # ===== ATR =====
        tr = pd.concat([high-low, (high-close.shift()).abs(), (low-close.shift()).abs()], axis=1).max(axis=1)
        atr14 = tr.rolling(14).mean()
        atr_current = atr14.iloc[-1]
        atr_sma = atr14.rolling(50).mean().iloc[-1]
        atr_ratio = atr_current / atr_sma if atr_sma > 0 else 1
        details["atr_ratio"] = round(atr_ratio, 2)

        # ===== Bollinger Width =====
        sma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()
        bb_width = ((sma20 + 2 * std20) - (sma20 - 2 * std20)) / sma20
        bb_width_val = bb_width.iloc[-1] if not pd.isna(bb_width.iloc[-1]) else 0
        bb_width_avg = bb_width.rolling(50).mean().iloc[-1]
        bb_ratio = bb_width_val / bb_width_avg if bb_width_avg > 0 else 1
        details["bb_width_ratio"] = round(bb_ratio, 2)

        # ===== Choppiness Index =====
        if len(df) >= 14:
            highest = high.rolling(14).max()
            lowest = low.rolling(14).min()
            tr_sum = tr.rolling(14).sum()
            chop = 100 * np.log10(tr_sum / (highest - lowest)) / np.log10(14) if (highest - lowest).iloc[-1] > 0 else 50
            chop_val = chop.iloc[-1] if not pd.isna(chop.iloc[-1]) else 50
        else:
            chop_val = 50
        details["choppiness"] = round(chop_val, 1)

        # ===== امتیازدهی =====
        score = 50

        if chop_val > 60:
            score = 20
            reasons.append(f"⚠️ Market is choppy ({chop_val:.0f}) - hard to trade")
        elif chop_val < 40:
            score = 80
            reasons.append(f"✅ Strong trend ({chop_val:.0f}) - good for trend following")
        else:
            score = 50
            reasons.append(f"➡️ Normal market ({chop_val:.0f})")

        # Bollinger Squeeze
        if bb_ratio < 0.7:
            reasons.append(f"⚡ Bollinger Squeeze! (ratio: {bb_ratio:.2f}) - big move incoming")
            score = 75
            details["squeeze"] = True

        # ATR افزایش
        if atr_ratio > 1.3:
            reasons.append(f"📊 Volatility increasing ({atr_ratio:.2f}x)")

        signal = "BULLISH" if score > 60 else "BEARISH" if score < 35 else "NEUTRAL"

        return EngineResult(self.name, round(score, 1), signal, details, reasons)
