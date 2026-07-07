"""
موتور 9 - News Engine
بررسی اخبار مهم (API واقعی نداریم، از فیلتر ساده استفاده می‌کنیم)
"""
from datetime import datetime, timezone
from .base_engine import BaseEngine, EngineResult


class NewsEngine(BaseEngine):
    def __init__(self):
        super().__init__("News", weight=1.5)

    def analyze(self, df, symbol, timeframes=None):
        score = 70  # پیش‌فرض: خبر بدی نیست
        reasons = []
        details = {}

        # ===== اخبار مهم هفتگی (CryptoPanic API نداریم، لیست ثابت) =====
        # در نسخه واقعی باید API بزنه
        known_events = {
            # روزهای مشخص (روز-ماه: نام رویداد)
            "2-1": "FOMC Meeting",
            "14-2": "CPI Data",
            "15-3": "FOMC Decision",
            "1-4": "CPI Data",
            "7-5": "FOMC Meeting",
            "12-6": "CPI Data",
            "31-7": "FOMC Decision",
            "28-8": "CPI Data",
            "18-9": "FOMC Rate Decision",
            "30-10": "CPI Data",
            "7-11": "FOMC Meeting",
            "11-12": "CPI Data",
            "18-12": "FOMC Rate Decision",
        }

        now = datetime.now(timezone.utc)
        today = f"{now.day}-{now.month}"

        if today in known_events:
            score = 30
            reasons.append(f"⚠️ Major event today: {known_events[today]}")
            details["event"] = known_events[today]
        else:
            reasons.append("✅ No major events today")
            details["event"] = "none"

        # ===== آخر هفته =====
        if now.weekday() >= 5:
            score = min(score, 20)
            reasons.append("❌ Weekend - low liquidity, news may cause gaps")

        # ===== زمان انتشار داده‌های اقتصادی =====
        # هر پنجشنبه ساعت 13:30 UTC (claims) و روزهای خاص
        hour = now.hour
        day = now.weekday()

        # NFP: اولین جمعه هر ماه ساعت 12:30 UTC
        # CPI: روزهای مشخص
        # FOMC: 8 بار در سال

        details["risk_level"] = "low" if score > 60 else "medium" if score > 30 else "high"

        if details["risk_level"] == "high":
            reasons.append("❌ High risk news period - consider avoiding trades")

        return EngineResult(self.name, score, "NEUTRAL", details, reasons)
