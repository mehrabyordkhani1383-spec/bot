"""
⚡ Indicator Cache v3.2 - Performance Optimization (Point 11)
Cache expensive indicator calculations to reduce CPU/RAM
"""
import pandas as pd
import numpy as np
from functools import lru_cache
import hashlib

# In-memory cache for dataframes
_df_cache = {}
_cache_hits = 0
_cache_miss = 0

def _df_hash(df):
    """Fast hash for dataframe - last 5 closes"""
    try:
        return hashlib.md5(
            f"{df['close'].iloc[-5:].sum()}_{len(df)}_{df['close'].iloc[-1]}".encode()
        ).hexdigest()[:12]
    except:
        return str(id(df))

def cached_indicator(df, name, func, *args, **kwargs):
    """Generic indicator cache"""
    global _cache_hits, _cache_miss
    key = f"{_df_hash(df)}_{name}_{args}_{tuple(sorted(kwargs.items()))}"
    if key in _df_cache:
        _cache_hits += 1
        return _df_cache[key]
    _cache_miss += 1
    result = func(df, *args, **kwargs)
    # LRU eviction - keep last 200
    if len(_df_cache) > 200:
        # remove oldest 50
        for k in list(_df_cache.keys())[:50]:
            del _df_cache[k]
    _df_cache[key] = result
    return result

def rsi(close, period=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def ema(close, period):
    return close.ewm(span=period).mean()

def atr(df, period=14):
    h, l, c = df['high'], df['low'], df['close']
    tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def get_cache_stats():
    return {"hits": _cache_hits, "miss": _cache_miss, "size": len(_df_cache), "hit_rate": round(_cache_hits / max(1, _cache_hits + _cache_miss) * 100, 1)}

def clear_cache():
    global _df_cache, _cache_hits, _cache_miss
    _df_cache.clear()
    _cache_hits = _cache_miss = 0
