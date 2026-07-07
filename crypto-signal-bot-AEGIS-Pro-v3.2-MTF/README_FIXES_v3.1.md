# Crypto Signal Bot v3.1 SWING - تغییرات

## 🔴 باگ های بحرانی که فیکس شد

1. **توکن تلگرام هاردکد** - `config.py`
   - قبل: `TELEGRAM_BOT_TOKEN = os.getenv(..., "8937083269:AA...")`
   - بعد: فقط از `.env` میخونه، خالی باشه fail میشه
   - ⚠️ حتما توکن جدید از @BotFather بگیرید

2. **Confidence فیک**
   - قبل: `confidence = min(100, confidence * 1.15 + 5)` 
   - بعد: فرمول واقعی، بدون باد کردن
   - Engine_score*0.4 + direction*0.35 + agreement*0.25

3. **فیلتر SELL خراب**
   - قبل: `critical_ok` فقط برای BULLISH زیاد میشد → سیگنال SELL هیچوقت رد نمیشد
   - بعد: برای BUY و SELL جداگانه چک میکنه
   - الان هم LONG هم SHORT میده

4. **موتورهای فیک حذف شد**
   - حذف: NewsEngine, MacroEngine, BTCFilterEngine, MultiTimeframeEngine, SessionEngine
   - موند: Trend, Momentum, Volume, PriceAction, SmartMoney, Volatility, Liquidity, Risk, MarketRegime
   - 9 موتور واقعی

5. **AI + Strategies وصل شد**
   - قبل: کلا استفاده نمیشد
   - بعد: 
     - AI Analyzer (Random Forest / GB) پیش‌بینی میکنه
     - 5 استراتژی: trend_following, mean_reversion, breakout, momentum, divergence
     - حداقل 2 استراتژی باید موافق باشن
     - AI باید تایید کنه (قابل خاموش کردن)

6. **مدیریت ریسک ATR**
   - قبل: SL ثابت 2.5% / TP = SL*2.5
   - بعد: 
     - ATR(14) * 1.8 = SL
     - TP = SL * 2.0 (R/R 1:2)
     - SL بین 1.2% تا 3.5%
   - اهرم محافظه‌کارانه: 2x-7x (قبلا تا 15x)

7. **اسکلپ 5m → Swing 1h/4h**
   - scalp_bot.py → swing_bot.py
   - تایم فریم: 4h + 1h
   - Cooldown: 4 ساعت (قبلا 20 دقیقه)
   - کوین‌ها: 25 کوین نقدشونده برتر
   - اسکن هر 15 دقیقه

8. **ارسال فوری**
   - به محض پیدا شدن سیگنال 80%+ ارسال میشه
   - توی `scan_market()` بعد از هر سیگنال موفق `telegram.send_signal()` صدا زده میشه

9. **کیفیت بر کمیت**
   - MIN_CONFIDENCE: 75 → 80%
   - TOP_SIGNALS_COUNT: 3 → 1
   - Strategy agreement required
   - AI confirmation required
   - سیگنال کم، ولی معتبر

10. **بک‌تست**
    - فایل جدید: `backtest.py`
    - Walk-forward تست روی دیتای تاریخی
    - `python main.py --backtest`

---

## 🚀 اجرا

```bash
# 1. توکن جدید بذار
cp .env.example .env
nano .env  # TELEGRAM_BOT_TOKEN=...

# 2. نصب
pip install -r requirements.txt

# 3. تست یک ارز
python main.py --symbol BTCUSDT

# 4. بک‌تست
python main.py --backtest

# 5. اجرای Swing Bot
python main.py --swing
# یا ساده:
python main.py
```

## 📊 تنظیمات پیشنهادی

`.env`:
```
MIN_CONFIDENCE=80.0
MIN_STRATEGY_AGREEMENT=2
REQUIRE_AI_CONFIRMATION=true
MAX_LEVERAGE=10
SCAN_INTERVAL_MINUTES=15
```

اگر سیگنال خیلی کم شد:
- MIN_CONFIDENCE → 77
- REQUIRE_AI_CONFIRMATION=false

اگر سیگنال زیاد / فیک شد:
- MIN_CONFIDENCE → 85
- MIN_STRATEGY_AGREEMENT=3

---

## تفاوت نسخه قدیم vs جدید

|  | v2.0 قدیم | v3.1 جدید |
|---|---|---|
| تایم فریم | 5m / 15m | 1h / 4h |
| Confidence | فیک +15% | واقعی |
| SELL | ❌ نمیداد | ✅ میده |
| AI | ❌ استفاده نمیشد | ✅ فعال |
| Strategies | ❌ استفاده نمیشد | ✅ 5 تا فعال |
| SL/TP | ثابت | ATR داینامیک |
| Leverage | تا 15x | 2x-7x |
| سیگنال/روز | 20-50 | 1-5 |
| وین ریت هدف | ~45% | 60-70% |

---

ساخته شده برای جامعه کریپتو ایران ❤️
