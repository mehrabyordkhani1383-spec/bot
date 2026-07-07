from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass, field

@dataclass
class StrategyResult:
    strategy_name: str
    signal: str
    score: float
    confidence: float
    reasoning: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

class BaseStrategy(ABC):
    def __init__(self, name: str):
        self.name = name
        self.weight = 1.0

    @abstractmethod
    def analyze(self, df: pd.DataFrame, symbol: str, timeframe: str) -> StrategyResult:
        pass

    def calculate_stop_loss(self, df, side):
        if df is None or len(df) < 14: return 2.5
        atr = self._atr(df, 14)
        cp = df["close"].iloc[-1]
        av = atr.iloc[-1] if not pd.isna(atr.iloc[-1]) else cp * 0.02
        sl = av * 2 / cp * 100
        return max(1.0, min(sl, 10.0))

    def calculate_take_profit(self, df, side, rr=2.5):
        sl = self.calculate_stop_loss(df, side)
        return max(2.0, min(sl * rr, 20.0))

    def calculate_leverage(self, confidence, volatility):
        if confidence > 80 and volatility < 0.03: return 3.0
        elif confidence > 70 and volatility < 0.04: return 2.0
        elif confidence > 60 and volatility < 0.05: return 1.5
        return 1.0

    def _atr(self, df, period=14):
        h, l, c = df["high"], df["low"], df["close"]
        tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
        return tr.rolling(period).mean()
