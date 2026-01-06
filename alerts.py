import pandas as pd
import datetime
import logging
from data_fetcher import get_stock_price

from idx_tickers import IDX_WATCHLIST

logger = logging.getLogger(__name__)

class StockMonitor:
    def __init__(self, watchlist=None):
        if watchlist is None:
            # Use the extensive list by default
            self.watchlist = IDX_WATCHLIST
        else:
            self.watchlist = watchlist

    async def scan_market(self, context=None):
        """
        Scans the watchlist for significant moves:
        - Price increase > 3% (Sensitive)
        - RSI < 70 (Ensure not already overbought if volume is high)
        """
        alerts = []
        logger.info("Scanning market for alerts...")
        
        for ticker in self.watchlist:
            try:
                # Fetch fresh data
                data = get_stock_price(ticker)
                if not data:
                    continue
                
                change_pct = data['change_pct']
                price = data['price']
                volume = data['volume']
                
                # Check 1: Significant Gain (>3%)
                if change_pct >= 3.0:
                    
                    # Quick check on RSI to avoid alert on exhausted trend
                    # This requires historical data, which might slow down the loop.
                    # Optimization: Only check RSI if gain is detected.
                    try:
                        from analyzer import analyze_stock
                        # We use analyze_stock implicitly or just fetch history quick
                        from data_fetcher import get_historical_data
                        import ta
                        
                        hist = get_historical_data(ticker, period="1mo")
                        if not hist.empty and len(hist) > 14:
                            # Recalculate RSI quick
                            rsi = ta.momentum.RSIIndicator(hist['Close'], window=14).rsi().iloc[-1]
                        else:
                            rsi = 50 # Default neutral if no data
                            
                    except Exception as e:
                        logger.warning(f"RSI check failed for {ticker}: {e}")
                        rsi = 50

                    # Smart Trigger:
                    # 1. Gain > 3% AND RSI < 70 (Room to grow)
                    # 2. OR Gain > 5% (Strong pump regardless of RSI)
                    
                    is_alert = False
                    reason = ""
                    
                    if change_pct > 5.0:
                        is_alert = True
                        reason = "🚀 PUMP ALERT (>5%)"
                    elif change_pct > 3.0 and rsi < 70:
                        is_alert = True
                        reason = f"⚡ PERGERAKAN SIGNIFIKAN (>3%, RSI {rsi:.1f})"

                    if is_alert:
                        # Premium Alert Format
                        emoji_alert = "🚀" if change_pct > 0 else "🔻"
                        alert_msg = (
                            f"🔔 *NEXUS SIGNAL ALERT* {emoji_alert}\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"💎 *{ticker}* (IDX)\n\n"
                            f"💵 *Harga*: Rp {price:,.0f}\n"
                            f"📈 *Kenaikan*: +{change_pct:.2f}%\n"
                            f"🔊 *Volume*: {volume:,.0f} (High Activity)\n"
                            f"📊 *RSI (14)*: {rsi:.1f}\n\n"
                            f"📝 *Analisis Singkat*:\n"
                            f"{reason}\n\n"
                            f"👉 *Action*: Cek chart & fundamental sekarang!\n"
                            f"Generate Chart: `/chart {ticker}`\n"
                            f"Analisis AI: `/analisa {ticker}`"
                        )
                        alerts.append(alert_msg)
            
            except Exception as e:
                logger.error(f"Error scanning {ticker}: {e}")
                continue
                
        return alerts
