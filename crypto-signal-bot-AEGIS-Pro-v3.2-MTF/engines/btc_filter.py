"""
موتور 10 - BTC Filter Engine
بررسی هم‌جهتی با بیت‌کوین
"""
from .base_engine import BaseEngine, EngineResult


class BTCFilterEngine(BaseEngine):
    def __init__(self):
        super().__init__("BTC Filter", weight=2.0)

    def analyze(self, df, symbol, timeframes=None):
        # در حالت عادی باید BTC رو جداگانه تحلیل کنه
        # اینجا ساده شده - از timeframes برچسب BTC رو میگیره
        reasons = []
        details = {}

        # اگر خودش BTC باشه
        if "BTC" in symbol.upper() and "USDT" in symbol.upper():
            details["is_btc"] = True
            return EngineResult(self.name, 70, "NEUTRAL", details, ["✅ BTCUSDT - no filter needed"])

        # بررسی وضعیت BTC از timeframes
        btc_result = None
        if timeframes and "btc" in timeframes:
            btc_result = timeframes["btc"]

        if btc_result:
            btc_score = btc_result.score if hasattr(btc_result, 'score') else btc_result.get("score", 50)
            btc_signal = btc_result.signal if hasattr(btc_result, 'signal') else btc_result.get("signal", "NEUTRAL")

            details["btc_score"] = btc_score
            details["btc_signal"] = btc_signal

            if btc_score > 60:
                reasons.append("✅ BTC is bullish - alt season favorable")
                return EngineResult(self.name, 80, "BULLISH", details, reasons)
            elif btc_score < 40:
                reasons.append("❌ BTC is bearish - avoid altcoins")
                return EngineResult(self.name, 20, "BEARISH", details, [])
            else:
                reasons.append("➡️ BTC is neutral")
                return EngineResult(self.name, 50, "NEUTRAL", details, reasons)

        # بدون اطلاعات BTC، فرض کنیم خوبه
        return EngineResult(self.name, 60, "NEUTRAL", details, ["⚠️ No BTC data available - skipping filter"])
