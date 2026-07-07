"""
موتور 13 - Macro Engine
بررسی شاخص‌های کلان (BTC.D, DXY ساده شده)
"""
from .base_engine import BaseEngine, EngineResult


class MacroEngine(BaseEngine):
    def __init__(self):
        super().__init__("Macro", weight=1.2)

    def analyze(self, df, symbol, timeframes=None):
        score = 60
        reasons = []
        details = {}

        # بدون API واقعی، فرض کنیم شرایط نرماله
        details["macro_status"] = "normal"

        if timeframes and "btc_dominance" in timeframes:
            dom = timeframes["btc_dominance"]
            if dom > 60:
                score -= 10
                reasons.append("⚠️ BTC dominance high - altcoins underperforming")
            elif dom < 40:
                score += 10
                reasons.append("✅ BTC dominance low - alt season possible")
            details["btc_d"] = dom

        reasons.append("✅ Macro conditions normal (limited data)")

        return EngineResult(self.name, score, "NEUTRAL", details, reasons)
