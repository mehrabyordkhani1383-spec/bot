"""
📋 Crypto Signal Bot - Configuration Module v3.2 AEGIS Pro
Multi-Timeframe: 15m / 30m / 1h / 4h / 1d
"""

import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()


class Config:
    # ==================== TELEGRAM ====================
    # SECURITY: Token MUST be set in .env - hardcoded tokens are revoked!
    # Get new token from @BotFather if send fails
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "")
    USER_CHAT_ID = os.getenv("USER_CHAT_ID", "")

    # ==================== TIMING ====================
    # Multi-TF mode
    SCAN_INTERVAL_MINUTES = int(os.getenv("SCAN_INTERVAL_MINUTES", "5"))

    # ==================== SIGNAL FILTERS ====================
    # High quality only - increased for low TFs
    TOP_SIGNALS_COUNT = int(os.getenv("TOP_SIGNALS_COUNT", "1"))
    MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "80.0"))

    # Timeframe-specific confidence thresholds (quality filter for low TF)
    TF_MIN_CONFIDENCE = {
        "15m": 84.0,
        "30m": 82.0,
        "1h": 80.0,
        "4h": 78.0,
        "1d": 75.0,
    }

    # Strategy consensus
    MIN_STRATEGY_AGREEMENT = int(os.getenv("MIN_STRATEGY_AGREEMENT", "2"))

    # AI confirmation
    REQUIRE_AI_CONFIRMATION = os.getenv("REQUIRE_AI_CONFIRMATION", "true").lower() == "true"
    MIN_AI_PROBABILITY = float(os.getenv("MIN_AI_PROBABILITY", "60.0"))

    # ==================== RISK MANAGEMENT ====================
    DEFAULT_STOP_LOSS_PERCENT = float(os.getenv("DEFAULT_STOP_LOSS_PERCENT", "1.8"))
    DEFAULT_TAKE_PROFIT_PERCENT = float(os.getenv("DEFAULT_TAKE_PROFIT_PERCENT", "3.6"))
    MAX_LEVERAGE = float(os.getenv("MAX_LEVERAGE", "10"))

    RISK_REWARD_RATIO = 2.0
    ATR_SL_MULTIPLIER = 1.8
    ATR_TP_MULTIPLIER = 3.6

    # ==================== ANALYSIS SETTINGS ====================
    # Multi-Timeframe support - Point 9
    TIMEFRAMES = {
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "4h": "4h",
        "1d": "1d",
    }

    # Scan order: high TF first (quality), then low TF
    SCAN_TIMEFRAMES = ["4h", "1h", "30m", "15m", "1d"]

    CANDLES_COUNT = {
        "15m": 150,
        "30m": 150,
        "1h": 200,
        "4h": 200,
        "1d": 200,
    }

    # Top liquid coins
    TOP_COINS = [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
        "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "LINKUSDT", "DOTUSDT",
        "UNIUSDT", "ATOMUSDT", "LTCUSDT", "ETCUSDT", "NEARUSDT",
        "APTUSDT", "ARBUSDT", "OPUSDT", "INJUSDT", "TIAUSDT",
        "SUIUSDT", "FILUSDT", "TRXUSDT", "XLMUSDT", "SEIUSDT",
    ]

    SWING_COINS = TOP_COINS

    STRATEGY_WEIGHTS = {
        "trend_following": 1.2,
        "mean_reversion": 0.9,
        "breakout": 1.1,
        "momentum": 1.0,
        "divergence": 1.3,
    }

    @classmethod
    def get_min_confidence_for_tf(cls, timeframe: str) -> float:
        """Timeframe-specific confidence threshold"""
        base = cls.MIN_CONFIDENCE
        tf_min = cls.TF_MIN_CONFIDENCE.get(timeframe, base)
        return max(base, tf_min)


config = Config()
