"""
موتور 6 - Momentum Engine v3.2
RSI, MACD, Stochastic + Divergence واقعی بر اساس Swing
"""
import pandas as pd
import numpy as np
from .base_engine import BaseEngine, EngineResult


class MomentumEngine(BaseEngine):
    def __init__(self):
        super().__init__("Momentum", weight=1.8)

    def _find_swings(self, series, left=5, right=5, is_high=True):
        """Swing High/Low برای هر سری (قیمت، RSI، MACD)"""
        vals = series.values if hasattr(series, 'values') else np.array(series)
        swings = []
        for i in range(left, len(vals) - right):
            window = vals[i-left:i+right+1]
            if is_high:
                if vals[i] == np.max(window) and list(window).count(vals[i]) == 1:
                    swings.append((i, vals[i]))
            else:
                if vals[i] == np.min(window) and list(window).count(vals[i]) == 1:
                    swings.append((i, vals[i]))
        return swings

    def analyze(self, df, symbol, timeframes=None):
        if df is None or len(df) < 50:
            return EngineResult(self.name, 0, "NEUTRAL", {}, ["No data"])

        close = df["close"]
        high, low = df["high"], df["low"]
        score = 0
        reasons = []
        details = {}

        # ===== RSI =====
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + gain / loss))
        rsi_val = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
        details["rsi"] = round(rsi_val, 1)

        if 55 <= rsi_val <= 70:
            score += 15
            reasons.append(f"✅ RSI={rsi_val:.1f} (optimal bullish)")
        elif 30 <= rsi_val <= 45:
            score -= 15
            reasons.append(f"❌ RSI={rsi_val:.1f} (bearish zone)")
        elif rsi_val > 75:
            score -= 12
            reasons.append(f"⚠️ RSI={rsi_val:.1f} overbought")
        elif rsi_val < 25:
            score += 8
            reasons.append(f"⚠️ RSI={rsi_val:.1f} oversold - bounce possible")

        # ===== MACD =====
        ema12 = close.ewm(span=12).mean()
        ema26 = close.ewm(span=26).mean()
        macd = ema12 - ema26
        macd_signal = macd.ewm(span=9).mean()
        macd_h = macd - macd_signal
        macd_val = macd.iloc[-1]
        macd_h_val = macd_h.iloc[-1]
        prev_macd_h = macd_h.iloc[-2] if len(macd_h) > 1 else 0
        details["macd"] = round(macd_val, 4)
        details["macd_hist"] = round(macd_h_val, 4)

        if macd_val > 0 and macd_h_val > prev_macd_h:
            score += 10
            reasons.append("✅ MACD bullish & increasing")
        elif macd_val < 0 and macd_h_val < prev_macd_h:
            score -= 10
            reasons.append("❌ MACD bearish & decreasing")
        elif macd_val > 0:
            score += 5
        elif macd_val < 0:
            score -= 5

        # ===== Stochastic RSI =====
        rsi_vals = rsi.iloc[-14:] if len(rsi) >= 14 else rsi
        min_rsi = float(rsi_vals.min()) if not rsi_vals.empty else 0
        max_rsi = float(rsi_vals.max()) if not rsi_vals.empty else 100
        if max_rsi > min_rsi:
            stoch_rsi = (rsi_val - min_rsi) / (max_rsi - min_rsi) * 100
        else:
            stoch_rsi = 50
        details["stoch_rsi"] = round(stoch_rsi, 1)

        if 20 < stoch_rsi < 40:
            score += 8
            reasons.append(f"✅ StochRSI={stoch_rsi:.0f} rising")
        elif 60 < stoch_rsi < 80:
            score -= 8
            reasons.append(f"❌ StochRSI={stoch_rsi:.0f} falling")

        # ===== CCI =====
        tp = (high + low + close) / 3
        sma_tp = tp.rolling(20).mean()
        mad = tp.rolling(20).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
        cci = (tp - sma_tp) / (0.015 * mad)
        cci_val = cci.iloc[-1] if not pd.isna(cci.iloc[-1]) else 0
        details["cci"] = round(cci_val, 1)

        if 100 < cci_val < 200:
            score += 5
        elif -200 < cci_val < -100:
            score -= 5

        # ===== DIVERGENCE - SWING BASED =====
        # RSI divergence
        price_lows = self._find_swings(low, left=5, right=5, is_high=False)
        rsi_lows = self._find_swings(rsi.fillna(50), left=5, right=5, is_high=False)
        
        price_highs = self._find_swings(high, left=5, right=5, is_high=True)
        rsi_highs = self._find_swings(rsi.fillna(50), left=5, right=5, is_high=True)

        divergence_found = False
        
        # Bullish RSI Divergence: Lower Low price, Higher Low RSI
        if len(price_lows) >= 2 and len(rsi_lows) >= 2:
            p1_idx, p1_val = price_lows[-1]
            p2_idx, p2_val = price_lows[-2]
            # find matching RSI swings near those indices
            r_near_p1 = [r for r in rsi_lows if abs(r[0] - p1_idx) <= 3]
            r_near_p2 = [r for r in rsi_lows if abs(r[0] - p2_idx) <= 3]
            if r_near_p1 and r_near_p2:
                r1_val = r_near_p1[-1][1]
                r2_val = r_near_p2[-1][1]
                if p1_val < p2_val * 0.998 and r1_val > r2_val + 2 and r1_val < 45:
                    score += 15
                    reasons.append("🟢 Bullish RSI Divergence (Swing confirmed)!")
                    details["divergence"] = "bullish_rsi"
                    divergence_found = True

        # Bearish RSI Divergence: Higher High price, Lower High RSI
        if not divergence_found and len(price_highs) >= 2 and len(rsi_highs) >= 2:
            p1_idx, p1_val = price_highs[-1]
            p2_idx, p2_val = price_highs[-2]
            r_near_p1 = [r for r in rsi_highs if abs(r[0] - p1_idx) <= 3]
            r_near_p2 = [r for r in rsi_highs if abs(r[0] - p2_idx) <= 3]
            if r_near_p1 and r_near_p2:
                r1_val = r_near_p1[-1][1]
                r2_val = r_near_p2[-1][1]
                if p1_val > p2_val * 1.002 and r1_val < r2_val - 2 and r1_val > 55:
                    score -= 15
                    reasons.append("🔴 Bearish RSI Divergence (Swing confirmed)!")
                    details["divergence"] = "bearish_rsi"
                    divergence_found = True

        # MACD Divergence
        if not divergence_found and len(df) > 30:
            macd_swings_low = self._find_swings(macd.fillna(0), left=5, right=5, is_high=False)
            macd_swings_high = self._find_swings(macd.fillna(0), left=5, right=5, is_high=True)
            
            # Bullish MACD div
            if len(price_lows) >= 2 and len(macd_swings_low) >= 2:
                pl1_idx, pl1_val = price_lows[-1]
                pl2_idx, pl2_val = price_lows[-2]
                ml1 = [m for m in macd_swings_low if abs(m[0] - pl1_idx) <= 3]
                ml2 = [m for m in macd_swings_low if abs(m[0] - pl2_idx) <= 3]
                if ml1 and ml2 and pl1_val < pl2_val and ml1[-1][1] > ml2[-1][1]:
                    score += 12
                    reasons.append("🟢 Bullish MACD Divergence!")
                    details["divergence"] = details.get("divergence", "") + " macd_bull"
            
            # Bearish MACD div
            if len(price_highs) >= 2 and len(macd_swings_high) >= 2:
                ph1_idx, ph1_val = price_highs[-1]
                ph2_idx, ph2_val = price_highs[-2]
                mh1 = [m for m in macd_swings_high if abs(m[0] - ph1_idx) <= 3]
                mh2 = [m for m in macd_swings_high if abs(m[0] - ph2_idx) <= 3]
                if mh1 and mh2 and ph1_val > ph2_val and mh1[-1][1] < mh2[-1][1]:
                    score -= 12
                    reasons.append("🔴 Bearish MACD Divergence!")
                    details["divergence"] = details.get("divergence", "") + " macd_bear"

        score = max(-100, min(100, score))
        norm_score = (score + 60) * 100 / 120
        norm_score = max(0, min(100, norm_score))

        signal = "BULLISH" if score > 20 else "BEARISH" if score < -20 else "NEUTRAL"

        return EngineResult(self.name, round(norm_score, 1), signal, details, reasons)
