"""
موتور 7 - Volume Engine
تحلیل حجم: Volume Spike, Relative Volume, OBV, CMF
"""
import pandas as pd
import numpy as np
from .base_engine import BaseEngine, EngineResult


class VolumeEngine(BaseEngine):
    def __init__(self):
        super().__init__("Volume", weight=2.0)

    def analyze(self, df, symbol, timeframes=None):
        if df is None or len(df) < 20:
            return EngineResult(self.name, 0, "NEUTRAL", {}, ["No data"])

        if "volume" not in df.columns or df["volume"].sum() == 0:
            return EngineResult(self.name, 30, "NEUTRAL", {}, ["No volume data"])

        score = 0
        reasons = []
        details = {}
        close = df["close"]
        volume = df["volume"]
        high, low = df["high"], df["low"]

        # ===== Average Volume =====
        vol_sma20 = volume.rolling(20).mean()
        vol_ratio = volume.iloc[-1] / vol_sma20.iloc[-1] if vol_sma20.iloc[-1] > 0 else 1
        details["vol_ratio"] = round(vol_ratio, 2)

        if vol_ratio > 2.0:
            score += 20
            reasons.append(f"🔊 Volume spike! ({vol_ratio:.1f}x normal)")
        elif vol_ratio > 1.5:
            score += 12
            reasons.append(f"🔊 Above average volume ({vol_ratio:.1f}x)")
        elif vol_ratio > 1.2:
            score += 5
        elif vol_ratio < 0.5:
            score -= 10
            reasons.append(f"🔇 Low volume ({vol_ratio:.1f}x) - weak moves")

        # ===== OBV (On-Balance Volume) =====
        obv = (volume * ((close.diff() > 0).astype(int) * 2 - 1)).cumsum()
        obv_sma = obv.rolling(20).mean()
        obv_trend = "up" if obv.iloc[-1] > obv_sma.iloc[-1] else "down"
        details["obv_trend"] = obv_trend

        if obv_trend == "up" and close.iloc[-1] > close.rolling(20).mean().iloc[-1]:
            score += 10
            reasons.append("✅ OBV confirming uptrend")
        elif obv_trend == "down" and close.iloc[-1] < close.rolling(20).mean().iloc[-1]:
            score -= 10
            reasons.append("❌ OBV confirming downtrend")

        # ===== CMF (Chaikin Money Flow) =====
        mfm = ((close - low) - (high - close)) / (high - low).replace(0, np.nan)
        mfv = mfm * volume
        cmf = mfv.rolling(20).sum() / volume.rolling(20).sum()
        cmf_val = cmf.iloc[-1] if not pd.isna(cmf.iloc[-1]) else 0
        details["cmf"] = round(cmf_val, 3)

        if cmf_val > 0.1:
            score += 10
            reasons.append("✅ CMF positive (buying pressure)")
        elif cmf_val < -0.1:
            score -= 10
            reasons.append("❌ CMF negative (selling pressure)")

        # ===== تشخیص Breakout با حجم =====
        if vol_ratio > 1.5:
            price_change_pct = abs(close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100
            if price_change_pct > 1.5:
                if close.iloc[-1] > close.iloc[-2]:
                    score += 10
                    reasons.append(f"🚀 High volume breakout (+{price_change_pct:.1f}%)")
                else:
                    score -= 10
                    reasons.append(f"💨 High volume breakdown (-{price_change_pct:.1f}%)")

        score = max(-100, min(100, score))
        norm_score = (score + 60) * 100 / 120
        norm_score = max(0, min(100, norm_score))

        signal = "BULLISH" if score > 15 else "BEARISH" if score < -15 else "NEUTRAL"

        return EngineResult(self.name, round(norm_score, 1), signal, details, reasons)
