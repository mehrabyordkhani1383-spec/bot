"""
موتور 5 - Price Action Engine
تشخیص ۱۵+ الگوی کندل استیک
"""
import pandas as pd
import numpy as np
from .base_engine import BaseEngine, EngineResult


class PriceActionEngine(BaseEngine):
    def __init__(self):
        super().__init__("Price Action", weight=1.5)

    def analyze(self, df, symbol, timeframes=None):
        if df is None or len(df) < 5:
            return EngineResult(self.name, 0, "NEUTRAL", {}, ["No data"])

        score = 0
        reasons = []
        details = {}
        patterns_found = []

        # تابع کمکی
        def body(c): return abs(c["close"] - c["open"])
        def rg(c): return c["high"] - c["low"]
        def uw(c): return c["high"] - max(c["close"], c["open"])
        def lw(c): return min(c["close"], c["open"]) - c["low"]
        def is_bull(c): return c["close"] > c["open"]
        def is_bear(c): return c["close"] < c["open"]

        # بررسی آخرین ۵ کندل
        for i in range(1, min(6, len(df))):
            c = df.iloc[-i]
            if rg(c) == 0: continue

            br = body(c) / rg(c)
            uwr = uw(c) / rg(c) if rg(c) > 0 else 0
            lwr = lw(c) / rg(c) if rg(c) > 0 else 0

            # Doji
            if br < 0.1:
                patterns_found.append(("Doji", 0))
                continue

            # Hammer
            if lwr > 0.6 and br < 0.3 and is_bull(c):
                patterns_found.append(("Hammer", 6))
                continue

            # Shooting Star
            if uwr > 0.6 and br < 0.3 and is_bear(c):
                patterns_found.append(("Shooting Star", -5))
                continue

            # Marubozu
            if br > 0.9:
                if is_bull(c):
                    patterns_found.append(("Bullish Marubozu", 5))
                else:
                    patterns_found.append(("Bearish Marubozu", -5))
                continue

            # Pin Bar
            if (lwr > 0.6 or uwr > 0.6) and br < 0.3:
                if lwr > 0.6:
                    patterns_found.append(("Bullish Pin Bar", 4))
                else:
                    patterns_found.append(("Bearish Pin Bar", -4))
                continue

        # الگوهای دو کندله
        if len(df) >= 3:
            c1, c2 = df.iloc[-1], df.iloc[-2]

            # Bullish Engulfing
            if is_bear(c2) and is_bull(c1):
                if c1["open"] < c2["close"] and c1["close"] > c2["open"]:
                    patterns_found.append(("Bullish Engulfing", 8))

            # Bearish Engulfing
            if is_bull(c2) and is_bear(c1):
                if c1["open"] > c2["close"] and c1["close"] < c2["open"]:
                    patterns_found.append(("Bearish Engulfing", -8))

            # Piercing / Dark Cloud
            if is_bear(c2) and is_bull(c1):
                mid = (c2["open"] + c2["close"]) / 2
                if c1["close"] > mid and c1["open"] < c2["close"]:
                    patterns_found.append(("Piercing Line", 5))

            if is_bull(c2) and is_bear(c1):
                mid = (c2["open"] + c2["close"]) / 2
                if c1["close"] < mid and c1["open"] > c2["close"]:
                    patterns_found.append(("Dark Cloud Cover", -5))

        # الگوهای سه کندله
        if len(df) >= 5:
            c1, c2, c3 = df.iloc[-1], df.iloc[-2], df.iloc[-3]

            # Three Soldiers
            if all(is_bull(x) for x in [c3, c2, c1]):
                if all(x["close"] > x["open"] for x in [c3, c2, c1]):
                    patterns_found.append(("Three Soldiers", 10))

            # Three Crows
            if all(is_bear(x) for x in [c3, c2, c1]):
                if all(x["close"] < x["open"] for x in [c3, c2, c1]):
                    patterns_found.append(("Three Crows", -10))

            # Morning Star
            if len(df) >= 5:
                c4 = df.iloc[-4]
                if is_bear(c4) and is_bull(c2):
                    if body(c3) < body(c4) * 0.3:
                        if c2["close"] > (c4["open"] + c4["close"]) / 2:
                            patterns_found.append(("Morning Star", 10))

            # Evening Star
            if len(df) >= 5:
                c4 = df.iloc[-4]
                if is_bull(c4) and is_bear(c2):
                    if body(c3) < body(c4) * 0.3:
                        if c2["close"] < (c4["open"] + c4["close"]) / 2:
                            patterns_found.append(("Evening Star", -10))

        details["patterns"] = [p[0] for p in patterns_found] if patterns_found else ["None"]

        # محاسبه امتیاز - ولی هرگز فقط با یک الگو تصمیم نگیر
        for name, pts in patterns_found:
            score += pts

        # محدود کردن - هیچ وقت امتیاز الگوها نباید بیش از حد باشه
        score = max(-100, min(100, score))

        # هیچ وقت فقط با کندل استیک سیگنال نده - امتیاز رو محدود کن
        signal = "NEUTRAL"

        return EngineResult(self.name, round(score, 1), signal, details, reasons + [f"📊 Patterns: {', '.join(details.get('patterns', ['None']))}"])
