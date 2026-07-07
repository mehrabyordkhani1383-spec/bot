"""
📊 Data Fetcher - دریافت داده از صرافی‌ها
پشتیبانی از Kraken, KuCoin, OKX, Gate
"""

import pandas as pd
import numpy as np
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import ccxt
from loguru import logger


class DataFetcher:
    # In-memory LRU cache - Point 11 Optimization
    _mem_cache = {}
    _mem_cache_ts = {}
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.exchange_names = ['kraken', 'kucoin', 'okx', 'gate', 'bitget']

    def _get_exchange(self, name):
        """ایجاد یک نمونه از صرافی"""
        try:
            ex = getattr(ccxt, name)({
                'enableRateLimit': True,
                'timeout': 15000,
            })
            return ex
        except:
            return None

    def _normalize_symbol(self, symbol: str) -> str:
        """تبدیل BTCUSDT به BTC/USDT"""
        if '/' in symbol:
            return symbol
        # Try common patterns
        for quote in ['USDT', 'USD', 'BTC', 'ETH']:
            if symbol.endswith(quote) and symbol != quote:
                base = symbol[:-len(quote)]
                return f"{base}/{quote}"
        return symbol

    def fetch_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = None, use_cache: bool = True) -> Optional[pd.DataFrame]:
        """
        دریافت داده‌های قیمت با failover بین صرافی‌ها
        با کش هوشمند بر اساس تایم‌فریم
        """
        from config import config
        if limit is None:
            limit = config.CANDLES_COUNT.get(timeframe, 100)
        
        symbol_norm = self._normalize_symbol(symbol)
        
        # کش هوشمند: تایم‌فریم پایین‌تر = کش کوتاه‌تر
        cache_ttl = {"5m": 20, "15m": 30, "30m": 45, "1h": 60, "4h": 120, "1d": 600}
        ttl = cache_ttl.get(timeframe, 60)
        
        # In-memory cache check - Point 11 Optimization
        mem_key = f"{symbol_norm}_{timeframe}_{limit}"
        now = time.time()
        if use_cache and mem_key in DataFetcher._mem_cache:
            ts, cached_df = DataFetcher._mem_cache[mem_key]
            if now - ts < ttl:
                return cached_df.copy()  # return copy to avoid mutation
        
        cache_file = self.cache_dir / f"{symbol_norm.replace('/', '_')}_{timeframe}_{limit}.parquet"
        if use_cache and cache_file.exists():
            cache_age = time.time() - cache_file.stat().st_mtime
            if cache_age < ttl:
                try:
                    return pd.read_parquet(cache_file)
                except:
                    pass

        # تلاش با صرافی‌های مختلف
        last_error = ""
        for name in self.exchange_names:
            try:
                ex = self._get_exchange(name)
                if ex is None:
                    continue
                
                # بررسی وجود symbol در صرافی
                try:
                    ex.load_markets()
                except:
                    pass
                
                if symbol_norm not in ex.symbols:
                    # تلاش با فرمت‌های مختلف
                    found = False
                    for s in ex.symbols:
                        if s.replace('/', '').upper() == symbol_norm.replace('/', '').upper():
                            symbol_norm = s
                            found = True
                            break
                    if not found:
                        continue

                ohlcv = ex.fetch_ohlcv(symbol_norm, timeframe, limit=limit)
                if ohlcv and len(ohlcv) > 20:
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df = df.sort_values('timestamp').reset_index(drop=True)
                    
                    try:
                        df.to_parquet(cache_file)
                    except:
                        pass
                    
                    logger.info(f"✅ {name}: {len(df)} candles for {symbol_norm} {timeframe}")
                    # Save to memory cache
                    DataFetcher._mem_cache[mem_key] = (time.time(), df.copy())
                    # LRU cleanup
                    if len(DataFetcher._mem_cache) > 100:
                        oldest = sorted(DataFetcher._mem_cache.items(), key=lambda x: x[1][0])[:20]
                        for k, _ in oldest:
                            DataFetcher._mem_cache.pop(k, None)
                    return df
                    
            except Exception as e:
                last_error = str(e)[:80]
                continue

        logger.warning(f"⚠️ No data for {symbol_norm} {timeframe}: {last_error}")
        return None

    def fetch_multiple(self, symbol: str, timeframes: List[str] = None) -> Dict[str, pd.DataFrame]:
        if timeframes is None:
            timeframes = ["15m", "1h", "4h", "1d"]
        result = {}
        for tf in timeframes:
            lim = 365 if tf == "1d" else 200
            df = self.fetch_ohlcv(symbol, tf, limit=lim)
            if df is not None:
                result[tf] = df
                time.sleep(0.3)
        return result

    def get_current_price(self, symbol: str) -> Optional[float]:
        symbol_norm = self._normalize_symbol(symbol)
        for name in self.exchange_names:
            try:
                ex = self._get_exchange(name)
                if ex is None: continue
                ticker = ex.fetch_ticker(symbol_norm)
                if ticker and ticker.get('last'):
                    return float(ticker['last'])
            except:
                continue
        return None


def get_data(symbol: str, timeframe: str = "1h", limit: int = 200) -> Optional[pd.DataFrame]:
    return DataFetcher().fetch_ohlcv(symbol, timeframe, limit)
