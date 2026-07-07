import pandas as pd
import numpy as np
from .base import BaseStrategy, StrategyResult

class BreakoutStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Breakout 🚀")
        self.weight = 1.2

    def analyze(self, df, symbol, timeframe):
        if df is None or len(df) < 50:
            return StrategyResult(self.name, "NEUTRAL", 0, 0, ["Insufficient data"])
        try:
            score = 0; reasoning = []; cp = df["close"].iloc[-1]
            rh = df["high"].iloc[-20:-1].max()
            rl = df["low"].iloc[-20:-1].min()
            
            if df["high"].iloc[-1] > rh:
                if cp > rh: score += 25; reasoning.append(f"🚀 Bullish breakout above {rh:.4f}")
                else: score -= 5
            elif df["low"].iloc[-1] < rl:
                if cp < rl: score -= 25; reasoning.append(f"💀 Bearish breakdown below {rl:.4f}")
                else: score += 5
            
            if "volume_ratio" in df.columns and df["volume_ratio"].iloc[-1] > 1.5:
                if score > 0: score += 10; reasoning.append("✅ High volume confirms breakout")
                elif score < 0: score -= 10; reasoning.append("✅ High volume confirms breakdown")
            
            score = max(-100, min(100, score))
            sig = "BUY" if score >= 25 else "SELL" if score <= -25 else "NEUTRAL"
            conf = min(100, abs(score) + 15) if sig != "NEUTRAL" else 50
            return StrategyResult(self.name, sig, score, conf, reasoning)
        except Exception as e:
            return StrategyResult(self.name, "NEUTRAL", 0, 0, [f"Error: {e}"])
