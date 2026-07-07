import pandas as pd
import numpy as np
from .base import BaseStrategy, StrategyResult
from loguru import logger

class TrendFollowingStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Trend Following 📈")
        self.weight = 1.0

    def analyze(self, df, symbol, timeframe):
        if df is None or len(df) < 50:
            return StrategyResult(self.name, "NEUTRAL", 0, 0, ["Insufficient data"])
        try:
            score = 0; reasoning = []
            e9 = df["close"].ewm(span=9).mean()
            e21 = df["close"].ewm(span=21).mean()
            e50 = df["close"].ewm(span=50).mean() if len(df) >= 50 else None
            cp = df["close"].iloc[-1]
            
            if cp > e9.iloc[-1] > e21.iloc[-1]:
                score += 25; reasoning.append("✅ Price above EMA 9 & 21 (Bullish)")
                if e50 is not None and e9.iloc[-1] > e21.iloc[-1] > e50.iloc[-1]:
                    score += 15; reasoning.append("✅ Strong uptrend alignment")
            elif cp < e9.iloc[-1] < e21.iloc[-1]:
                score -= 25; reasoning.append("❌ Price below EMA 9 & 21 (Bearish)")
                if e50 is not None and e9.iloc[-1] < e21.iloc[-1] < e50.iloc[-1]:
                    score -= 15; reasoning.append("❌ Strong downtrend alignment")
            
            if "adx" in df.columns:
                adx = df["adx"].iloc[-1] if not pd.isna(df["adx"].iloc[-1]) else 0
                dip, dim = df["di_plus"].iloc[-1], df["di_minus"].iloc[-1]
                if adx > 25:
                    if dip > dim: score += 20; reasoning.append(f"✅ Strong uptrend (ADX: {adx:.1f})")
                    else: score -= 20; reasoning.append(f"❌ Strong downtrend (ADX: {adx:.1f})")
            
            score = max(-100, min(100, score))
            sig = "BUY" if score >= 30 else "SELL" if score <= -30 else "NEUTRAL"
            conf = min(100, abs(score) + 20) if sig != "NEUTRAL" else 50
            return StrategyResult(self.name, sig, score, conf, reasoning)
        except Exception as e:
            return StrategyResult(self.name, "NEUTRAL", 0, 0, [f"Error: {e}"])
