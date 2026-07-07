"""
🤖 Telegram Bot - AEGIS Pro v3.2
📢 کانال: پیام کامل با TP1/TP2/TP3 + Entry Timing
💬 ربات: تحلیل کامل
"""
from typing import List
from datetime import datetime
import requests
from loguru import logger
from signal_generator import FinalSignal
from config import config


class TelegramSignalBot:
    def __init__(self, token: str = None, channel_id: str = None, user_chat_id: str = None):
        self.token = token or config.TELEGRAM_BOT_TOKEN
        self.channel_id = channel_id or config.TELEGRAM_CHANNEL_ID
        self.user_chat_id = user_chat_id or config.USER_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"

        if self.token and self.channel_id:
            logger.info(f"✅ Telegram ready 📢 Channel: {self.channel_id} | 💬 Bot: {'✅' if self.user_chat_id else '❌'}")
        else:
            logger.warning("⚠️ Telegram: Set TELEGRAM_BOT_TOKEN in .env")

    def _send(self, text, chat_id: str) -> bool:
        if not self.token or not chat_id:
            return False
        try:
            resp = requests.post(f"{self.base_url}/sendMessage", json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }, timeout=10)
            if resp.status_code == 200:
                return True
            logger.error(f"❌ Telegram {resp.status_code}: {resp.text[:80]}")
            return False
        except Exception as e:
            logger.error(f"❌ Telegram: {e}")
            return False

    def _fmt(self, p: float) -> str:
        if p >= 1000: return f"{p:,.2f}"
        elif p >= 1: return f"{p:.4f}"
        elif p >= 0.01: return f"{p:.6f}"
        return f"{p:.8f}"

    # ============================================================
    # 📢 CHANNEL - کامل با TP1/TP2/TP3 + Entry Timing - Point 14
    # ============================================================
    def format_short(self, s: FinalSignal) -> str:
        em = "🟢" if s.action == "BUY" else "🔴"
        act = "LONG" if s.action == "BUY" else "SHORT"
        
        # Use tp1/tp2/tp3 from signal if available, else calculate
        tp1 = s.tp1 if s.tp1 > 0 else s.take_profit
        tp2 = s.tp2 if s.tp2 > 0 else s.take_profit
        tp3 = s.tp3 if s.tp3 > 0 else s.take_profit
        
        # Percentages
        if s.action == "BUY":
            rp = (s.entry_price - s.stop_loss) / s.entry_price * 100 if s.entry_price else 0
            tp1_p = (tp1 - s.entry_price) / s.entry_price * 100 if s.entry_price else 0
            tp2_p = (tp2 - s.entry_price) / s.entry_price * 100 if s.entry_price else 0
            tp3_p = (tp3 - s.entry_price) / s.entry_price * 100 if s.entry_price else 0
        else:
            rp = (s.stop_loss - s.entry_price) / s.entry_price * 100 if s.entry_price else 0
            tp1_p = (s.entry_price - tp1) / s.entry_price * 100 if s.entry_price else 0
            tp2_p = (s.entry_price - tp2) / s.entry_price * 100 if s.entry_price else 0
            tp3_p = (s.entry_price - tp3) / s.entry_price * 100 if s.entry_price else 0

        risk_pct = s.risk_pct if s.risk_pct > 0 else abs(rp)
        rr = s.rr_ratio if s.rr_ratio > 0 else (tp3_p / abs(rp) if rp else 2.0)
        bar = "▓" * int(min(s.confidence / 10, 10)) + "░" * (10 - int(min(s.confidence / 10, 10)))
        
        # Entry timing
        entry_emoji = getattr(s, 'entry_timing_emoji', em)
        entry_timing = getattr(s, 'entry_timing', 'Immediate Entry')
        validity = getattr(s, 'signal_validity', '')
        
        timing_line = f"\n⏳ {entry_emoji} <b>{entry_timing}</b>"
        if validity:
            timing_line += f"\n⌛ اعتبار: {validity}"
        
        return f"""
{em} <b>{act} {s.symbol}</b> | {bar} {s.confidence:.0f}%
<code>━━━━━━━━━━━━━━━━━━━━</code>
💵 ورود: <b>{self._fmt(s.entry_price)}</b>
🎯 TP1: <b>{self._fmt(tp1)}</b> (+{tp1_p:.1f}%)
🎯 TP2: <b>{self._fmt(tp2)}</b> (+{tp2_p:.1f}%)
🏆 TP3: <b>{self._fmt(tp3)}</b> (+{tp3_p:.1f}%)
🛑 SL: <b>{self._fmt(s.stop_loss)}</b> (-{risk_pct:.1f}%)
<code>━━━━━━━━━━━━━━━━━━━━</code>{timing_line}
📊 R/R 1:{rr:.1f} | ⚡ {s.leverage}x | ⏱ {s.timeframe}
{em} #{s.symbol.replace('/', '').replace('USDT','')}
"""

    # ============================================================
    # 📄 DETAILED - کامل
    # ============================================================
    def format_detailed(self, s: FinalSignal) -> str:
        em = "🟢" if s.action == "BUY" else "🔴"
        act = "BUY 🟢 LONG" if s.action == "BUY" else "SELL 🔴 SHORT"

        # TPs
        tp1 = s.tp1 if s.tp1 > 0 else s.take_profit
        tp2 = s.tp2 if s.tp2 > 0 else s.take_profit
        tp3 = s.tp3 if s.tp3 > 0 else s.take_profit

        if s.action == "BUY":
            rp = (s.entry_price - s.stop_loss) / s.entry_price * 100 if s.entry_price else 0
            tp1_p = (tp1 - s.entry_price) / s.entry_price * 100 if s.entry_price else 0
            tp2_p = (tp2 - s.entry_price) / s.entry_price * 100 if s.entry_price else 0
            tp3_p = (tp3 - s.entry_price) / s.entry_price * 100 if s.entry_price else 0
        else:
            rp = (s.stop_loss - s.entry_price) / s.entry_price * 100 if s.entry_price else 0
            tp1_p = (s.entry_price - tp1) / s.entry_price * 100 if s.entry_price else 0
            tp2_p = (s.entry_price - tp2) / s.entry_price * 100 if s.entry_price else 0
            tp3_p = (s.entry_price - tp3) / s.entry_price * 100 if s.entry_price else 0

        risk_pct = s.risk_pct if s.risk_pct > 0 else abs(rp)
        rr = s.rr_ratio if s.rr_ratio > 0 else 2.0
        bar = "▓" * int(min(s.confidence / 10, 10)) + "░" * (10 - int(min(s.confidence / 10, 10)))

        # Engine Scores
        engine_lines = ""
        if s.engine_scores:
            sorted_engines = sorted(s.engine_scores.items(), key=lambda x: x[1].get("score", 0), reverse=True)[:8]
            for name, data in sorted_engines:
                sc = data.get("score", 0)
                sg = data.get("signal", "?")
                icon = "🟢" if sg == "BULLISH" else ("🔴" if sg == "BEARISH" else "⚪")
                engine_lines += f"   {icon} {name}: {sc:.0f}%\n"

        pro_lines = "\n".join([f"   {r}" for r in s.reasons_pro[:6]]) or "   ✔ All filters passed"
        con_lines = "\n".join([f"   {r}" for r in s.reasons_con[:4]]) or "   ✖ None"

        entry_emoji = getattr(s, 'entry_timing_emoji', '🟢')
        entry_timing = getattr(s, 'entry_timing', 'Immediate Entry')
        validity = getattr(s, 'signal_validity', '')
        market_regime = getattr(s, 'market_regime', 'UNKNOWN')

        ai_txt = ""
        if s.ai_result:
            ai_dir = s.ai_result.get('direction', '?')
            ai_prob = s.ai_result.get('probability', 0)
            ai_txt = f"\n🤖 AI: {ai_dir} {ai_prob:.0f}%"

        return f"""
{em}━━━━━━━━━━━━━━━━━━{em}
   🎯 <b>AEGIS Pro {act}</b>
{em}━━━━━━━━━━━━━━━━━━{em}

📌 <b>{s.symbol}</b> | ⏱ {s.timeframe}
📊 Confidence: {bar} <b>{s.confidence:.0f}%</b>
📈 Regime: {market_regime}{ai_txt}
━━━━━━━━━━━━━━━━━━

⏳ <b>Entry:</b> {entry_emoji} {entry_timing}
⌛ <b>Validity:</b> {validity or '2 candle'}
━━━━━━━━━━━━━━━━━━

💵 <b>Entry:</b> <code>{self._fmt(s.entry_price)}</code>

🎯 <b>TP1</b> <code>{self._fmt(tp1)}</code> (+{tp1_p:.1f}%)
🎯 <b>TP2</b> <code>{self._fmt(tp2)}</code> (+{tp2_p:.1f}%)
🏆 <b>TP3</b> <code>{self._fmt(tp3)}</code> (+{tp3_p:.1f}%)

🛑 <b>SL</b> <code>{self._fmt(s.stop_loss)}</code> (-{risk_pct:.1f}%)
━━━━━━━━━━━━━━━━━━

📊 R/R: 1:{rr:.1f} | Lev: {s.leverage}x

<b>📋 TP Management:</b>
TP1 → Close 30% + SL to BE
TP2 → Close 30% + Trailing
TP3 → Close remaining
━━━━━━━━━━━━━━━━━━

<b>✅ موافق:</b>
{pro_lines}
━━━━━━━━━━━━━━━━━━

<b>❌ مخالف:</b>
{con_lines}
━━━━━━━━━━━━━━━━━━

<b>📊 موتورها:</b>
{engine_lines}━━━━━━━━━━━━━━━━━━
🆔 {s.signal_id}
📅 {s.generated_at}
⚠️ فقط آموزشی - مدیریت ریسک کنید
"""

    def send_signal(self, signal: FinalSignal) -> bool:
        ok = False
        if self.channel_id:
            ok |= self._send(self.format_short(signal), self.channel_id)
        if self.user_chat_id:
            ok |= self._send(self.format_detailed(signal), self.user_chat_id)
        return ok

    def send_batch(self, signals: List[FinalSignal]) -> int:
        sent = 0
        for s in signals:
            if self.send_signal(s): sent += 1
        return sent
