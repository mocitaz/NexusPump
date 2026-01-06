import pandas as pd
import datetime
import logging
import pytz
from data_fetcher import get_stock_price

from idx_tickers import IDX_WATCHLIST

logger = logging.getLogger(__name__)

class StockMonitor:
    def __init__(self, watchlist=None):
        if watchlist is None:
            self.watchlist = IDX_WATCHLIST
        else:
            self.watchlist = watchlist
        
        # Spam Protection: Store last alert time for each ticker
        self.alert_cooldowns = {}

    def is_market_open(self):
        """
        Checks if IDX market is currently open (09:00 - 16:15 WIB, Mon-Fri).
        """
        tz_jkt = pytz.timezone('Asia/Jakarta')
        now = datetime.datetime.now(tz_jkt)
        
        # 1. Check Weekend
        if now.weekday() > 4: # 5=Sat, 6=Sun
            return False
            
        # 2. Check Time
        current_time = now.time()
        start_time = datetime.time(9, 0)
        end_time = datetime.time(16, 15)
        
        if start_time <= current_time <= end_time:
            return True
        return False

    async def scan_market(self, context=None):
        """
        Scans values. Returns list of alert strings.
        """
        # 1. Market Hours Check
        if not self.is_market_open():
            return []
            
        alerts = []
        logger.info("Scanning market for alerts...")
        
        tz_jkt = pytz.timezone('Asia/Jakarta')
        now = datetime.datetime.now(tz_jkt)
        time_str = now.strftime('%H:%M')
        
        for ticker in self.watchlist:
            try:
                # 2. Cooldown Check (4 Hours)
                if ticker in self.alert_cooldowns:
                    last_alert = self.alert_cooldowns[ticker]
                    if (now - last_alert).total_seconds() < 14400: 
                        continue
                
                # Fetch fresh data
                data = get_stock_price(ticker)
                if not data:
                    continue
                
                change_pct = data['change_pct']
                price = data['price']
                volume = data['volume']
                
                # Check 1: Significant Gain (>3%)
                if change_pct >= 3.0:
                    
                    # Quick RSI check
                    try:
                        from data_fetcher import get_historical_data
                        import ta
                        
                        hist = get_historical_data(ticker, period="1mo")
                        if not hist.empty and len(hist) > 14:
                            rsi = ta.momentum.RSIIndicator(hist['Close'], window=14).rsi().iloc[-1]
                        else:
                            rsi = 50
                    except Exception as e:
                        # logger.warning(f"RSI check failed for {ticker}: {e}")
                        rsi = 50

                    # Smart Trigger
                    is_alert = False
                    reason = ""
                    
                    if change_pct > 5.0:
                        is_alert = True
                        reason = "🚀 PUMP ALERT (>5%)"
                    elif change_pct > 3.0 and rsi < 70:
                        is_alert = True
                        reason = f"⚡ PERGERAKAN SIGNIFIKAN (>3%, RSI {rsi:.1f})"
                    elif volume > 500000000 and change_pct > 2.0:
                         is_alert = True
                         reason = "🔊 VOLUME SPIKE (Big Money Flow)"

                    if is_alert:
                        # Premium Alert Format
                        emoji_alert = "🚀" if change_pct > 0 else "🔻"
                        alert_msg = (
                            f"🔔 *NEXUS ALERT: {ticker}* {emoji_alert}\n"
                            f"⏰ {time_str} WIB\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"� *IDR {price:,.0f}* ({change_pct:+.2f}%)\n"
                            f"🔊 Vol: {volume:,.0f}\n"
                            f"📊 RSI: {rsi:.1f}\n\n"
                            f"📝 *TRIGGER*: _{reason}_\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"👉 `/chart {ticker}` | `/analisa {ticker}`"
                        )
                        alerts.append(alert_msg)
                        
                        # 3. Set Cooldown
                        self.alert_cooldowns[ticker] = now
            
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
        tz_jkt = pytz.timezone('Asia/Jakarta')
        now = datetime.datetime.now(tz_jkt)
        time_str = now.strftime('%H:%M')
        
        logger.info(f"Generating market report: {session_type} at {time_str}")
        
        # 1. Get Top Movers from Watchlist
        from data_fetcher import get_top_gainers_losers_idx
        gainers, losers = get_top_gainers_losers_idx() 
        
        # 2. Construct Message
        if session_type == 'open':
            msg = (
                f"🔔 *MARKET OPENING (SESI 1)* 🔔\n"
                f"⏰ {time_str} WIB\n"
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
                f"🍱 *RECAP SESI 1 (ISHOMA)* 🍱\n"
                f"⏰ {time_str} WIB\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Market istirahat. Berikut highlight sesi 1:\n\n"
                "🚀 *Top Gainers Watchlist*:\n"
            )
            for s in top3:
                msg += f"• *{s['ticker']}*: {s['price']:,.0f} (+{s['change_pct']:.1f}%)\n"
                
            msg += "\n💡 *Saran*: Review portfolio anda. Siapkan rencana untuk Sesi 2."
            
        elif session_type == 'open2':
            msg = (
                f"📢 *MARKET SESI 2 DIMULAI* 📢\n"
                f"⏰ {time_str} WIB\n"
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
                f"🏁 *MARKET CLOSED (FINAL)* 🏁\n"
                f"⏰ {time_str} WIB\n"
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
