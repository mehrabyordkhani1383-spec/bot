"""
موتور 8 - Session Engine
فیلتر سشن معاملاتی - فقط لندن و نیویورک
"""
from datetime import datetime, timezone, timedelta
from .base_engine import BaseEngine, EngineResult


class SessionEngine(BaseEngine):
    def __init__(self):
        super().__init__("Session", weight=1.5)

    def analyze(self, df, symbol, timeframes=None):
        now = datetime.now(timezone.utc)
        current_hour = now.hour
        current_min = now.minute
        current_time = current_hour * 60 + current_min  # minutes since midnight
        current_day = now.weekday()  # 0=Monday

        reasons = []
        details = {}

        # آخر هفته (شنبه و یکشنبه)
        if current_day >= 5:
            return EngineResult(self.name, 15, "NEUTRAL", {"session": "weekend"}, ["❌ Weekend - low liquidity"])

        # ===== سشن‌های معاملاتی (به وقت UTC) =====
        sessions = []

        # Asian Session: 00:00 - 09:00 UTC
        # London Session: 08:00 - 17:00 UTC
        # New York Session: 13:00 - 22:00 UTC
        # London/NY Overlap: 13:00 - 17:00 UTC (بیشترین حجم)

        asia_start = 0
        asia_end = 9 * 60  # 09:00
        london_start = 8 * 60  # 08:00
        london_end = 17 * 60  # 17:00
        ny_start = 13 * 60  # 13:00
        ny_end = 22 * 60  # 22:00

        session_name = "Unknown"
        session_score = 0

        if current_time >= ny_start and current_time <= london_end:
            # Overlap London + NY (13:00-17:00 UTC) - بهترین زمان
            session_name = "London/NY Overlap"
            session_score = 100
            reasons.append(f"✅ London/NY Overlap - Peak liquidity!")
        elif current_time >= london_start and current_time < ny_start:
            # فقط لندن (08:00-13:00)
            session_name = "London Only"
            session_score = 80
            reasons.append(f"✅ London session - Good liquidity")
        elif current_time >= ny_start and current_time <= ny_end:
            # فقط نیویورک (13:00-22:00)
            session_name = "New York Only"
            session_score = 75
            reasons.append(f"✅ New York session - Good liquidity")
        elif current_time >= asia_start and current_time < london_start:
            session_name = "Asia / Low Volume"
            session_score = 30
            reasons.append(f"⚠️ Asian session - Low liquidity")
        else:
            session_name = "Off Hours"
            session_score = 10
            reasons.append(f"❌ Off hours - Very low liquidity")

        details["session"] = session_name
        details["utc_time"] = f"{current_hour:02d}:{current_min:02d}"

        signal = "NEUTRAL"
        if session_score >= 75:
            signal = "BULLISH"  # زمان خوب برای معامله
        elif session_score <= 30:
            signal = "BEARISH"  # زمان بد برای معامله

        return EngineResult(self.name, session_score, signal, details, reasons)
