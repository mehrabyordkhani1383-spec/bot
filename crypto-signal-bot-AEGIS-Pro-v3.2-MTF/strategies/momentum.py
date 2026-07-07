import pandas as pd
import numpy as np
from .base import BaseStrategy, StrategyResult

class MomentumStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Momentum ⚡")
        self.weight = 1.0

    def analyze(self, df, symbol, timeframe):
        if df is None or len(df) < 30:
            return StrategyResult(self.name, "NEUTRAL", 0, 0, ["Insufficient data"])
        try:
            score = 0; reasoning = []
            
            for p in [5, 10]:
                roc = (df["close"].iloc[-1] - df["close"].iloc[-p]) / df["close"].iloc[-p] * 100
                if p == 5 and abs(roc) > 2:
                    if roc > 0: score += 15; reasoning.append(f"⚡ Strong momentum ({roc:.1f}%)")
                    else: score -= 15; reasoning.append(f"⚡ Strong negative momentum ({roc:.1f}%)")
            
            if "macd_histogram" in df.columns:
                h, ph = df["macd_histogram"].iloc[-1], df["macd_histogram"].iloc[-2]
                if h > ph:
                    score += 12 if h > 0 else 5
                    reasoning.append("📈 MACD momentum increasing")
                elif h < ph:
                    score -= 12 if h < 0 else 5
                    reasoning.append("📉 MACD momentum decreasing")
            
            if len(df) >= 10:
                r5 = (df["close"].iloc[-1] / df["close"].iloc[-5] - 1) * 100
                r10 = (df["close"].iloc[-5] / df["close"].iloc[-10] - 1) * 100
                if r5 > r10 and r5 > 0: score += 10; reasoning.append("🚀 Price accelerating up")
                elif r5 < r10 and r5 < 0: score -= 10; reasoning.append("💨 Price accelerating down")
            
            score = max(-100, min(100, score))
            sig = "BUY" if score >= 25 else "SELL" if score <= -25 else "NEUTRAL"
            conf = min(100, abs(score) + 15) if sig != "NEUTRAL" else 50
            return StrategyResult(self.name, sig, score, conf, reasoning)
        except Exception as e:
            return StrategyResult(self.name, "NEUTRAL", 0, 0, [f"Error: {e}"])
