"""
🏛️ Base Engine - کلاس پایه برای همه موتورها
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class EngineResult:
    name: str
    score: float  # 0-100
    signal: str  # BULLISH, BEARISH, NEUTRAL
    details: Dict = field(default_factory=dict)
    reasons: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "name": self.name,
            "score": self.score,
            "signal": self.signal,
            "details": self.details,
            "reasons": self.reasons[:5]
        }

class BaseEngine:
    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight

    def analyze(self, df, symbol: str, timeframes: dict = None) -> EngineResult:
        raise NotImplementedError
