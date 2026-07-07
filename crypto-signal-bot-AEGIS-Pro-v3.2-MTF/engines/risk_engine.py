"""
موتور 11 - Risk Engine v3.2 Pro
SL/TP ترکیبی: ATR + Swing Structure + SR + Liquidity
"""
import pandas as pd
import numpy as np
from .base_engine import BaseEngine, EngineResult


class RiskEngine(BaseEngine):
    def __init__(self):
        super().__init__("Risk Management", weight=1.5)

    def _find_swings(self, df, left=3, right=3):
        highs = df['high'].values
        lows = df['low'].values
        sh, sl = [], []
        for i in range(left, len(df) - right):
            if highs[i] == max(highs[i-left:i+right+1]):
                sh.append((i, highs[i]))
            if lows[i] == min(lows[i-left:i+right+1]):
                sl.append((i, lows[i]))
        return sh, sl

    def analyze(self, df, symbol, timeframes=None):
        if df is None or len(df) < 30:
            return EngineResult(self.name, 30, "NEUTRAL", {}, ["No data"])

        close = df["close"]
        high, low = df["high"], df["low"]
        cp = close.iloc[-1]
        reasons = []
        details = {}

        # ===== ATR =====
        tr = pd.concat([high-low, (high-close.shift()).abs(), (low-close.shift()).abs()], axis=1).max(axis=1)
        atr14 = tr.rolling(14).mean().iloc[-1]
        atr_pct = atr14 / cp * 100
        details["atr_pct"] = round(atr_pct, 2)

        # ===== Swing Structure SL =====
        sh, sl = self._find_swings(df, 3, 3)
        swing_sl_long = swing_sl_short = None
        if sl:
            last_swing_low = sl[-1][1]
            swing_sl_long = (cp - last_swing_low) / cp * 100 * 1.05
            details["swing_low"] = round(last_swing_low, 6)
        if sh:
            last_swing_high = sh[-1][1]
            swing_sl_short = (last_swing_high - cp) / cp * 100 * 1.05
            details["swing_high"] = round(last_swing_high, 6)

        # ===== Support / Resistance =====
        # Simple SR: recent highs/lows clusters
        lookback = 30
        recent_high = high.iloc[-lookback:].max()
        recent_low = low.iloc[-lookback:].min()
        sr_sl_long = (cp - recent_low) / cp * 100 * 1.02
        sr_sl_short = (recent_high - cp) / cp * 100 * 1.02
        details["sr_low"] = round(recent_low, 6)
        details["sr_high"] = round(recent_high, 6)

        # ===== Liquidity zones =====
        # Volume profile approx: high volume nodes
        # Simplified: use recent low volume as liquidity
        liquidity_sl = atr_pct * 1.8
        details["liquidity_buffer"] = round(liquidity_sl, 2)

        # ===== Combine SL =====
        # ATR base
        if atr_pct > 5:
            atr_sl = atr_pct * 1.5
        elif atr_pct > 3:
            atr_sl = atr_pct * 1.8
        elif atr_pct > 1.5:
            atr_sl = atr_pct * 2.0
        else:
            atr_sl = 1.8

        # Combine with swing/SR
        sl_candidates_long = [x for x in [atr_sl, swing_sl_long or atr_sl, sr_sl_long, liquidity_sl] if x and 0.8 < x < 5.0]
        sl_candidates_short = [x for x in [atr_sl, swing_sl_short or atr_sl, sr_sl_short, liquidity_sl] if x and 0.8 < x < 5.0]
        
        sl_pct_long = np.median(sl_candidates_long) if sl_candidates_long else atr_sl
        sl_pct_short = np.median(sl_candidates_short) if sl_candidates_short else atr_sl
        
        # Use average for general signal
        sl_pct = (sl_pct_long + sl_pct_short) / 2
        sl_pct = max(1.0, min(4.0, sl_pct))

        details["sl_pct"] = round(sl_pct, 2)
        details["sl_long"] = round(sl_pct_long, 2)
        details["sl_short"] = round(sl_pct_short, 2)

        # ===== TP based on market structure =====
        # Find next resistance/support for TP
        tp_multiplier = 2.2  # default R/R
        
        # If strong trend, extend TP
        # (regime info not available here, use ATR)
        if atr_pct < 2.5:
            tp_multiplier = 2.5  # tight market, higher RR
        elif atr_pct > 4:
            tp_multiplier = 1.8  # volatile, lower RR
        
        tp_pct = sl_pct * tp_multiplier
        details["tp_pct"] = round(tp_pct, 2)

        # TP1/TP2/TP3 levels
        details["tp1_pct"] = round(tp_pct * 0.4, 2)
        details["tp2_pct"] = round(tp_pct * 0.7, 2)
        details["tp3_pct"] = round(tp_pct, 2)

        rr = tp_pct / sl_pct if sl_pct > 0 else 2.0
        details["rr_ratio"] = round(rr, 2)

        if rr >= 2.2:
            reasons.append(f"✅ R/R 1:{rr:.1f} excellent (ATR+SR+Liquidity)")
        elif rr >= 1.8:
            reasons.append(f"✅ R/R 1:{rr:.1f} good")
        else:
            reasons.append(f"⚠️ R/R 1:{rr:.1f}")

        reasons.append(f"📊 SL={sl_pct:.1f}% (ATR {atr_pct:.1f}% + Swing/SR)")
        
        score = min(100, max(0, rr * 35))
        signal = "BULLISH" if rr >= 1.8 else "NEUTRAL"

        return EngineResult(self.name, round(score, 1), signal, details, reasons)
