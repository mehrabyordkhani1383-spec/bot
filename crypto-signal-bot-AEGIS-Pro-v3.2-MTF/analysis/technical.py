"""
📈 Technical Analysis Engine
تحلیل تکنیکال جامع با بیش از ۱۵ اندیکاتور
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class TechnicalSignal:
    symbol: str
    timeframe: str
    score: float
    signal: str = "NEUTRAL"
    indicators: Dict = field(default_factory=dict)
    patterns: List[str] = field(default_factory=list)
    support_resistance: Dict = field(default_factory=dict)
    market_structure: str = ""


class TechnicalAnalyzer:
    def __init__(self):
        pass

    def analyze(self, df: pd.DataFrame, symbol: str, timeframe: str) -> Optional[TechnicalSignal]:
        if df is None or len(df) < 50:
            return None
        try:
            df = self._add_all_indicators(df)
            score = 0
            indicators = {}
            patterns_found = []
            support_resistance = {}

            rsi_score, rsi_info = self._analyze_rsi(df); score += rsi_score; indicators["RSI"] = rsi_info
            macd_score, macd_info = self._analyze_macd(df); score += macd_score; indicators["MACD"] = macd_info
            ma_score, ma_info = self._analyze_moving_averages(df); score += ma_score; indicators["MovingAverages"] = ma_info
            bb_score, bb_info = self._analyze_bollinger(df); score += bb_score; indicators["BollingerBands"] = bb_info
            stoch_score, stoch_info = self._analyze_stochastic(df); score += stoch_score; indicators["Stochastic"] = stoch_info
            adx_score, adx_info = self._analyze_adx(df); score += adx_score; indicators["ADX"] = adx_info
            ichi_score, ichi_info = self._analyze_ichimoku(df); score += ichi_score; indicators["Ichimoku"] = ichi_info
            vol_score, vol_info = self._analyze_volume(df); score += vol_score; indicators["Volume"] = vol_info
            pattern_score, patterns_found = self._detect_candlestick_patterns(df); score += pattern_score
            sr_score, support_resistance = self._find_support_resistance(df); score += sr_score
            market_structure = self._analyze_market_structure(df)

            score = max(-100, min(100, score))
            signal_type = "STRONG_BUY" if score > 60 else "BUY" if score > 20 else "STRONG_SELL" if score < -60 else "SELL" if score < -20 else "NEUTRAL"

            return TechnicalSignal(symbol=symbol, timeframe=timeframe, score=score, signal=signal_type,
                                   indicators=indicators, patterns=patterns_found,
                                   support_resistance=support_resistance, market_structure=market_structure)
        except Exception as e:
            logger.error(f"❌ Tech analysis error {symbol}: {e}")
            return None

    def _add_all_indicators(self, df):
        df = df.copy()
        df["rsi"] = self._rsi(df["close"])
        ema12, ema26 = df["close"].ewm(span=12).mean(), df["close"].ewm(span=26).mean()
        df["macd"] = ema12 - ema26
        df["macd_signal"] = df["macd"].ewm(span=9).mean()
        df["macd_histogram"] = df["macd"] - df["macd_signal"]
        for p in [20, 50, 200]:
            df[f"sma_{p}"] = df["close"].rolling(p).mean()
        df["ema_9"] = df["close"].ewm(span=9).mean()
        df["ema_21"] = df["close"].ewm(span=21).mean()
        bb_mid = df["close"].rolling(20).mean()
        bb_std = df["close"].rolling(20).std()
        df["bb_upper"] = bb_mid + 2 * bb_std
        df["bb_lower"] = bb_mid - 2 * bb_std
        df["bb_width"] = df["bb_upper"] - df["bb_lower"]
        df["bb_percent"] = (df["close"] - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])
        df["stoch_rsi_k"], df["stoch_rsi_d"] = self._stoch_rsi(df)
        df["adx"], df["di_plus"], df["di_minus"] = self._adx(df)
        df["atr"] = self._atr(df)
        df["volume_sma"] = df["volume"].rolling(20).mean()
        df["volume_ratio"] = df["volume"] / df["volume_sma"]
        return df

    def _rsi(self, prices, period=14):
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _stoch_rsi(self, df, period=14):
        rsi = df["rsi"]
        min_r = rsi.rolling(period).min()
        max_r = rsi.rolling(period).max()
        k = ((rsi - min_r) / (max_r - min_r) * 100).rolling(3).mean()
        d = k.rolling(3).mean()
        return k, d

    def _adx(self, df, period=14):
        h, l, c = df["high"], df["low"], df["close"]
        tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        up = h - h.shift()
        down = l.shift() - l
        pdm = np.where((up > down) & (up > 0), up, 0)
        ndm = np.where((down > up) & (down > 0), down, 0)
        pdi = 100 * pd.Series(pdm, index=df.index).rolling(period).mean() / atr
        ndi = 100 * pd.Series(ndm, index=df.index).rolling(period).mean() / atr
        dx = 100 * abs(pdi - ndi) / (pdi + ndi)
        return dx.rolling(period).mean(), pdi, ndi

    def _atr(self, df, period=14):
        h, l, c = df["high"], df["low"], df["close"]
        tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
        return tr.rolling(period).mean()

    def _analyze_rsi(self, df):
        rsi = df["rsi"].iloc[-1]
        score = 0
        info = {"value": round(rsi, 1), "direction": "neutral"}
        if rsi < 30:
            score += 12
            info["direction"] = "oversold"
            if rsi < 25: score += 3
        elif rsi > 70:
            score -= 12
            info["direction"] = "overbought"
            if rsi > 75: score -= 3
        info["status"] = "Bullish 🔥" if score > 0 else ("Bearish ❄️" if score < 0 else "Neutral")
        return score, info

    def _analyze_macd(self, df):
        macd = df["macd"].iloc[-1]
        signal = df["macd_signal"].iloc[-1]
        hist = df["macd_histogram"].iloc[-1]
        ph = df["macd_histogram"].iloc[-2]
        score = 0
        cross = "none"
        if macd > signal and df["macd"].iloc[-2] <= df["macd_signal"].iloc[-2]:
            score += 10; cross = "bullish"
        elif macd < signal and df["macd"].iloc[-2] >= df["macd_signal"].iloc[-2]:
            score -= 10; cross = "bearish"
        if macd > 0: score += 3
        else: score -= 3
        if hist > ph: score += 2
        else: score -= 2
        return score, {"macd": round(macd, 4), "signal": round(signal, 4), "histogram": round(hist, 4), "cross": cross,
                       "status": "Bullish 🔥" if score > 0 else ("Bearish ❄️" if score < 0 else "Neutral")}

    def _analyze_moving_averages(self, df):
        c = df["close"].iloc[-1]
        s20, s50 = df["sma_20"].iloc[-1], df["sma_50"].iloc[-1]
        e9, e21 = df["ema_9"].iloc[-1], df["ema_21"].iloc[-1]
        score = 0
        info = {}
        if c > s20: score += 3
        else: score -= 3
        if c > s50: score += 3
        else: score -= 3
        if c > e9: score += 2
        else: score -= 2
        if c > e21: score += 2
        else: score -= 2
        if len(df) > 60:
            p = df["sma_20"].iloc[-2] - df["sma_50"].iloc[-2]
            curr = s20 - s50
            if p < 0 and curr > 0: score += 5; info["golden_cross"] = True
            elif p > 0 and curr < 0: score -= 5; info["death_cross"] = True
        if c > s20 > s50: score += 3
        elif c < s20 < s50: score -= 3
        info["price_vs_sma20"] = f"{((c/s20-1)*100):.1f}%"
        info["price_vs_sma50"] = f"{((c/s50-1)*100):.1f}%"
        info["status"] = "Bullish 🔥" if score > 0 else ("Bearish ❄️" if score < 0 else "Neutral")
        return score, info

    def _analyze_bollinger(self, df):
        c = df["close"].iloc[-1]
        bu, bl = df["bb_upper"].iloc[-1], df["bb_lower"].iloc[-1]
        bp = df["bb_percent"].iloc[-1]
        score = 0
        if c <= bl * 1.01: score += 8
        elif c >= bu * 0.99: score -= 8
        return score, {"bb_percent": round(bp, 2), "position": "upper" if bp > 0.8 else ("lower" if bp < 0.2 else "middle"),
                       "status": "Bullish 🔥" if score > 0 else ("Bearish ❄️" if score < 0 else "Neutral")}

    def _analyze_stochastic(self, df):
        k, d = df["stoch_rsi_k"].iloc[-1], df["stoch_rsi_d"].iloc[-1]
        pk = df["stoch_rsi_k"].iloc[-2]
        score = 0
        if k < 20 and d < 20:
            score += 6
            if pk < d and k > d: score += 4
        elif k > 80 and d > 80:
            score -= 6
            if pk > d and k < d: score -= 4
        return score, {"k": round(k, 1), "d": round(d, 1),
                       "status": "Bullish 🔥" if score > 0 else ("Bearish ❄️" if score < 0 else "Neutral")}

    def _analyze_adx(self, df):
        adx = df["adx"].iloc[-1] if not pd.isna(df["adx"].iloc[-1]) else 0
        dip, dim = df["di_plus"].iloc[-1], df["di_minus"].iloc[-1]
        score = 0
        trend = "weak"
        if adx >= 25:
            trend = "strong"
            score += 8 if dip > dim else -8
        elif adx >= 20:
            trend = "moderate"
            score += 4 if dip > dim else -4
        return score, {"adx": round(adx, 1), "di_plus": round(dip, 1), "di_minus": round(dim, 1),
                       "trend_strength": trend, "status": "Trending 📈" if adx > 25 else "Ranging 📊"}

    def _analyze_ichimoku(self, df):
        if len(df) < 52: return 0, {"status": "insufficient"}
        h52 = df["high"].rolling(52).max().iloc[-1]
        l52 = df["low"].rolling(52).min().iloc[-1]
        pos = (df["close"].iloc[-1] - l52) / (h52 - l52) * 100
        score = 2 if 30 < pos < 70 else (-2 if pos > 80 else 2)
        return score, {"range_position": round(pos, 1), "status": "Above Cloud ☁️" if pos > 50 else "Below Cloud ☁️"}

    def _analyze_volume(self, df):
        vr = df["volume_ratio"].iloc[-1]
        pc = df["close"].iloc[-1] - df["close"].iloc[-2]
        score = 0
        if vr > 1.5 and pc > 0: score += 6
        elif vr > 1.5 and pc < 0: score -= 6
        elif vr < 0.5 and abs(pc) > df["atr"].iloc[-1]: score -= 3
        return score, {"volume_ratio": round(vr, 2), "volume_trend": "increasing" if vr > 1 else "decreasing",
                       "status": "High Volume 🔊" if vr > 1.5 else "Normal Volume"}

    def _detect_candlestick_patterns(self, df):
        score = 0
        patterns = []
        if len(df) < 3: return 0, patterns
        c1, c2 = df.iloc[-1], df.iloc[-2]
        
        def bd(c): return abs(c["close"] - c["open"])
        def rg(c): return c["high"] - c["low"]
        
        # Doji
        if rg(c1) > 0 and bd(c1) / rg(c1) < 0.1:
            patterns.append("Doji ⚠️")
            if c2["close"] > c2["open"]: score += 4
        
        # Hammer
        if rg(c1) > 0:
            lw = min(c1["close"], c1["open"]) - c1["low"]
            uw = c1["high"] - max(c1["close"], c1["open"])
            if lw / rg(c1) > 0.6 and bd(c1) / rg(c1) < 0.3:
                if c1["close"] > c1["open"]:
                    score += 6; patterns.append("Hammer 🔨 (Bullish)")
            if uw / rg(c1) > 0.6 and bd(c1) / rg(c1) < 0.3:
                if c1["close"] < c1["open"]:
                    score -= 5; patterns.append("Shooting Star 🌠 (Bearish)")
        
        # Engulfing
        if c2["close"] < c2["open"] and c1["close"] > c1["open"]:
            if c1["open"] < c2["close"] and c1["close"] > c2["open"]:
                score += 7; patterns.append("Bullish Engulfing 🟢")
        if c2["close"] > c2["open"] and c1["close"] < c1["open"]:
            if c1["open"] > c2["close"] and c1["close"] < c2["open"]:
                score -= 7; patterns.append("Bearish Engulfing 🔴")
        
        # Three soldiers/crows
        if len(df) >= 5:
            c3 = df.iloc[-3]
            if all(x["close"] > x["open"] for x in [c3, c2, c1]):
                score += 8; patterns.append("Three Soldiers ⚔️ (Bullish)")
            if all(x["close"] < x["open"] for x in [c3, c2, c1]):
                score -= 8; patterns.append("Three Crows 🦅 (Bearish)")
        
        return score, patterns

    def _find_support_resistance(self, df):
        score = 0
        sr = {"support": [], "resistance": []}
        if len(df) < 50: return 0, sr
        c = df["close"].iloc[-1]
        w = 20
        for i in range(w, len(df) - w):
            if df["high"].iloc[i] == df["high"].iloc[i-w:i+w].max():
                sr["resistance"].append(round(df["high"].iloc[i], 4))
            if df["low"].iloc[i] == df["low"].iloc[i-w:i+w].min():
                sr["support"].append(round(df["low"].iloc[i], 4))
        sr["resistance"] = sorted(set(sr["resistance"]))[-5:]
        sr["support"] = sorted(set(sr["support"]))[-5:]
        for level in sr["resistance"]:
            if abs(c - level) / c < 0.02: score -= 5; sr["near_resistance"] = level; break
        for level in sr["support"]:
            if abs(c - level) / c < 0.02: score += 5; sr["near_support"] = level; break
        return score, sr

    def _analyze_market_structure(self, df):
        if len(df) < 50: return "insufficient_data"
        c = df["close"].values[-20:]
        if c[-1] > c[-10] > c[0]: return "Uptrend 📈"
        if c[-1] < c[-10] < c[0]: return "Downtrend 📉"
        rng = (df["high"].iloc[-20:].max() - df["low"].iloc[-20:].min()) / df["low"].iloc[-20:].min() * 100
        if rng < 10: return "Ranging 📊"
        return "Mixed 🔀"
