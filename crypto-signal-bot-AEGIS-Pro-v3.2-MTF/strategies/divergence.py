import pandas as pd
import numpy as np
from .base import BaseStrategy, StrategyResult

class DivergenceStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Divergence 🎯")
        self.weight = 1.1

    def analyze(self, df, symbol, timeframe):
        if df is None or len(df) < 30:
            return StrategyResult(self.name, "NEUTRAL", 0, 0, ["Insufficient data"])
        try:
            score = 0
            reasoning = []
            
            if "rsi" in df.columns and len(df) >= 20:
                pl = df["low"].iloc[-20:]
                ph = df["high"].iloc[-20:]
                rsi = df["rsi"].iloc[-20:]
                crsi = df["rsi"].iloc[-1] if not pd.isna(df["rsi"].iloc[-1]) else 50
                
                for i in range(1, 10):
                    if pl.iloc[-1] < pl.iloc[-i] and crsi > rsi.iloc[-i] and crsi < 40:
                        score += 20
                        reasoning.append("🟢 BULLISH RSI DIVERGENCE!")
                        break
                for i in range(1, 10):
                    if ph.iloc[-1] > ph.iloc[-i] and crsi < rsi.iloc[-i] and crsi > 60:
                        score -= 20
                        reasoning.append("🔴 BEARISH RSI DIVERGENCE!")
                        break
            
            score = max(-100, min(100, score))
            sig = "BUY" if score >= 20 else "SELL" if score <= -20 else "NEUTRAL"
            conf = min(100, abs(score) + 20) if sig != "NEUTRAL" else 50
            return StrategyResult(self.name, sig, score, conf, reasoning)
        except Exception as e:
            return StrategyResult(self.name, "NEUTRAL", 0, 0, [f"Error: {e}"])
