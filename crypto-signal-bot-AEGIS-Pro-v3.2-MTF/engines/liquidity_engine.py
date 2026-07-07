"""
موتور 14 - Liquidity Engine
تشخیص نقدینگی، Stop Hunt, Equal High/Low
"""
import pandas as pd
import numpy as np
from .base_engine import BaseEngine, EngineResult


class LiquidityEngine(BaseEngine):
    def __init__(self):
        super().__init__("Liquidity", weight=1.5)

    def analyze(self, df, symbol, timeframes=None):
        if df is None or len(df) < 30:
            return EngineResult(self.name, 30, "NEUTRAL", {}, ["No data"])

        score = 0
        reasons = []
        details = {}
        high, low, close = df["high"], df["low"], df["close"]

        # ===== Equal Highs / Equal Lows (نقدینگی) =====
        for i in range(3, 15):
            if abs(high.iloc[-1] - high.iloc[-i]) / high.iloc[-i] < 0.002:
                score += 5
                reasons.append(f"💰 Equal Highs at {high.iloc[-1]:.2f}")
                details["equal_high"] = True
                break

        for i in range(3, 15):
            if abs(low.iloc[-1] - low.iloc[-i]) / low.iloc[-i] < 0.002:
                score -= 5
                reasons.append(f"💰 Equal Lows at {low.iloc[-1]:.2f}")
                details["equal_low"] = True
                break

        # ===== Stop Hunt (Wick گرفتن Low قبلی) =====
        if len(df) > 5:
            prev_low = low.iloc[-6:-1].min()
            if low.iloc[-1] < prev_low and close.iloc[-1] > prev_low:
                score += 10
                reasons.append(f"🎯 Stop Hunt detected! (wiped lows at {prev_low:.2f})")
                details["stop_hunt"] = True

            prev_high = high.iloc[-6:-1].max()
            if high.iloc[-1] > prev_high and close.iloc[-1] < prev_high:
                score -= 10
                reasons.append(f"🎯 Stop Hunt detected! (wiped highs at {prev_high:.2f})")
                details["stop_hunt"] = True

        # ===== Liquidity Sweep ساده =====
        if len(df) > 10:
            range_10 = high.iloc[-10:].max() - low.iloc[-10:].min()
            if range_10 > 0:
                # بررسی sweeping
                if close.iloc[-1] > high.iloc[-10:-1].max() * 0.99:
                    score += 8
                    reasons.append("💰 Buy-side liquidity swept")
                    details["liquidity_sweep"] = "buy_side"

                if close.iloc[-1] < low.iloc[-10:-1].min() * 1.01:
                    score -= 8
                    reasons.append("💰 Sell-side liquidity swept")
                    details["liquidity_sweep"] = "sell_side"

        score = max(-100, min(100, score))
        norm_score = (score + 60) * 100 / 120
        norm_score = max(0, min(100, norm_score))
        signal = "BULLISH" if score > 10 else "BEARISH" if score < -10 else "NEUTRAL"

        return EngineResult(self.name, round(norm_score, 1), signal, details, reasons)
