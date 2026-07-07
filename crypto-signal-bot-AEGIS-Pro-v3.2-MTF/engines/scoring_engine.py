"""
📊 Scoring Engine v3.2 - AEGIS Pro
- وزن‌های داینامیک بر اساس Market Regime
- امتیازدهی مستقل BUY/SELL
- Conflict detection
- Confidence واقعی
"""

from typing import Dict, List
from .base_engine import BaseEngine, EngineResult


class ScoringEngine(BaseEngine):
    def __init__(self):
        super().__init__("Scoring", weight=1.0)

    def analyze(self, df, symbol, timeframes=None):
        return EngineResult(self.name, 50, "NEUTRAL", {}, ["Use calculate()"])

    def _get_dynamic_weights(self, market_regime: str) -> Dict[str, float]:
        """وزن موتورها بر اساس وضعیت بازار - Point 2"""
        base = {
            "Trend": 2.5,
            "Momentum": 1.8,
            "Volume": 2.0,
            "Price Action": 1.5,
            "Smart Money": 2.0,
            "Volatility": 1.0,
            "Liquidity": 1.2,
            "Risk Management": 0.8,
        }
        
        # Dynamic adjustment per regime
        if market_regime == "TREND":
            base["Trend"] *= 1.3
            base["Momentum"] *= 1.2
            base["Smart Money"] *= 1.1
        elif market_regime == "WEAK_TREND":
            base["Trend"] *= 1.1
            base["Volume"] *= 1.2
        elif market_regime == "RANGE":
            base["Price Action"] *= 1.4
            base["Smart Money"] *= 1.2
            base["Momentum"] *= 0.8
            base["Trend"] *= 0.7
        elif market_regime == "VOLATILE":
            base["Volatility"] *= 1.5
            base["Risk Management"] *= 1.3
            base["Liquidity"] *= 1.2
            base["Trend"] *= 0.8
        elif market_regime == "ACCUMULATION":
            base["Volume"] *= 1.4
            base["Smart Money"] *= 1.3
            base["Liquidity"] *= 1.2
        elif market_regime == "DISTRIBUTION":
            base["Volume"] *= 1.4
            base["Smart Money"] *= 1.3
            base["Risk Management"] *= 1.2
        
        return base

    def calculate(self, engine_results: Dict[str, EngineResult], market_regime: str, ai_result: Dict = None) -> Dict:
        if not engine_results:
            return {"total_score": 0, "confidence": 0, "signal": "NEUTRAL",
                    "reasons_pro": [], "reasons_con": [], "engine_scores": {},
                    "buy_score": 0, "sell_score": 0}

        weights = self._get_dynamic_weights(market_regime)

        total_w = 0
        weighted_s = 0
        engine_scores = {}
        all_pro, all_con = [], []
        
        # Independent BUY/SELL scoring - Point 18
        bull_score_sum = 0
        bear_score_sum = 0
        bull_w = bear_w = neutral_w = 0

        # Conflict detection - Point 1, 16
        trend_sig = None
        momentum_sig = None

        for name, result in engine_results.items():
            if result is None:
                continue
            w = weights.get(name, 0.5)
            total_w += w
            sc = max(0, min(100, result.score))
            weighted_s += sc * w
            engine_scores[name] = {"score": round(sc, 1), "signal": result.signal, "weight": round(w, 2)}

            # Track Trend/Momentum conflict
            if name == "Trend":
                trend_sig = result.signal
            if name == "Momentum":
                momentum_sig = result.signal

            # Independent scoring
            if result.signal == "BULLISH":
                bull_w += w
                bull_score_sum += sc * w
            elif result.signal == "BEARISH":
                bear_w += w
                bear_score_sum += sc * w
            else:
                neutral_w += w

            for r in result.reasons:
                if r.startswith(("✅", "📈", "🟢")):
                    all_pro.append(r)
                elif r.startswith(("❌", "📉", "🔴", "⚠️")):
                    all_con.append(r)

        if total_w == 0:
            return {"total_score": 0, "confidence": 0, "signal": "NEUTRAL",
                    "reasons_pro": [], "reasons_con": [], "engine_scores": {},
                    "buy_score": 0, "sell_score": 0}

        total_score = weighted_s / total_w

        # Independent BUY/SELL scores
        buy_score = (bull_score_sum / bull_w) if bull_w > 0 else 0
        sell_score = (bear_score_sum / bear_w) if bear_w > 0 else 0

        total_votes = bull_w + bear_w
        if total_votes > 0:
            bull_pct = bull_w / total_votes * 100
            bear_pct = bear_w / total_votes * 100
        else:
            bull_pct = bear_pct = 0

        # Signal decision with NO_TRADE support - Point 1, 18
        # Need strong consensus, otherwise NO_TRADE
        conflict_penalty = 0
        conflict_reasons = []
        
        # Trend vs Momentum conflict - Point 1
        if trend_sig and momentum_sig and trend_sig != "NEUTRAL" and momentum_sig != "NEUTRAL":
            if trend_sig != momentum_sig:
                conflict_penalty += 15
                conflict_reasons.append(f"⚠️ Trend({trend_sig}) vs Momentum({momentum_sig}) conflict")
        
        # Engine disagreement check - Point 16
        agreement_ratio_raw = max(bull_pct, bear_pct) if total_votes > 0 else 0
        if agreement_ratio_raw < 60:
            # Too much disagreement
            signal = "NEUTRAL"
            conflict_penalty += 10
            conflict_reasons.append(f"❌ Engine disagreement: Bull {bull_pct:.0f}% / Bear {bear_pct:.0f}%")
        elif bull_pct >= 62 and buy_score >= 55:
            signal = "BULLISH"
        elif bear_pct >= 62 and sell_score >= 55:
            signal = "BEARISH"
        else:
            signal = "NEUTRAL"

        # ===== CONFIDENCE - weighted average, no fake =====
        direction_strength = max(bull_pct, bear_pct)
        agreeing_w = bull_w if signal == "BULLISH" else bear_w if signal == "BEARISH" else 0
        agreement_ratio = (agreeing_w / total_w * 100) if total_w > 0 else 0
        
        # Base confidence
        engine_conf = buy_score if signal == "BULLISH" else sell_score if signal == "BEARISH" else total_score
        
        confidence = (
            engine_conf * 0.40 +
            direction_strength * 0.35 +
            agreement_ratio * 0.25
        )
        
        # Conflict penalty
        confidence -= conflict_penalty
        all_con.extend(conflict_reasons)

        # Regime adjustment
        regime_mod = {
            "TREND": 4,
            "WEAK_TREND": 0,
            "RANGE": -6,
            "VOLATILE": -8,
            "ACCUMULATION": 2,
            "DISTRIBUTION": -5,
        }
        confidence += regime_mod.get(market_regime, 0)

        # AI confirmation
        ai_match = False
        if ai_result:
            ai_dir = ai_result.get("direction", "NEUTRAL")
            ai_prob = ai_result.get("probability", 50)
            ai_match = (
                (signal == "BULLISH" and ai_dir == "UP") or
                (signal == "BEARISH" and ai_dir == "DOWN")
            )
            if ai_match and ai_prob >= 60:
                confidence += 4
                all_pro.append(f"🤖 AI confirms {ai_dir} {ai_prob:.0f}%")
            elif not ai_match and ai_prob >= 60:
                confidence -= 12
                all_con.append(f"🤖 AI disagrees: {ai_dir} {ai_prob:.0f}%")

        if signal == "NEUTRAL":
            confidence *= 0.5

        confidence = max(5, min(95, confidence))

        # NO_TRADE if confidence too low or high conflict
        final_signal = signal
        if confidence < 55 or agreement_ratio < 55:
            final_signal = "NEUTRAL"

        return {
            "total_score": round(total_score, 1),
            "confidence": round(confidence, 1),
            "signal": final_signal,
            "raw_signal": signal,
            "reasons_pro": list(dict.fromkeys(all_pro))[:10],
            "reasons_con": list(dict.fromkeys(all_con))[:8],
            "engine_scores": engine_scores,
            "bull_pct": round(bull_pct, 1),
            "bear_pct": round(bear_pct, 1),
            "agreement_ratio": round(agreement_ratio, 1),
            "buy_score": round(buy_score, 1),
            "sell_score": round(sell_score, 1),
            "conflict_penalty": conflict_penalty,
            "weights_used": weights,
        }
