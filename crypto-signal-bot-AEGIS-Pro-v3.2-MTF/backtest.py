"""
📊 Backtest Engine v3.2 Pro
Fee, Slippage, TP1/TP2/TP3, Partial Close, BE, Trailing
Profit Factor, Max DD, Expectancy, Sharpe
"""
import pandas as pd
import numpy as np
import time
from datetime import datetime
from loguru import logger
from signal_generator import SignalGenerator
from data.fetcher import DataFetcher

class Backtester:
    def __init__(self, fee_pct=0.06, slippage_pct=0.05):
        self.generator = SignalGenerator()
        self.fetcher = DataFetcher()
        self.fee_pct = fee_pct
        self.slippage_pct = slippage_pct

    def backtest_symbol(self, symbol: str, timeframe: str = "1h", lookback_days: int = 90):
        df_full = self.fetcher.fetch_ohlcv(symbol, timeframe, limit=500, use_cache=False)
        if df_full is None or len(df_full) < 150:
            return None
        
        results = []
        equity_curve = [10000]
        peak = 10000
        max_dd = 0
        
        # Walk forward
        for i in range(120, len(df_full) - 30, 5):
            df_slice = df_full.iloc[:i].copy()
            original_fetch = self.generator.fetcher.fetch_ohlcv
            self.generator.fetcher.fetch_ohlcv = lambda s, tf, limit=None, use_cache=True: df_slice
            
            try:
                signal = self.generator.analyze_single(symbol, timeframe)
            except Exception:
                signal = None
            finally:
                self.generator.fetcher.fetch_ohlcv = original_fetch
            
            if not signal:
                continue
            
            entry = signal.entry_price
            # Apply slippage
            if signal.action == "BUY":
                entry *= (1 + self.slippage_pct/100)
            else:
                entry *= (1 - self.slippage_pct/100)
            
            sl = signal.stop_loss
            tp1 = signal.tp1 if signal.tp1 > 0 else signal.take_profit
            tp2 = signal.tp2 if signal.tp2 > 0 else signal.take_profit
            tp3 = signal.tp3 if signal.tp3 > 0 else signal.take_profit
            action = signal.action
            
            # Simulate with TP1/TP2/TP3, BE, Trailing
            future = df_full.iloc[i:i+30]
            hit = None
            exit_price = entry
            pnl_pct = 0
            
            position_size = 1.0
            be_moved = False
            trailing_active = False
            trailing_stop = sl
            
            for _, row in future.iterrows():
                high, low, close = row['high'], row['low'], row['close']
                
                if action == "BUY":
                    # SL hit?
                    check_price = low
                    if not be_moved and check_price <= sl:
                        hit = "SL"
                        exit_price = sl
                        pnl_pct = -abs((entry - sl) / entry * 100)
                        break
                    if be_moved and check_price <= trailing_stop:
                        hit = "BE/TSL"
                        exit_price = trailing_stop
                        pnl_pct = (trailing_stop - entry) / entry * 100
                        break
                    # TP1
                    if check_price >= tp1 or high >= tp1:
                        # Partial close 30%, move SL to BE
                        if not be_moved:
                            be_moved = True
                            trailing_stop = entry
                        # TP2
                        if high >= tp2:
                            trailing_active = True
                            # TP3
                            if high >= tp3:
                                hit = "TP3"
                                exit_price = tp3
                                # Weighted PnL: 30% TP1, 30% TP2, 40% TP3
                                p1 = (tp1 - entry) / entry * 100 * 0.3
                                p2 = (tp2 - entry) / entry * 100 * 0.3
                                p3 = (tp3 - entry) / entry * 100 * 0.4
                                pnl_pct = p1 + p2 + p3
                                break
                            else:
                                # Hit TP2 only
                                hit = "TP2"
                                exit_price = tp2
                                p1 = (tp1 - entry) / entry * 100 * 0.3
                                p2 = (tp2 - entry) / entry * 100 * 0.7
                                pnl_pct = p1 + p2
                                # continue for TP3 with trailing?
                        else:
                            # Only TP1 hit so far, continue
                            pass
                    # Trailing stop update
                    if trailing_active:
                        new_trail = close * 0.995
                        if new_trail > trailing_stop:
                            trailing_stop = new_trail
                else:  # SELL
                    check_price = high
                    if not be_moved and check_price >= sl:
                        hit = "SL"
                        exit_price = sl
                        pnl_pct = -abs((sl - entry) / entry * 100)
                        break
                    if be_moved and check_price >= trailing_stop:
                        hit = "BE/TSL"
                        exit_price = trailing_stop
                        pnl_pct = (entry - trailing_stop) / entry * 100
                        break
                    if check_price <= tp1 or low <= tp1:
                        if not be_moved:
                            be_moved = True
                            trailing_stop = entry
                        if low <= tp2:
                            trailing_active = True
                            if low <= tp3:
                                hit = "TP3"
                                exit_price = tp3
                                p1 = (entry - tp1) / entry * 100 * 0.3
                                p2 = (entry - tp2) / entry * 100 * 0.3
                                p3 = (entry - tp3) / entry * 100 * 0.4
                                pnl_pct = p1 + p2 + p3
                                break
                            else:
                                hit = "TP2"
                                exit_price = tp2
                                p1 = (entry - tp1) / entry * 100 * 0.3
                                p2 = (entry - tp2) / entry * 100 * 0.7
                                pnl_pct = p1 + p2
                    if trailing_active:
                        new_trail = close * 1.005
                        if new_trail < trailing_stop:
                            trailing_stop = new_trail
            
            if hit is None:
                # Timeout - close at last price
                last_price = future['close'].iloc[-1] if len(future) > 0 else entry
                exit_price = last_price
                if action == "BUY":
                    pnl_pct = (last_price - entry) / entry * 100
                else:
                    pnl_pct = (entry - last_price) / entry * 100
                hit = "TIMEOUT"
            
            # Apply fees (entry + exit)
            pnl_pct -= self.fee_pct * 2
            
            win = pnl_pct > 0
            results.append({
                "symbol": symbol,
                "action": action,
                "confidence": signal.confidence,
                "entry": entry,
                "exit": exit_price,
                "result": hit,
                "pnl_pct": round(pnl_pct, 2),
                "win": win
            })
            
            # Equity curve for DD / Sharpe
            last_equity = equity_curve[-1]
            new_equity = last_equity * (1 + pnl_pct/100)
            equity_curve.append(new_equity)
            if new_equity > peak:
                peak = new_equity
            dd = (peak - new_equity) / peak * 100
            if dd > max_dd:
                max_dd = dd
        
        if not results:
            return {"symbol": symbol, "trades": 0}
        
        wins = [r for r in results if r["win"]]
        losses = [r for r in results if not r["win"]]
        total = len(results)
        win_rate = len(wins) / total * 100
        
        gross_profit = sum(r["pnl_pct"] for r in wins)
        gross_loss = abs(sum(r["pnl_pct"] for r in losses)) or 0.001
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 99
        
        avg_win = np.mean([r["pnl_pct"] for r in wins]) if wins else 0
        avg_loss = np.mean([r["pnl_pct"] for r in losses]) if losses else 0
        expectancy = (win_rate/100 * avg_win) + ((1-win_rate/100) * avg_loss)
        
        # Sharpe (simplified)
        returns = [r["pnl_pct"] for r in results]
        sharpe = (np.mean(returns) / (np.std(returns) + 1e-9)) * np.sqrt(252) if len(returns) > 1 else 0
        
        total_pnl = sum(returns)
        
        return {
            "symbol": symbol,
            "trades": total,
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(win_rate, 1),
            "profit_factor": round(profit_factor, 2),
            "expectancy": round(expectancy, 2),
            "sharpe": round(sharpe, 2),
            "max_dd": round(max_dd, 2),
            "total_pnl_pct": round(total_pnl, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "details": results
        }

    def run_bulk(self, symbols=None, timeframe="1h"):
        from config import config
        if symbols is None:
            symbols = config.TOP_COINS[:10]
        
        all_results = []
        for sym in symbols:
            logger.info(f"Backtesting {sym} {timeframe}...")
            res = self.backtest_symbol(sym, timeframe)
            if res and res.get("trades", 0) > 0:
                logger.info(f"  {sym}: {res['wins']}/{res['trades']} = {res['win_rate']}% | PF={res['profit_factor']} | DD={res['max_dd']}%")
                all_results.append(res)
            time.sleep(0.3)
        
        if all_results:
            total_trades = sum(r["trades"] for r in all_results)
            total_wins = sum(r["wins"] for r in all_results)
            overall_wr = total_wins / total_trades * 100 if total_trades else 0
            avg_pf = np.mean([r["profit_factor"] for r in all_results])
            avg_dd = np.mean([r["max_dd"] for r in all_results])
            total_pnl = sum(r["total_pnl_pct"] for r in all_results)
            
            print("\n" + "="*60)
            print(f"BACKTEST PRO SUMMARY - {timeframe} | Fee {self.fee_pct}% + Slip {self.slippage_pct}%")
            print("="*60)
            for r in all_results:
                print(f"{r['symbol']:12} | {r['wins']:2}/{r['trades']:2} | WR {r['win_rate']:5.1f}% | PF {r['profit_factor']:.2f} | DD {r['max_dd']:.1f}% | PnL {r['total_pnl_pct']:+.1f}%")
            print("-"*60)
            print(f"TOTAL: {total_wins}/{total_trades} = {overall_wr:.1f}% | Avg PF {avg_pf:.2f} | Avg DD {avg_dd:.1f}% | Total PnL {total_pnl:+.1f}%")
            print("="*60)
            
            return {
                "overall_win_rate": round(overall_wr, 1),
                "total_trades": total_trades,
                "profit_factor": round(avg_pf, 2),
                "max_dd": round(avg_dd, 2),
                "total_pnl_pct": round(total_pnl, 2),
                "per_symbol": all_results
            }
        else:
            print("No trades found")
            return None


if __name__ == "__main__":
    bt = Backtester(fee_pct=0.06, slippage_pct=0.05)
    print("Running backtest 1h...")
    bt.run_bulk(timeframe="1h")
    print("\nRunning backtest 4h...")
    bt.run_bulk(timeframe="4h")
