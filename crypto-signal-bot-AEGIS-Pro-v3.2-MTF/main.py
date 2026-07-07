"""
🚀 Crypto Signal Bot v3.1 SWING
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path
from loguru import logger

from config import config
from signal_generator import SignalGenerator
from telegram_bot import TelegramSignalBot
from scheduler import SignalScheduler

logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level:^8}</level> | <cyan>{message}</cyan>", level="INFO", colorize=True)
logger.add("data/logs/bot_{time:YYYY-MM-DD}.log", rotation="1 day", retention="7 days", level="INFO")


class CryptoSignalBot:
    def __init__(self):
        self.name = "🎯 Crypto Signal Bot v3.1 SWING"
        self.generator = SignalGenerator()
        self.telegram = TelegramSignalBot()
        self.scheduler = None
        logger.info(f"{'='*50}")
        logger.info(f"  {self.name}")
        logger.info(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"  Min Conf: {config.MIN_CONFIDENCE}% | Top: {config.TOP_SIGNALS_COUNT}")
        logger.info(f"{'='*50}")

    def scan_and_send(self, symbols=None):
        logger.info("🔍 Scanning market...")
        signals = self.generator.get_top_signals(symbols)
        if signals:
            for s in signals:
                logger.info(f"🏆 {s.symbol} {s.action} | Conf: {s.confidence:.0f}%")
            # signals already sent instantly in scan_market
            logger.info(f"📤 {len(signals)} signals")
        else:
            logger.info("📭 No strong signals")
        return signals

    def scan_once(self, symbol=None):
        if symbol:
            # try 4h then 1h
            signal = self.generator.analyze_single(symbol.upper(), "4h")
            if not signal:
                signal = self.generator.analyze_single(symbol.upper(), "1h")
            if signal:
                self.telegram.send_signal(signal)
                logger.info(f"✅ Signal for {symbol}")
            else:
                logger.info(f"❌ No signal for {symbol}")
        else:
            self.scan_and_send()

    def train(self):
        logger.info("🧠 Training AI models...")
        from data.fetcher import DataFetcher
        fetcher = DataFetcher()
        df = fetcher.fetch_ohlcv("BTCUSDT", "1d", limit=500)
        if df is not None and self.generator.ai_analyzer:
            results = self.generator.ai_analyzer.train(df)
            if "error" not in results:
                for m, r in results.items():
                    logger.success(f"  {m}: Accuracy={r['accuracy']:.2%}")
            else:
                logger.warning(f"⚠️ {results['error']}")
        else:
            logger.error("❌ Could not fetch training data")


def main():
    parser = argparse.ArgumentParser(description="Crypto Signal Bot v3.1")
    parser.add_argument("--scan-now", action="store_true", help="Scan once")
    parser.add_argument("--symbol", type=str, help="Analyze a symbol")
    parser.add_argument("--train", action="store_true", help="Train AI")
    parser.add_argument("--backtest", action="store_true", help="Run backtest")
    parser.add_argument("--swing", action="store_true", help="Run SWING bot")
    args = parser.parse_args()

    Path("data/logs").mkdir(parents=True, exist_ok=True)
    Path("data/cache").mkdir(parents=True, exist_ok=True)
    Path("data/models").mkdir(parents=True, exist_ok=True)

    bot = CryptoSignalBot()

    if args.train:
        bot.train()
    elif args.backtest:
        from backtest import Backtester
        bt = Backtester()
        bt.run_bulk(timeframe="4h")
        bt.run_bulk(timeframe="1h")
    elif args.symbol:
        bot.scan_once(args.symbol.upper())
    elif args.scan_now:
        bot.scan_and_send()
    elif args.swing:
        from swing_bot import SwingBot
        swing = SwingBot()
        swing.start(interval_seconds=config.SCAN_INTERVAL_MINUTES * 60)
    else:
        # Default: Swing Bot
        logger.info("🎯 Starting SWING BOT v3.1 - Default mode")
        from swing_bot import SwingBot
        swing = SwingBot()
        swing.start(interval_seconds=config.SCAN_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    main()
