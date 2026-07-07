import pandas as pd
import numpy as np
from .base import BaseStrategy, StrategyResult

class MeanReversionStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Mean Reversion 🔄")
        self.weight = 0.8

    def analyze(self, df, symbol, timeframe):
        if df is None or len(df) < 30:
            return StrategyResult(self.name, "NEUTRAL", 0, 0, ["Insufficient data"])
        try:
            score = 0; reasoning = []
            if "rsi" in df.columns:
                rsi = df["rsi"].iloc[-1] if not pd.isna(df["rsi"].iloc[-1]) else 50
                prsi = df["rsi"].iloc[-2] if not pd.isna(df["rsi"].iloc[-2]) else 50
                if rsi < 30:
                    score += 30; reasoning.append(f"💰 RSI oversold ({rsi:.1f})")
                    if rsi < 25: score += 10; reasoning.append("🔥 Extreme oversold!")
                elif rsi > 70:
                    score -= 30; reasoning.append(f"⚠️ RSI overbought ({rsi:.1f})")
                    if rsi > 75: score -= 10; reasoning.append("🔥 Extreme overbought!")
                if rsi < 35 and rsi > prsi: score += 5; reasoning.append("↗️ RSI turning up")
                elif rsi > 65 and rsi < prsi: score -= 5; reasoning.append("↘️ RSI turning down")
            
            if "bb_lower" in df.columns:
                cp = df["close"].iloc[-1]
                if cp <= df["bb_lower"].iloc[-1] * 1.005:
                    score += 25; reasoning.append("📉 At lower Bollinger Band - Bounce expected!")
                elif cp >= df["bb_upper"].iloc[-1] * 0.995:
                    score -= 25; reasoning.append("📈 At upper Bollinger Band - Rejection expected!")
            
            score = max(-100, min(100, score))
            sig = "BUY" if score >= 25 else "SELL" if score <= -25 else "NEUTRAL"
            conf = min(100, abs(score) + 15) if sig != "NEUTRAL" else 50
            return StrategyResult(self.name, sig, score, conf, reasoning)
        except Exception as e:
            return StrategyResult(self.name, "NEUTRAL", 0, 0, [f"Error: {e}"])
