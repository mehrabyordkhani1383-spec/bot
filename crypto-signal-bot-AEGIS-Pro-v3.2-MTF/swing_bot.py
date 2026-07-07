"""
🎯 AEGIS Pro Bot v3.2 - Multi-Timeframe
15m / 30m / 1h / 4h / 1d | Confidence dynamic | ارسال فوری
"""
import time
from datetime import datetime, timedelta
from loguru import logger
import warnings
warnings.filterwarnings("ignore")

from signal_generator import SignalGenerator, FinalSignal
from telegram_bot import TelegramSignalBot
from config import config


class SwingBot:
    def __init__(self):
        self.name = "🎯 AEGIS Pro Bot v3.2"
        self.generator = SignalGenerator()
        self.telegram = TelegramSignalBot()
        
        self.coins = config.SWING_COINS
        self.timeframes = config.SCAN_TIMEFRAMES
        self.sent_signals = {}  # key -> timestamp
        self.scan_count = 0
        
        logger.info(f"{'='*55}")
        logger.info(f"  {self.name}")
        logger.info(f"  📊 {len(self.coins)} coins | {' / '.join(self.timeframes)}")
        logger.info(f"  🎯 Min Conf: {config.MIN_CONFIDENCE}% (TF adaptive)")
        logger.info(f"  📤 Send: INSTANT")
        logger.info(f"{'='*55}")
        
        self._test_telegram()
    
    def _test_telegram(self):
        try:
            import requests
            if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHANNEL_ID:
                r = requests.post(
                    f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": config.TELEGRAM_CHANNEL_ID,
                        "text": f"🎯 <b>AEGIS Pro v3.2 Started</b>\n📊 {len(self.coins)} coins | {' / '.join(self.timeframes)}\n🎯 Min Conf adaptive | ✅ MTF confirmed",
                        "parse_mode": "HTML"
                    }, timeout=10
                )
                if r.status_code == 200:
                    logger.success("✅ Telegram test OK")
                else:
                    logger.warning(f"Telegram test failed: {r.status_code} {r.text[:100]}")
                    logger.warning("⚠️ Check TELEGRAM_BOT_TOKEN in .env - token may be revoked!")
        except Exception as e:
            logger.warning(f"Telegram test: {e}")

    def start(self, interval_seconds: int = 300):
        """default 5 min for multi-TF"""
        logger.info(f"⏰ Started - scanning every {interval_seconds}s")
        try:
            while True:
                self.scan_count += 1
                self._scan_cycle()
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("🛑 Stopped")

    def _scan_cycle(self):
        start = time.time()
        found = 0
        logger.info(f"🔄 Scan #{self.scan_count} @ {datetime.now().strftime('%H:%M:%S')}")
        
        # Scan high TF first (quality), then low TF
        for tf in self.timeframes:
            tf_found = 0
            for symbol in self.coins:
                try:
                    signal = self.generator.analyze_single(symbol, tf)
                    if signal and self._is_unique(signal, tf):
                        self._send(signal)
                        found += 1
                        tf_found += 1
                        time.sleep(0.8)
                        # Limit signals per cycle to avoid spam
                        if found >= 3:
                            break
                except Exception:
                    continue
            if tf_found > 0:
                logger.info(f"  {tf}: {tf_found} signals")
            if found >= 3:
                break
        
        elapsed = time.time() - start
        if found:
            logger.success(f"🔥 Sent {found} signals | {elapsed:.0f}s")
        else:
            logger.info(f"📭 No quality signals | {elapsed:.0f}s")
        
        self._cleanup()

    def _is_unique(self, signal: FinalSignal, timeframe: str) -> bool:
        # Cooldown depends on TF
        tf_cooldown = {
            "15m": 1800,   # 30 min
            "30m": 3600,   # 1h
            "1h": 7200,    # 2h
            "4h": 14400,   # 4h
            "1d": 43200,   # 12h
        }
        cooldown = tf_cooldown.get(timeframe, 7200)
        key = f"{signal.symbol}_{signal.action}_{timeframe}"
        if key in self.sent_signals:
            elapsed = (datetime.now() - self.sent_signals[key]).total_seconds()
            if elapsed < cooldown:
                return False
        return True

    def _send(self, signal: FinalSignal):
        tf = signal.timeframe
        key = f"{signal.symbol}_{signal.action}_{tf}"
        self.sent_signals[key] = datetime.now()
        
        em = "🟢" if signal.action == "BUY" else "🔴"
        logger.success(f"📤 {em} {signal.symbol} {signal.action} | {signal.confidence:.0f}% | {tf} | {signal.entry_timing}")
        
        try:
            result = self.telegram.send_signal(signal)
            if result:
                logger.success(f"✅ Sent!")
            else:
                logger.error("❌ Send failed - Check TELEGRAM_BOT_TOKEN in .env ! Token may be revoked.")
                logger.error(f"   Token set: {'Yes' if config.TELEGRAM_BOT_TOKEN else 'No - EMPTY!'}")
                logger.error(f"   Channel: {config.TELEGRAM_CHANNEL_ID}")
        except Exception as e:
            logger.error(f"Send error: {e}")

    def _cleanup(self):
        now = datetime.now()
        expired = [k for k, v in self.sent_signals.items() if (now - v).total_seconds() > 86400]
        for k in expired:
            del self.sent_signals[k]


if __name__ == "__main__":
    bot = SwingBot()
    bot.start(interval_seconds=config.SCAN_INTERVAL_MINUTES * 60)
