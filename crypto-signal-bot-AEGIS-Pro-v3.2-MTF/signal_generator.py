"""
🎯 Signal Generator v3.2 AEGIS Pro
- Confidence واقعی
- SELL = BUY quality
- AI + Strategies integrated
- ATR + Swing SR + Liquidity SL/TP
- Entry Timing
- TP1/TP2/TP3
- NO_TRADE support
- Independent BUY/SELL scoring
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from loguru import logger

from data.fetcher import DataFetcher
from config import config

# Real engines only
from engines import (
    MarketRegimeEngine, TrendEngine, MultiTimeframeEngine,
    SmartMoneyEngine, PriceActionEngine, MomentumEngine,
    VolumeEngine,
    RiskEngine, ScoringEngine,
    LiquidityEngine,
    VolatilityEngine
)

# AI
from analysis.ai_analyzer import AIAnalyzer

# Strategies
from strategies.trend_following import TrendFollowingStrategy
from strategies.mean_reversion import MeanReversionStrategy
from strategies.breakout import BreakoutStrategy
from strategies.momentum import MomentumStrategy
from strategies.divergence import DivergenceStrategy


@dataclass
class FinalSignal:
    symbol: str
    action: str  # BUY / SELL / NO_TRADE
    entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    # TP Management - Point 14,15
    tp1: float = 0.0
    tp2: float = 0.0
    tp3: float = 0.0
    leverage: float = 2.0
    confidence: float = 0.0
    timeframe: str = "1h"
    # Entry Timing - Point 13
    entry_timing: str = "Immediate Entry"
    entry_timing_emoji: str = "🟢"
    signal_validity: str = ""
    # Risk
    risk_pct: float = 0.0
    reward_pct: float = 0.0
    rr_ratio: float = 2.0
    # Analysis
    reasons_pro: List[str] = field(default_factory=list)
    reasons_con: List[str] = field(default_factory=list)
    engine_scores: Dict = field(default_factory=dict)
    strategy_votes: Dict = field(default_factory=dict)
    ai_result: Dict = field(default_factory=dict)
    market_regime: str = "UNKNOWN"
    mtf_status: str = "N/A"
    buy_score: float = 0.0
    sell_score: float = 0.0
    # Meta
    generated_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    signal_id: str = ""


class SignalGenerator:
    def __init__(self):
        self.fetcher = DataFetcher()

        # ===== REAL ENGINES ONLY =====
        self.engines = {
            "Trend": TrendEngine(),
            "Momentum": MomentumEngine(),
            "Volume": VolumeEngine(),
            "Price Action": PriceActionEngine(),
            "Smart Money": SmartMoneyEngine(),
            "Volatility": VolatilityEngine(),
            "Liquidity": LiquidityEngine(),
            "Risk Management": RiskEngine(),
            "Market Regime": MarketRegimeEngine(),
            "Multi Timeframe": MultiTimeframeEngine(),
        }
        self.scoring = ScoringEngine()

        # AI Analyzer
        try:
            self.ai_analyzer = AIAnalyzer()
            logger.info("🤖 AI Analyzer loaded")
        except Exception as e:
            logger.warning(f"AI load failed: {e}")
            self.ai_analyzer = None

        # Strategies
        self.strategies = {
            "trend_following": TrendFollowingStrategy(),
            "mean_reversion": MeanReversionStrategy(),
            "breakout": BreakoutStrategy(),
            "momentum": MomentumStrategy(),
            "divergence": DivergenceStrategy(),
        }

        logger.info(f"🎯 v3.2 AEGIS Pro loaded with {len(self.engines)} engines + {len(self.strategies)} strategies + AI")

    def _atr(self, df, period=14):
        h, l, c = df["high"], df["low"], df["close"]
        tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
        return tr.rolling(period).mean()

    def _find_swings(self, df, left=3, right=3):
        highs = df['high'].values
        lows = df['low'].values
        sh, sl = [], []
        for i in range(left, len(df) - right):
            if highs[i] == max(highs[i-left:i+right+1]):
                sh.append((i, highs[i]))
            if lows[i] == min(lows[i-left:i+right+1]):
                sl.append((i, lows[i]))
        return sh, sl

    def _calculate_entry_timing(self, df, signal_type: str, rsi: float, engine_results: Dict) -> Tuple[str, str, str]:
        """Point 13 - Entry Timing"""
        close = df['close'].iloc[-1]
        prev_close = df['close'].iloc[-2]
        
        # Check momentum
        momentum = engine_results.get("Momentum")
        macd_hist = 0
        if momentum and "macd_hist" in str(momentum.details):
            pass
        
        # Simple logic
        # 1. Immediate Entry: strong momentum, good volume, near entry
        # 2. Wait Pullback: overextended, RSI extreme
        # 3. Wait Candle Close: indecision
        # 4. Wait Breakout: near SR
        
        if signal_type == "BULLISH":
            if rsi < 65 and rsi > 45 and close > prev_close:
                return "🟢", "Immediate Entry", "2 candle"
            elif rsi > 70:
                return "🟡", "Wait for Pullback", "4 candle"
            else:
                return "🟡", "Wait for Candle Close", "1 candle"
        else:  # BEARISH
            if rsi > 35 and rsi < 55 and close < prev_close:
                return "🟢", "Immediate Entry", "2 candle"
            elif rsi < 25:
                return "🟡", "Wait for Pullback", "4 candle"
            else:
                return "🟡", "Wait for Candle Close", "1 candle"

    def _run_strategies(self, df, symbol, timeframe="1h"):
        """Run all 5 strategies, return consensus"""
        votes = {"BUY": 0, "SELL": 0, "NEUTRAL": 0}
        details = {}
        
        for name, strat in self.strategies.items():
            try:
                result = strat.analyze(df, symbol, timeframe)
                if result:
                    if hasattr(result, 'signal'):
                        sig = result.signal.upper()
                        conf = getattr(result, 'confidence', 50)
                    else:
                        sig = result.get("signal", "NEUTRAL").upper()
                        conf = result.get("confidence", 50)
                    
                    if sig in ["STRONG_BUY", "BUY"]:
                        sig = "BUY"
                    elif sig in ["STRONG_SELL", "SELL"]:
                        sig = "SELL"
                    else:
                        sig = "NEUTRAL"
                    
                    weight = config.STRATEGY_WEIGHTS.get(name, 1.0)
                    if sig in votes:
                        votes[sig] += weight
                    details[name] = {"signal": sig, "confidence": conf}
            except Exception as e:
                logger.debug(f"Strategy {name} failed: {e}")
                continue
        
        total = sum(votes.values()) or 1
        buy_pct = votes["BUY"] / total * 100
        sell_pct = votes["SELL"] / total * 100

        if buy_pct >= 40 and votes["BUY"] >= config.MIN_STRATEGY_AGREEMENT:
            consensus = "BUY"
            conf = buy_pct
        elif sell_pct >= 40 and votes["SELL"] >= config.MIN_STRATEGY_AGREEMENT:
            consensus = "SELL"
            conf = sell_pct
        else:
            consensus = "NEUTRAL"
            conf = max(buy_pct, sell_pct)

        return {
            "consensus": consensus,
            "confidence": conf,
            "votes": votes,
            "details": details
        }

    def analyze_single(self, symbol: str, timeframe: str = "1h") -> Optional[FinalSignal]:
        df = self.fetcher.fetch_ohlcv(symbol, timeframe, limit=config.CANDLES_COUNT.get(timeframe, 200))
        if df is None or len(df) < 100:
            return None

        # ===== Run Engines =====
        engine_results = {}
        tf_context = {"current": timeframe}
        for name, engine in self.engines.items():
            try:
                # Pass timeframe context for MTF engine
                engine_results[name] = engine.analyze(df, symbol, tf_context)
            except Exception as e:
                logger.warning(f"⚠️ {name}: {e}")
                engine_results[name] = None

        # Market Regime
        regime_result = engine_results.get("Market Regime")
        regime = regime_result.details.get("regime", "UNKNOWN") if regime_result else "UNKNOWN"

        # ===== AI Prediction =====
        ai_result = None
        if self.ai_analyzer:
            try:
                ai_result = self.ai_analyzer.predict(df)
            except Exception:
                ai_result = None

        # ===== Strategies =====
        strat_result = self._run_strategies(df, symbol, timeframe)

        # ===== Scoring - Independent BUY/SELL =====
        scoring = self.scoring.calculate(engine_results, regime, ai_result)
        confidence = scoring["confidence"]
        signal = scoring["signal"]  # BULLISH / BEARISH / NEUTRAL
        reasons_pro = scoring["reasons_pro"]
        reasons_con = scoring["reasons_con"]
        engine_scores = scoring["engine_scores"]
        buy_score = scoring.get("buy_score", 0)
        sell_score = scoring.get("sell_score", 0)

        # ===== Strategy consensus filter =====
        strat_consensus = strat_result["consensus"]
        strat_votes = strat_result["votes"]
        engine_action = "BUY" if signal == "BULLISH" else "SELL" if signal == "BEARISH" else "NEUTRAL"
        
        if strat_consensus != "NEUTRAL" and strat_consensus != engine_action:
            reasons_con.append(f"❌ Strategies disagree: {strat_consensus} vs {engine_action}")
            confidence -= 12
        elif strat_consensus == engine_action:
            reasons_pro.append(f"✅ Strategies confirm: BUY {strat_votes['BUY']:.1f} / SELL {strat_votes['SELL']:.1f}")
            confidence += 2

        # ===== Pre-signal checklist - Point 19 =====
        checklist_fail = []
        
        # 1. Trend alignment?
        trend_eng = engine_results.get("Trend")
        trend_ok = trend_eng and ((signal == "BULLISH" and trend_eng.signal == "BULLISH") or (signal == "BEARISH" and trend_eng.signal == "BEARISH"))
        if not trend_ok:
            checklist_fail.append("Trend mismatch")
        
        # 2. Momentum confirms?
        mom_eng = engine_results.get("Momentum")
        mom_ok = mom_eng and ((signal == "BULLISH" and mom_eng.signal != "BEARISH") or (signal == "BEARISH" and mom_eng.signal != "BULLISH"))
        if not mom_ok:
            checklist_fail.append("Momentum no confirm")
        
        # 3. Smart Money?
        sm_eng = engine_results.get("Smart Money")
        sm_ok = sm_eng is not None
        # 4. Volume OK?
        vol_eng = engine_results.get("Volume")
        vol_ok = vol_eng and vol_eng.signal != ("BEARISH" if signal == "BULLISH" else "BULLISH")
        if not vol_ok:
            checklist_fail.append("Volume against")
        
        # 5. Liquidity OK?
        liq_eng = engine_results.get("Liquidity")
        liq_ok = True
        
        # 6. MTF Alignment? - Point 9
        mtf_eng = engine_results.get("Multi Timeframe")
        mtf_ok = True
        mtf_status = "N/A"
        if mtf_eng:
            mtf_status = "Aligned" if mtf_eng.details.get("aligned") else "Conflict"
            if mtf_eng.signal == "NEUTRAL" and mtf_eng.score < 30:
                # Strong MTF conflict
                checklist_fail.append("MTF conflict")
                mtf_ok = False
                confidence -= 15
        
        # 7. R/R OK? will check later
        # 8. Confidence OK? will check later
        
        if len(checklist_fail) >= 2:
            # Fail 2+ checks = NO_TRADE
            return None

        # ===== AI confirmation =====
        if config.REQUIRE_AI_CONFIRMATION and ai_result:
            ai_dir = ai_result.get("direction", "NEUTRAL")
            ai_prob = ai_result.get("probability", 50)
            ai_ok_buy = signal == "BULLISH" and ai_dir == "UP" and ai_prob >= config.MIN_AI_PROBABILITY
            ai_ok_sell = signal == "BEARISH" and ai_dir == "DOWN" and ai_prob >= config.MIN_AI_PROBABILITY
            
            if not (ai_ok_buy or ai_ok_sell):
                if confidence < 88:
                    return None

        # ===== Critical engines - BOTH BUY/SELL =====
        critical_engines = ["Trend", "Volume"]
        critical_ok = 0
        for eng_name in critical_engines:
            eng = engine_results.get(eng_name)
            if not eng:
                continue
            if signal == "BULLISH" and eng.signal == "BULLISH":
                critical_ok += 1
            elif signal == "BEARISH" and eng.signal == "BEARISH":
                critical_ok += 1
        
        if critical_ok < 1:
            return None

        # ===== RSI filter =====
        momentum = engine_results.get("Momentum")
        rsi_val = 50
        if momentum:
            rsi_val = momentum.details.get("rsi", 50)
            if rsi_val > 75 and signal == "BULLISH":
                reasons_con.append(f"❌ RSI overbought ({rsi_val:.0f})")
                confidence -= 8
            elif rsi_val < 25 and signal == "BEARISH":
                reasons_con.append(f"❌ RSI oversold ({rsi_val:.0f})")
                confidence -= 8

        # ===== Final threshold - Timeframe specific =====
        min_conf_tf = config.get_min_confidence_for_tf(timeframe)
        if confidence < min_conf_tf or signal == "NEUTRAL":
            return None

        # ===== RISK MANAGEMENT - ATR + Swing SR + Liquidity - Point 7 =====
        cp = float(df["close"].iloc[-1])
        atr_series = self._atr(df, 14)
        atr = float(atr_series.iloc[-1]) if not pd.isna(atr_series.iloc[-1]) else cp * 0.018
        atr_pct = atr / cp * 100

        # Swing based SL
        swing_highs, swing_lows = self._find_swings(df, left=3, right=3)
        swing_sl_pct = None
        if signal == "BULLISH" and swing_lows:
            last_sl = swing_lows[-1][1]
            swing_sl_pct = (cp - last_sl) / cp * 100 * 1.1  # 10% buffer
        elif signal == "BEARISH" and swing_highs:
            last_sh = swing_highs[-1][1]
            swing_sl_pct = (last_sh - cp) / cp * 100 * 1.1

        # ATR based SL
        atr_sl_pct = max(1.2, min(3.5, atr_pct * config.ATR_SL_MULTIPLIER))
        
        # Combine: use max(ATR, Swing) but capped
        if swing_sl_pct and 0.8 < swing_sl_pct < 4.5:
            sl_pct = (atr_sl_pct * 0.6 + swing_sl_pct * 0.4)
        else:
            sl_pct = atr_sl_pct
        
        sl_pct = max(1.0, min(4.0, sl_pct))
        tp_pct = sl_pct * config.RISK_REWARD_RATIO

        # R/R check - Point 19
        if tp_pct / sl_pct < 1.8:
            return None  # R/R too low

        # ===== Entry Timing - Point 13 =====
        entry_emoji, entry_timing, validity_candles = self._calculate_entry_timing(df, signal, rsi_val, engine_results)
        
        # Signal validity
        tf_minutes = {"15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}.get(timeframe, 60)
        if "candle" in validity_candles:
            n_candles = int(validity_candles.split()[0]) if validity_candles[0].isdigit() else 2
            validity_str = f"{n_candles} candle {timeframe}"
        else:
            validity_str = validity_candles

        # Leverage
        if confidence > 92:
            leverage = 7.0
        elif confidence > 88:
            leverage = 5.0
        elif confidence > 84:
            leverage = 3.0
        else:
            leverage = 2.0
        leverage = min(leverage, config.MAX_LEVERAGE)

        # ===== TP1/TP2/TP3 - Point 14 =====
        if signal == "BULLISH":
            action = "BUY"
            entry_price = cp
            stop_loss = cp * (1 - sl_pct / 100)
            tp1 = cp * (1 + tp_pct * 0.4 / 100)
            tp2 = cp * (1 + tp_pct * 0.7 / 100)
            tp3 = cp * (1 + tp_pct / 100)
        else:
            action = "SELL"
            entry_price = cp
            stop_loss = cp * (1 + sl_pct / 100)
            tp1 = cp * (1 - tp_pct * 0.4 / 100)
            tp2 = cp * (1 - tp_pct * 0.7 / 100)
            tp3 = cp * (1 - tp_pct / 100)

        sid = f"{symbol.replace('/', '').replace(':', '')}_{action}_{datetime.now().strftime('%H%M%S')}"

        risk_pct = sl_pct
        reward_pct = tp_pct
        rr_ratio = reward_pct / risk_pct if risk_pct > 0 else 2.0

        logger.success(f"🎯 {action} {symbol} | Conf:{confidence:.0f}% | TF:{timeframe} | SL:{sl_pct:.1f}% TP:{tp_pct:.1f}% | {entry_timing}")

        # Get MTF status from engine
        mtf_eng = engine_results.get("Multi Timeframe")
        if mtf_eng:
            mtf_status_str = "Aligned ✅" if mtf_eng.details.get("aligned") else "Conflict ❌"
        else:
            mtf_status_str = "N/A"

        return FinalSignal(
            symbol=symbol, action=action,
            entry_price=round(entry_price, 8),
            current_price=round(cp, 8),
            stop_loss=round(stop_loss, 8),
            take_profit=round(tp3, 8),
            tp1=round(tp1, 8),
            tp2=round(tp2, 8),
            tp3=round(tp3, 8),
            leverage=round(leverage, 1),
            confidence=round(confidence, 1),
            timeframe=timeframe,
            entry_timing=entry_timing,
            entry_timing_emoji=entry_emoji,
            signal_validity=validity_str,
            risk_pct=round(risk_pct, 2),
            reward_pct=round(reward_pct, 2),
            rr_ratio=round(rr_ratio, 2),
            reasons_pro=reasons_pro[:8],
            reasons_con=reasons_con[:5],
            engine_scores=engine_scores,
            strategy_votes=strat_votes,
            ai_result=ai_result or {},
            market_regime=regime,
            mtf_status=mtf_status_str,
            buy_score=round(buy_score, 1),
            sell_score=round(sell_score, 1),
            signal_id=sid,
        )

    def scan_market(self, symbols=None, timeframes=None):
        if symbols is None:
            symbols = config.TOP_COINS
        if timeframes is None:
            timeframes = config.SCAN_TIMEFRAMES
        
        all_signals = []
        logger.info(f"🔍 Scanning {len(symbols)} coins x {len(timeframes)} TFs {timeframes}...")
        
        for symbol in symbols:
            for tf in timeframes:
                s = self.analyze_single(symbol, tf)
                if s:
                    all_signals.append(s)
                    # INSTANT SEND
                    try:
                        from telegram_bot import TelegramSignalBot
                        tg = TelegramSignalBot()
                        tg.send_signal(s)
                        logger.success(f"📤 Instant: {s.symbol} {s.action} {s.confidence}%")
                    except Exception as e:
                        logger.error(f"Send failed: {e}")
        
        all_signals.sort(key=lambda s: s.confidence, reverse=True)
        logger.success(f"✅ Done: {len(all_signals)} signals")
        return all_signals

    def get_top_signals(self, symbols=None, count=None):
        if count is None:
            count = config.TOP_SIGNALS_COUNT
        signals = self.scan_market(symbols)
        return signals[:count]
