"""
⏰ Scheduler
"""

import time
import schedule
from datetime import datetime
from typing import List, Callable, Optional
from loguru import logger
from config import config


class SignalScheduler:
    def __init__(self, scan_function: Callable, send_function: Callable):
        self.scan_function = scan_function
        self.send_function = send_function
        self.is_running = False
        self.scan_count = 0
        self.last_scan = None
        self.history = []

    def start(self, interval_minutes: int = None):
        if interval_minutes is None: interval_minutes = config.SCAN_INTERVAL_MINUTES
        self.is_running = True
        logger.info(f"⏰ Scheduler started - scanning every {interval_minutes} minutes")
        
        logger.info("🔄 Running initial scan...")
        self._run()
        
        schedule.every(interval_minutes).minutes.do(self._run)
        
        try:
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 Stopped by user")
            self.is_running = False
        except Exception as e:
            logger.error(f"❌ Scheduler error: {e}")
            self.is_running = False

    def stop(self):
        self.is_running = False

    def _run(self):
        try:
            self.scan_count += 1
            self.last_scan = datetime.now()
            logger.info(f"🔄 Scan #{self.scan_count} at {self.last_scan}")
            
            signals = self.scan_function()
            if signals:
                sent = self.send_function(signals)
                logger.info(f"✅ Sent {sent} signals")
            else:
                logger.info("📭 No strong signals")
        except Exception as e:
            logger.error(f"❌ Scan error: {e}")
            import traceback; logger.error(traceback.format_exc())

    def get_stats(self):
        return {"scans": self.scan_count, "last_scan": self.last_scan, "running": self.is_running}
