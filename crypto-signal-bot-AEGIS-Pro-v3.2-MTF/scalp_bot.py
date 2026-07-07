"""
⚡ SCALP BOT v4 - مانیتورینگ لحظه‌ای ۲۰۰+ ارز
فقط 75%+ | BUY + SELL | ارسال فوری تک‌تک
هر سیگنال همون موقع میره | اهرم 10x
"""
import time
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger
import warnings
warnings.filterwarnings("ignore")

from signal_generator import SignalGenerator, FinalSignal
from telegram_bot import TelegramSignalBot
from data.fetcher import DataFetcher
from config import config


# ===== ۲۰۰ ارز برتر =====
SCALP_COINS = [
    "BTC/USDT", "ETH/USDT", "XRP/USDT", "XMR/USDT", "SOL/USDT",
    "HYPE/USDT", "ZEC/USDT", "NEAR/USDT", "TAO/USDT", "AAVE/USDT",
    "LTC/USDT", "UNI/USDT", "BNB/USDT", "DOT/USDT", "AVAX/USDT",
    "PEPE/USDT", "ADA/USDT", "SEI/USDT", "DOGE/USDT", "TRX/USDT",
    "SUI/USDT", "LINK/USDT", "XLM/USDT", "WLD/USDT", "SHIB/USDT",
    "HBAR/USDT", "WIF/USDT", "FET/USDT", "ENA/USDT", "CHZ/USDT",
    "BONK/USDT", "INJ/USDT", "JUP/USDT", "ARB/USDT", "ONDO/USDT",
    "ATOM/USDT", "FIL/USDT", "TIA/USDT", "APT/USDT", "ALGO/USDT",
    "OP/USDT", "ETC/USDT", "FLOKI/USDT", "POPCAT/USDT", "POL/USDT",
    "STX/USDT", "CRV/USDT", "PENDLE/USDT", "JTO/USDT",
    "JASMY/USDT", "MANA/USDT", "SAND/USDT", "GALA/USDT", "AXS/USDT",
    "QTUM/USDT", "ZIL/USDT", "IOST/USDT", "IOTA/USDT", "ONT/USDT",
    "WAVES/USDT", "NEO/USDT", "VET/USDT", "THETA/USDT", "FTM/USDT",
    "EGLD/USDT", "KSM/USDT", "COMP/USDT", "MKR/USDT", "YFI/USDT",
    "BAL/USDT", "LRC/USDT", "ENJ/USDT", "HOT/USDT", "STMX/USDT",
    "DGB/USDT", "SC/USDT", "ANKR/USDT", "CELR/USDT", "MATIC/USDT",
    "1INCH/USDT", "GRT/USDT", "OCEAN/USDT", "ALICE/USDT", "CHR/USDT",
    "SFP/USDT", "ALPHA/USDT", "BEL/USDT", "DUSK/USDT", "NKN/USDT",
    "ARPA/USDT", "CTSI/USDT", "TOMO/USDT", "REN/USDT", "LIT/USDT",
    "STPT/USDT", "HIVE/USDT", "MDX/USDT", "DODO/USDT", "BAKE/USDT",
    "BURGER/USDT", "SUSHI/USDT", "CAKE/USDT", "PROM/USDT", "RLC/USDT",
    "CVC/USDT", "POWR/USDT", "POLY/USDT", "MTL/USDT", "LOOM/USDT",
    "SKL/USDT", "TRB/USDT", "BAND/USDT", "KAVA/USDT", "IRIS/USDT",
    "FET/USDT", "PAXG/USDT", "KSM/USDT", "AKT/USDT", "LUNC/USDT",
    "USTC/USDT", "LUNA/USDT", "ANC/USDT", "MIR/USDT", "MNT/USDT",
    "GLMR/USDT", "MOVR/USDT", "FLOW/USDT", "MINA/USDT", "API3/USDT",
    "RARE/USDT", "VOXEL/USDT", "C98/USDT", "CLV/USDT", "ATA/USDT",
    "GTC/USDT", "TORN/USDT", "BADGER/USDT", "DNT/USDT", "BNT/USDT",
    "SRM/USDT", "MAPS/USDT", "OXY/USDT", "FIDA/USDT", "COPE/USDT",
    "SAMO/USDT", "MEDIA/USDT", "MER/USDT", "SOL/USDT", "RAY/USDT",
    "SRM/USDT", "MNGO/USDT", "ORCA/USDT", "SYP/USDT", "ATLAS/USDT",
    "POLIS/USDT", "AURY/USDT", "weWIND/USDT", "SLIM/USDT", "SBR/USDT",
    "ZBC/USDT", "SCNSOL/USDT", "LARIX/USDT", "TULIP/USDT", "ABR/USDT",
    "PRISM/USDT", "PORT/USDT", "SHDW/USDT", "IN/USDT", "SONIC/USDT",
    "NEON/USDT", "WNT/USDT", "NATIVE/USDT", "GSWAP/USDT", "CYS/USDT",
    "STR/USDT", "CHICKS/USDT", "PIXL/USDT", "INTR/USDT", "LIKE/USDT",
    "DXL/USDT", "SLC/USDT", "FRKT/USDT", "SYP/USDT", "weWETH/USDT",
    "weWBTC/USDT", "weWETH/USDT", "weWSOL/USDT", "weWUSDT/USDT",
]


class ScalpBot:
    """
    ⚡ Scalp Bot v4 - ارسال فوری تک‌تک
    
    هر سیگنال 75%+ رو همون لحظه میفرسته
    بسته‌بندی نمیکنه، همه رو یکبار نمیفرسته
    """
    
    def __init__(self):
        self.name = "⚡ Scalp Bot v4"
        self.generator = SignalGenerator()
        self.telegram = TelegramSignalBot()
        
        self.scalp_coins = SCALP_COINS
        self.sent_signals = {}  # key -> timestamp
        self.scan_count = 0
        self.is_running = False
        self.min_confidence = 75.0
        
        # === تست تلگرام ===
        self._test_telegram()
        
        logger.info(f"{'='*55}")
        logger.info(f"  {self.name}")
        logger.info(f"  📊 {len(self.scalp_coins)} coins | 15m+5m")
        logger.info(f"  🎯 Min Confidence: {self.min_confidence}%")
        logger.info(f"  ⚡ Leverage: Up to 15x")
        logger.info(f"  📤 Send: INSTANT (one by one)")
        logger.info(f"{'='*55}")
    
    def _test_telegram(self):
        try:
            import requests
            if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHANNEL_ID:
                r = requests.post(
                    f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={
                        "chat_id": config.TELEGRAM_CHANNEL_ID,
                        "text": f"🔥 <b>AEGIS Scalp v4</b> started ✅\n📊 {len(self.scalp_coins)} coins | 🎯 75%+ | ⚡ 10x | 🚀 Real-time (<60s delay)",
                        "parse_mode": "HTML"
                    }, timeout=10
                )
                if r.status_code == 200:
                    logger.success("✅ Telegram test message sent!")
        except Exception as e:
            logger.warning(f"⚠️ Telegram test: {e}")
    
    def start(self, interval_seconds: int = 60):
        """شروع مانیتورینگ"""
        self.is_running = True
        logger.info(f"⏰ Started - scanning {len(self.scalp_coins)} coins every {interval_seconds}s")
        logger.info(f"🎯 Looking for 75%+ signals... INSTANT SEND ON FIND! 🔥")
        
        try:
            while self.is_running:
                self.scan_count += 1
                self._scan_and_send_instantly()
                
                # استراحت
                remaining = interval_seconds
                while remaining > 0 and self.is_running:
                    time.sleep(5)
                    remaining -= 5
                    
        except KeyboardInterrupt:
            logger.info("🛑 Stopped")
        except Exception as e:
            logger.error(f"❌ {e}")
            import traceback; logger.error(traceback.format_exc())
        finally:
            self.is_running = False
    
    def _scan_and_send_instantly(self):
        """
        اسکن میکنه. به محض پیدا شدن سیگنال 75%+،
        همون موقع میفرسته، بقیه ادامه پیدا میکنه
        """
        cycle_start = time.time()
        batch_signals = []
        batch_size = 0
        
        logger.info(f"🔄 Scan #{self.scan_count} @ {datetime.now().strftime('%H:%M:%S')}")
        
        # اسکن به صورت دسته‌های ۲۰ تایی برای سرعت
        batch_size = 20
        total_scanned = 0
        
        for i in range(0, len(self.scalp_coins), batch_size):
            batch = self.scalp_coins[i:i+batch_size]
            batch_found = []
            
            for symbol in batch:
                try:
                    # فقط ۵m برای سرعت (سریع‌ترین تایم)
                    signal = self.generator.analyze_single(symbol, "5m")
                    if signal and signal.confidence >= self.min_confidence:
                        batch_found.append(signal)
                        total_scanned += 1
                        continue
                    
                    # اگه ۵m نبود، ۱۵m رو چک کن
                    signal = self.generator.analyze_single(symbol, "15m")
                    if signal and signal.confidence >= self.min_confidence:
                        batch_found.append(signal)
                        total_scanned += 1
                        continue
                    
                    total_scanned += 1
                except:
                    continue
            
            # 📤 به محض پیدا شدن سیگنال در این دسته، فوری بفرست
            if batch_found:
                batch_found.sort(key=lambda s: s.confidence, reverse=True)
                best_in_batch = batch_found[0]
                
                if self._is_unique(best_in_batch):
                    self._send_immediately(best_in_batch)
                    batch_signals.append(best_in_batch)
        
        elapsed = time.time() - cycle_start
        
        if batch_signals:
            logger.success(f"🔥 Sent {len(batch_signals)} signals instantly! ({elapsed:.0f}s)")
        else:
            logger.info(f"📭 Scan #{self.scan_count}: No 75%+ signals ({elapsed:.0f}s)")
    
    def _send_immediately(self, signal: FinalSignal):
        """📤 ارسال فوری! همین لحظه!"""
        
        # جلوگیری از ارسال تکراری (۲۰ دقیقه)
        key = f"{signal.symbol}_{signal.action}"
        if key in self.sent_signals:
            elapsed = (datetime.now() - self.sent_signals[key]).total_seconds()
            if elapsed < 1200:  # 20 minutes
                logger.info(f"⏭️ {signal.symbol}: Already sent ({elapsed:.0f}s ago)")
                return
        
        em = "🟢" if signal.action == "BUY" else "🔴"
        
        # 📤 ارسال فوری به کانال + ربات
        logger.success(f"🔥🔥 INSTANT SEND: {em} {signal.symbol} {signal.action} | Conf:{signal.confidence:.0f}% | TF:{signal.timeframe} | Lev:{signal.leverage}x 💰")
        
        result = self.telegram.send_signal(signal)
        if result:
            logger.success(f"✅✅ {signal.symbol} SENT INSTANTLY!")
        else:
            logger.error(f"❌ FAILED to send {signal.symbol}")
        
        self.sent_signals[key] = datetime.now()
        
        # پاکسازی قدیمی‌ها
        self._cleanup()
    
    def _cleanup(self):
        now = datetime.now()
        expired = [k for k, v in self.sent_signals.items() if (now - v).total_seconds() > 7200]
        for k in expired: del self.sent_signals[k]


def run_scalp_bot():
    bot = ScalpBot()
    bot.start()


if __name__ == "__main__":
    run_scalp_bot()
