"""
موتور 2 - Trend Engine v3.2
تحلیل روند با EMA, VWAP + Swing Structure واقعی
HH/HL/LH/LL بر اساس Pivot های واقعی
"""
import pandas as pd
import numpy as np
from .base_engine import BaseEngine, EngineResult


class TrendEngine(BaseEngine):
    def __init__(self):
        super().__init__("Trend", weight=2.5)

    def _find_swings(self, df, left=5, right=5):
        """پیدا کردن Swing High/Low واقعی"""
        highs = df['high'].values
        lows = df['low'].values
        swing_highs = []
        swing_lows = []
        
        for i in range(left, len(df) - right):
            # Swing High
            is_sh = True
            for j in range(i-left, i+right+1):
                if j == i: continue
                if highs[j] >= highs[i]:
                    is_sh = False
                    break
            if is_sh:
                swing_highs.append((i, highs[i]))
            
            # Swing Low
            is_sl = True
            for j in range(i-left, i+right+1):
                if j == i: continue
                if lows[j] <= lows[i]:
                    is_sl = False
                    break
            if is_sl:
                swing_lows.append((i, lows[i]))
        
        return swing_highs, swing_lows

    def analyze(self, df, symbol, timeframes=None):
        if df is None or len(df) < 100:
            return EngineResult(self.name, 0, "NEUTRAL", {}, ["Insufficient data"])

        score = 0
        reasons = []
        details = {}
        close = df["close"]
        high = df["high"]
        low = df["low"]

        # ===== EMA ها =====
        for p in [20, 50, 100, 200]:
            if len(df) >= p:
                ema = close.ewm(span=p).mean()
                details[f"ema{p}"] = round(float(ema.iloc[-1]), 2)

        # ===== روند EMA =====
        ema20 = close.ewm(span=20).mean()
        ema50 = close.ewm(span=50).mean() if len(df) >= 50 else None
        ema100 = close.ewm(span=100).mean() if len(df) >= 100 else None
        ema200 = close.ewm(span=200).mean() if len(df) >= 200 else None

        cp = close.iloc[-1]

        # امتیاز قیمت نسبت به EMAها
        ema_score = 0
        if cp > ema20.iloc[-1]: ema_score += 10
        else: ema_score -= 10

        if ema50 is not None and cp > float(ema50.iloc[-1]): ema_score += 10
        elif ema50 is not None: ema_score -= 10

        if ema100 is not None and cp > float(ema100.iloc[-1]): ema_score += 10
        elif ema100 is not None: ema_score -= 10

        if ema200 is not None and cp > float(ema200.iloc[-1]): ema_score += 10
        elif ema200 is not None: ema_score -= 10

        # alignment EMA
        if ema50 is not None and float(ema20.iloc[-1]) > float(ema50.iloc[-1]):
            ema_score += 10
            reasons.append("✅ EMA20 > EMA50 (Bullish alignment)")
        elif ema50 is not None and float(ema20.iloc[-1]) < float(ema50.iloc[-1]):
            ema_score -= 10
            reasons.append("❌ EMA20 < EMA50 (Bearish alignment)")

        # Slope EMA
        slope20 = (ema20.iloc[-1] - ema20.iloc[-5]) / ema20.iloc[-5] * 100
        details["ema_slope"] = round(slope20, 2)
        if slope20 > 0.5:
            ema_score += 5
            reasons.append("📈 EMA slope positive")
        elif slope20 < -0.5:
            ema_score -= 5
            reasons.append("📉 EMA slope negative")

        # ===== VWAP =====
        if "volume" in df.columns:
            tp = (high + low + close) / 3
            vwap = (tp * df["volume"]).rolling(20).sum() / df["volume"].rolling(20).sum()
            details["vwap"] = round(float(vwap.iloc[-1]), 2)
            if cp > vwap.iloc[-1]:
                ema_score += 10
                reasons.append("✅ Price above VWAP")
            else:
                ema_score -= 10
                reasons.append("❌ Price below VWAP")

        # ===== SWING STRUCTURE - واقعی =====
        swing_highs, swing_lows = self._find_swings(df, left=5, right=5)
        
        structure = "UNKNOWN"
        structure_score = 0
        
        # تحلیل 3 swing آخر
        if len(swing_highs) >= 2:
            sh1_idx, sh1_price = swing_highs[-1]
            sh2_idx, sh2_price = swing_highs[-2]
            details["last_swing_high"] = round(sh1_price, 4)
            details["prev_swing_high"] = round(sh2_price, 4)
            
            if sh1_price > sh2_price * 1.001:  # Higher High
                structure_score += 15
                reasons.append(f"📈 HH confirmed: {sh2_price:.2f} → {sh1_price:.2f}")
                structure = "BULLISH"
                details["hh"] = True
            elif sh1_price < sh2_price * 0.999:  # Lower High
                structure_score -= 15
                reasons.append(f"📉 LH confirmed: {sh2_price:.2f} → {sh1_price:.2f}")
                if structure != "BULLISH":
                    structure = "BEARISH"
                details["lh"] = True
        
        if len(swing_lows) >= 2:
            sl1_idx, sl1_price = swing_lows[-1]
            sl2_idx, sl2_price = swing_lows[-2]
            details["last_swing_low"] = round(sl1_price, 4)
            details["prev_swing_low"] = round(sl2_price, 4)
            
            if sl1_price > sl2_price * 1.001:  # Higher Low
                structure_score += 10
                reasons.append(f"📈 HL confirmed: {sl2_price:.2f} → {sl1_price:.2f}")
                if structure == "UNKNOWN":
                    structure = "BULLISH"
                details["hl"] = True
            elif sl1_price < sl2_price * 0.999:  # Lower Low
                structure_score -= 10
                reasons.append(f"📉 LL confirmed: {sl2_price:.2f} → {sl1_price:.2f}")
                structure = "BEARISH"
                details["ll"] = True

        # Break of Structure check
        if len(swing_highs) >= 1 and len(swing_lows) >= 1:
            last_sh = swing_highs[-1][1]
            last_sl = swing_lows[-1][1]
            if cp > last_sh:
                structure_score += 8
                reasons.append("✅ BOS Bullish - broke last swing high")
                details["bos"] = "bullish"
            elif cp < last_sl:
                structure_score -= 8
                reasons.append("❌ BOS Bearish - broke last swing low")
                details["bos"] = "bearish"

        details["structure"] = structure
        details["swing_highs_count"] = len(swing_highs)
        details["swing_lows_count"] = len(swing_lows)
        
        ema_score += structure_score

        # امتیاز نهایی
        score = max(0, min(100, (ema_score + 80) * 100 / 160))

        if score >= 65:
            signal = "BULLISH"
        elif score <= 35:
            signal = "BEARISH"
        else:
            signal = "NEUTRAL"

        return EngineResult(self.name, round(score, 1), signal, details, reasons)
