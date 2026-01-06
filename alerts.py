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

class MarketSessionReporter:
    def __init__(self, bot_app):
        self.bot = bot_app
        
    async def send_report(self, context, session_type):
        """
        Generates and sends market reports based on session.
        session_type: 'open', 'mid', 'open2', 'close'
        """
        logger.info(f"Generating market report: {session_type}")
        
        # 1. Get Top Movers from Watchlist
        from data_fetcher import get_top_gainers_losers_idx
        gainers, losers = get_top_gainers_losers_idx() 
        
        # 2. Construct Message
        if session_type == 'open':
            msg = (
                "🔔 *MARKET OPENING (SESI 1)* 🔔\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Selamat pagi Traders! Market IHSG telah dibuka.\n"
                "Pantau volatilitas awal 15 menit pertama.\n\n"
                "🔥 *Fokus Pagi Ini*:\n"
                "Gunakan `/screener` untuk mencari saham yang breakout pagi ini.\n"
                "Gunakan `/gainers` untuk melihat top movers awal."
            )
            
        elif session_type == 'mid':
            # Mid day recap
            top3 = gainers[:3] if gainers else []
            msg = (
                "🍱 *RECAP SESI 1 (ISHOMA)* 🍱\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Market istirahat. Berikut highlight sesi 1:\n\n"
                "🚀 *Top Gainers Watchlist*:\n"
            )
            for s in top3:
                msg += f"• *{s['ticker']}*: {s['price']:,.0f} (+{s['change_pct']:.1f}%)\n"
                
            msg += "\n💡 *Saran*: Review portfolio anda. Siapkan rencana untuk Sesi 2."
            
        elif session_type == 'open2':
            msg = (
                "📢 *MARKET SESI 2 DIMULAI* 📢\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Sesi perdagangan terakhir hari ini.\n"
                "Cek apakah ada saham yang *rebound* atau *lanjut naik*.\n\n"
                "👉 Cek `/screener` sekarang."
            )
            
        elif session_type == 'close':
            # Closing recap + BSJP
            top3_g = gainers[:3] if gainers else []
            top3_l = losers[:3] if losers else []
            
            msg = (
                "🏁 *MARKET CLOSED (FINAL)* 🏁\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Hari perdagangan berakhir. Simpan energi untuk besok!\n\n"
                "🚀 *Top Performers*:\n"
            )
            for s in top3_g:
                msg += f"• *{s['ticker']}*: {s['price']:,.0f} (+{s['change_pct']:.1f}%)\n"
                
            msg += "\n🔻 *Top Losers*:\n"
            for s in top3_l:
                msg += f"• *{s['ticker']}*: {s['price']:,.0f} ({s['change_pct']:.1f}%)\n"
                
            msg += "\n🌅 *Info BSJP*:\nCek saham potensi Beli Sore Jual Pagi dengan `/bsjp`."

        else:
            return

        # Send to Channel
        try:
            import os
            channel_id = os.getenv("TELEGRAM_CHANNEL_ID")
            if channel_id:
                await context.bot.send_message(chat_id=channel_id, text=msg, parse_mode='Markdown')
            else:
                logger.warning("No Channel ID for report")
        except Exception as e:
            logger.error(f"Failed to send report: {e}")
