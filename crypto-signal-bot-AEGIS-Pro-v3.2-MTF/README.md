# 🚀 AEGIS Pro v3.2 - Crypto Signal Bot

دستیار هوشمند سیگنال‌دهی کریپتو - Multi-Timeframe

یک ربات فوق‌پیشرفته که بازار کریپتو را با **۲۰+ موتور تحلیل** بررسی کرده و فقط بهترین سیگنال‌ها را با **وین‌ریت بالا** ارسال میکند!

## ✨ ویژگی‌ها

| نوع تحلیل | توضیح |
|-----------|-------|
| 📈 **تکنیکال Pro** | ۱۵+ اندیکاتور + Swing Structure واقعی |
| 🤖 **هوش مصنوعی** | Random Forest + Gradient Boosting |
| 🎯 **۵ استراتژی** | Trend, Mean Reversion, Breakout, Momentum, Divergence |
| 💰 **Smart Money** | BOS, CHOCH, Liquidity Sweep, Order Block, FVG, Premium/Discount |
| 📊 **Multi-Timeframe** | 15m / 30m / 1h / 4h / 1d با تایید کراس‌تایم‌فریم |
| 🛡️ **ریسک ATR+SR** | SL/TP داینامیک بر اساس ATR + Swing + Liquidity |

### 🏆 سیستم سیگنال
- فقط سیگنال‌های **80%+ Confidence** (15m: 84% / 1h: 80% / 4h: 78%)
- ترکیب: تکنیکال + AI + استراتژی‌ها + Smart Money
- **Entry Timing**: Immediate / Wait Pullback / Wait Candle Close
- **TP Management**: TP1 30% + BE / TP2 30% + Trailing / TP3 Rest
- ارسال **فوری** به محض پیدا شدن سیگنال

---

## 🛠️ نصب

```bash
cd crypto-signal-bot
pip install -r requirements.txt
cp .env.example .env
# ⚠️ توکن تلگرام رو تو .env بذار - توکن لو رفته قبلی باطل شده!
# TELEGRAM_BOT_TOKEN=...
# TELEGRAM_CHANNEL_ID=@your_channel
```

**⚠️ مشکل Send failed؟**
1. توکن رو از @BotFather دوباره بگیر (توکن قبلی لو رفته)
2. ربات باید ادمین کانال باشه
3. تست: `curl "https://api.telegram.org/bot<TOKEN>/sendMessage?chat_id=@your_channel&text=test"`

---

## 🚀 اجرا

```bash
# اجرای Multi-TF Bot (پیشنهادی)
python main.py

# اسکن یکباره همه تایم‌فریم‌ها
python main.py --scan-now

# تحلیل یک ارز خاص
python main.py --symbol BTCUSDT

# آموزش هوش مصنوعی
python main.py --train

# بک‌تست حرفه‌ای (Fee/Slippage/TP1-3/Trail/Sharpe)
python main.py --backtest
```

---

## 📊 تایم‌فریم‌ها

پیش‌فرض: `4h → 1h → 30m → 15m → 1d`

برای تغییر، فایل `config.py`:
```python
SCAN_TIMEFRAMES = ["4h", "1h", "30m", "15m"]  # به ترتیب اولویت
```

آستانه Confidence تطبیقی:
- 15m: 84%
- 30m: 82%
- 1h: 80%
- 4h: 78%
- 1d: 75%

سیگنال‌های تایم پایین فقط وقتی صادر میشن که با تایم بالاتر هم‌جهت باشن (MTF confirm).

---

## 📈 نمونه سیگنال تلگرام

```
🟢 LONG BTCUSDT | ▓▓▓▓▓▓▓▓░░ 84%

💵 ورود: 67234.5000
🎯 TP1: 67845.2000 (+0.9%)
🎯 TP2: 68290.1000 (+1.6%)
🏆 TP3: 68750.0000 (+2.3%)
🛑 SL: 66780.0000 (-0.7%)

⏳ 🟢 Immediate Entry
⌛ اعتبار: 2 candle 1h
📊 R/R 1:2.5 | ⚡ 3x | ⏱ 1h
```

---

## 📊 ساختار پروژه

```
crypto-signal-bot/
├── main.py                 # 🚀 ورودی
├── config.py               # 📋 تنظیمات + TF list
├── signal_generator.py     # 🎯 موتور سیگنال v3.2 Pro
├── telegram_bot.py         # 🤖 تلگرام + TP1/2/3
├── swing_bot.py           # ⏰ Multi-TF scanner
├── backtest.py            # 📊 Backtest Pro
├── analysis/
│   ├── technical.py
│   ├── ai_analyzer.py
│   └── indicator_cache.py # ⚡ Cache
├── engines/
│   ├── trend_engine.py          # Swing HH/HL
│   ├── momentum_engine.py       # Divergence Swing
│   ├── smart_money.py           # BOS/CHOCH/OB/FVG/Liquidity
│   ├── market_regime.py         # 6 regimes + Choppiness
│   ├── risk_engine.py           # ATR+SR+Liquidity
│   ├── scoring_engine.py        # Dynamic weights + BUY/SELL independent
│   ├── multi_timeframe.py       # MTF confirm
│   └── ...
└── strategies/
    ├── trend_following.py
    ├── mean_reversion.py
    ├── breakout.py
    ├── momentum.py
    └── divergence.py
```

---

> AEGIS Pro v3.2 – ساخته شده با ❤️ برای جامعه کریپتو ایران
