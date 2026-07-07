"""
موتور 4 - Smart Money Engine v3.2 Pro
BOS, CHOCH, Liquidity Sweep, OB, Breaker, FVG, Premium/Discount
"""
import pandas as pd
import numpy as np
from .base_engine import BaseEngine, EngineResult


class SmartMoneyEngine(BaseEngine):
    def __init__(self):
        super().__init__("Smart Money", weight=2.5)

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
        if df is None or len(df) < 50:
            return EngineResult(self.name, 0, "NEUTRAL", {}, ["No data"])

        score = 0
        reasons = []
        details = {}
        high, low, close = df["high"], df["low"], df["close"]
        cp = close.iloc[-1]

        sh, sl = self._find_swings(df, 3, 3)

        # ===== 1. BOS - Break of Structure - Swing based =====
        if len(sh) >= 2:
            last_sh, prev_sh = sh[-1][1], sh[-2][1]
            if cp > last_sh:
                score += 12
                reasons.append(f"✅ External BOS Bullish > {last_sh:.4f}")
                details["ext_bos"] = "bullish"
        if len(sl) >= 2:
            last_sl, prev_sl = sl[-1][1], sl[-2][1]
            if cp < last_sl:
                score -= 12
                reasons.append(f"✅ External BOS Bearish < {last_sl:.4f}")
                details["ext_bos"] = "bearish"

        # Internal BOS (shorter)
        if len(df) > 20:
            recent_h = high.iloc[-10:].max()
            recent_l = low.iloc[-10:].min()
            if cp > recent_h:
                score += 5
                details["int_bos"] = "bullish"
            if cp < recent_l:
                score -= 5
                details["int_bos"] = "bearish"

        # ===== 2. CHOCH - Change of Character =====
        if len(sh) >= 2 and len(sl) >= 2:
            # Bullish CHOCH: break previous SH, HL formed
            if sh[-1][1] > sh[-2][1] and sl[-1][1] > sl[-2][1]:
                score += 10
                reasons.append("🔄 CHOCH Bullish confirmed")
                details["choch"] = "bullish"
            # Bearish CHOCH
            if sh[-1][1] < sh[-2][1] and sl[-1][1] < sl[-2][1]:
                score -= 10
                reasons.append("🔄 CHOCH Bearish confirmed")
                details["choch"] = "bearish"

        # ===== 3. Market Structure Shift =====
        if len(sh) >= 3:
            # MSS Bullish: LH -> HH break
            if sh[-1][1] > sh[-2][1] > sh[-3][1]:
                score += 8
                reasons.append("📊 MSS Bullish")
                details["mss"] = "bullish"
            if sh[-1][1] < sh[-2][1] < sh[-3][1]:
                score -= 8
                reasons.append("📊 MSS Bearish")
                details["mss"] = "bearish"

        # ===== 4. Liquidity Sweep =====
        if sl:
            last_swing_low = sl[-1][1]
            lowest_wick = low.iloc[-5:].min()
            if lowest_wick < last_swing_low * 0.999 and cp > last_swing_low:
                score += 12
                reasons.append("💧 Bullish Liquidity Sweep")
                details["liquidity_sweep"] = "bullish"
        if sh:
            last_swing_high = sh[-1][1]
            highest_wick = high.iloc[-5:].max()
            if highest_wick > last_swing_high * 1.001 and cp < last_swing_high:
                score -= 12
                reasons.append("💧 Bearish Liquidity Sweep")
                details["liquidity_sweep"] = "bearish"

        # ===== 5. Order Block – real =====
        # Bullish OB: last bearish candle before strong bullish move
        for i in range(len(df)-5, len(df)-1):
            if i < 2: continue
            c0 = df.iloc[i]
            c1 = df.iloc[i+1]
            # OB bearish candle
            if c0['close'] < c0['open']:
                # followed by strong bullish displacement
                move = (c1['close'] - c0['high']) / c0['high'] * 100
                if move > 0.5:
                    ob_low, ob_high = c0['low'], c0['high']
                    if ob_low <= cp <= ob_high * 1.005:
                        score += 10
                        reasons.append(f"📦 Bullish OB mitigation {ob_low:.4f}")
                        details["ob"] = "bullish"
                        break
        # Bearish OB
        for i in range(len(df)-5, len(df)-1):
            if i < 2: continue
            c0 = df.iloc[i]
            c1 = df.iloc[i+1]
            if c0['close'] > c0['open']:
                move = (c0['low'] - c1['close']) / c0['low'] * 100
                if move > 0.5:
                    ob_low, ob_high = c0['low'], c0['high']
                    if ob_low * 0.995 <= cp <= ob_high:
                        score -= 10
                        reasons.append(f"📦 Bearish OB mitigation {ob_high:.4f}")
                        details["ob"] = "bearish"
                        break

        # ===== 6. Breaker Block =====
        # Failed OB becomes breaker
        details["breaker"] = "none"
        # simplified: if price broke OB and returned
        # (placeholder, counts as OB for now)

        # ===== 7. Mitigation Block =====
        # Similar to OB, already covered
        details["mitigation"] = details.get("ob", "none")

        # ===== 8. Fair Value Gap - real =====
        fvgs = []
        for i in range(2, len(df)):
            c1, c2, c3 = df.iloc[i-2], df.iloc[i-1], df.iloc[i]
            # Bullish FVG
            if c1['high'] < c3['low']:
                fvgs.append(("bull", c1['high'], c3['low'], i))
            # Bearish FVG
            if c1['low'] > c3['high']:
                fvgs.append(("bear", c3['high'], c1['low'], i))
        
        # Check if price is in recent FVG
        for fvg_type, f_low, f_high, idx in reversed(fvgs[-5:]):
            if f_low <= cp <= f_high:
                if fvg_type == "bull":
                    score += 6
                    reasons.append("💎 FVG Bullish filled")
                    details["fvg"] = "bullish"
                else:
                    score -= 6
                    reasons.append("💎 FVG Bearish filled")
                    details["fvg"] = "bearish"
                break

        # ===== 9. Premium / Discount Zone =====
        if len(df) >= 50:
            lookback = min(50, len(df))
            swing_high = high.iloc[-lookback:].max()
            swing_low = low.iloc[-lookback:].min()
            fib_50 = swing_low + (swing_high - swing_low) * 0.5
            details["premium_zone"] = round(swing_high, 4)
            details["discount_zone"] = round(swing_low, 4)
            details["equilibrium"] = round(fib_50, 4)
            
            if cp < fib_50:
                score += 4
                reasons.append("✅ Discount Zone - Buy favorable")
                details["pd_zone"] = "discount"
            else:
                score -= 4
                reasons.append("⚠️ Premium Zone - Sell favorable")
                details["pd_zone"] = "premium"

        # ===== Final =====
        score = max(-100, min(100, score))
        norm_score = (score + 60) * 100 / 120
        norm_score = max(0, min(100, norm_score))
        signal = "BULLISH" if score > 12 else "BEARISH" if score < -12 else "NEUTRAL"

        return EngineResult(self.name, round(norm_score, 1), signal, details, reasons)
