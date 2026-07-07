"""
موتور 3 - Multi Timeframe Engine v3.2 Pro
بررسی هم‌جهتی تایم‌فریم بالاتر - تاثیر زیاد در تصمیم نهایی
"""
import pandas as pd
from .base_engine import BaseEngine, EngineResult


class MultiTimeframeEngine(BaseEngine):
    def __init__(self):
        super().__init__("Multi Timeframe", weight=2.2)  # وزن بالا - Point 9
        self._fetcher = None

    def _get_fetcher(self):
        if self._fetcher is None:
            from data.fetcher import DataFetcher
            self._fetcher = DataFetcher()
        return self._fetcher

    def _trend_direction(self, df):
        """تشخیص سریع روند"""
        if df is None or len(df) < 50:
            return "NEUTRAL", 50
        close = df['close']
        ema20 = close.ewm(span=20).mean().iloc[-1]
        ema50 = close.ewm(span=50).mean().iloc[-1]
        cp = close.iloc[-1]
        if cp > ema20 > ema50:
            return "BULLISH", 70
        elif cp < ema20 < ema50:
            return "BEARISH", 70
        elif cp > ema50:
            return "BULLISH", 55
        elif cp < ema50:
            return "BEARISH", 55
        return "NEUTRAL", 50

    def analyze(self, df, symbol, timeframes=None):
        # Determine current timeframe from df length / or passed in timeframes dict?
        # Simple heuristic: if we have 100-150 candles, assume 1h
        # Better: caller passes timeframe in timeframes={'current': '1h'}
        current_tf = "1h"
        if timeframes and isinstance(timeframes, dict) and "current" in timeframes:
            current_tf = timeframes["current"]
        
        # Map to higher timeframe
        tf_map = {"15m": "1h", "30m": "1h", "1h": "4h", "4h": "1d", "1d": "1d"}
        higher_tf = tf_map.get(current_tf, "4h")
        
        # Analyze current TF
        curr_sig, curr_score = self._trend_direction(df)
        
        # Fetch higher TF
        try:
            fetcher = self._get_fetcher()
            df_htf = fetcher.fetch_ohlcv(symbol, higher_tf, limit=100)
            if df_htf is not None and len(df_htf) >= 50:
                htf_sig, htf_score = self._trend_direction(df_htf)
            else:
                htf_sig, htf_score = "NEUTRAL", 50
        except Exception:
            htf_sig, htf_score = "NEUTRAL", 50

        reasons = []
        details = {
            "current_tf": current_tf,
            "higher_tf": higher_tf,
            "current_signal": curr_sig,
            "htf_signal": htf_sig,
            "aligned": False
        }

        # Alignment check - Point 9
        if curr_sig != "NEUTRAL" and curr_sig == htf_sig:
            score = 80
            details["aligned"] = True
            reasons.append(f"✅ MTF Aligned: {current_tf} {curr_sig} + {higher_tf} {htf_sig}")
            signal = curr_sig
        elif curr_sig != "NEUTRAL" and htf_sig == "NEUTRAL":
            score = 55
            details["aligned"] = False
            reasons.append(f"⚠️ HTF {higher_tf} neutral, {current_tf} {curr_sig}")
            signal = curr_sig
        elif curr_sig != "NEUTRAL" and htf_sig != "NEUTRAL" and curr_sig != htf_sig:
            # CONFLICT - penalize heavily - Point 9
            score = 20
            details["aligned"] = False
            reasons.append(f"❌ MTF CONFLICT: {current_tf} {curr_sig} vs {higher_tf} {htf_sig} - AVOID!")
            signal = "NEUTRAL"
        else:
            score = 45
            details["aligned"] = False
            reasons.append(f"➡️ MTF mixed / neutral")
            signal = "NEUTRAL"

        return EngineResult(self.name, score, signal, details, reasons)
