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
        Scans values. Returns list of Dicts {'text': msg, 'ticker': ticker} for button support.
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
                        # Premium Alert Format (God Mode)
                        emoji_alert = "🚀" if change_pct > 0 else "🔻"
                        alert_msg = (
                            f"🔔 *NEXUS FLASH INTELLIGENCE* {emoji_alert}\n"
                            f"🏢 *{ticker}* | ⏰ {time_str} WIB\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━\n"
                            f"💵 Price : {price:,.0f} ({change_pct:+.2f}%)\n"
                            f"🔊 Vol   : {volume:,.0f}\n"
                            f"📊 RSI   : {rsi:.1f}\n\n"
                            f"⚡ *AI TRIGGER*: _{reason}_\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━"
                        )
                        
                        # Pack into Dict for Main.py to add buttons
                        alerts.append({
                            'text': alert_msg,
                            'ticker': ticker
                        })
                        
                        # 3. Set Cooldown
                        self.alert_cooldowns[ticker] = now
            
            except Exception as e:
                logger.error(f"Error scanning {ticker}: {e}")
                continue
                
        return alerts

class MarketSessionReporter:
    def __init__(self, bot_app, channel_id=None):
        self.bot = bot_app
        self.channel_id = channel_id
        
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
                f"🔔 *NEXUS EXECUTIVE BRIEFING: SESSION 1* 🔔\n"
                f"⏰ {time_str} WIB\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Market Opening detected. Volatility scan active.\n"
                "Sistem memantau anomali volume dan breakout awal.\n\n"
                "🔥 *ACTION ITEMS*:\n"
                "• `/screener` : Cari saham breakout pagi.\n"
                "• `/pulse`    : Cek sentimen pasar (Fear/Greed)."
            )
            
        elif session_type == 'mid':
            # Mid day recap
            top3 = gainers[:3] if gainers else []
            msg = (
                f"🍱 *NEXUS MID-DAY RECAP* 🍱\n"
                f"⏰ {time_str} WIB\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Market Break (Sesi 1 Berakhir). Highlight pagi ini:\n\n"
                "🚀 *Leading Movers*:\n"
            )
            for s in top3:
                msg += f"• *{s['ticker']}*: {s['price']:,.0f} (+{s['change_pct']:.1f}%)\n"
                
            msg += "\n💡 *Insight*: Siapkan trading plan untuk Sesi 2."
            
        elif session_type == 'open2':
            msg = (
                f"📢 *NEXUS SESSION 2: ACTIVE* ⚡\n"
                f"⏰ {time_str} WIB\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Sesi terakhir dimulai. Fokus pada saham rebound & akumulasi.\n"
                "Pantau pergerakan Smart Money/Bandar.\n\n"
                "👉 Gunakan `/flow` untuk deteksi Whale."
            )
            
        elif session_type == 'close':
            # Closing recap + BSJP
            top3_g = gainers[:3] if gainers else []
            top3_l = losers[:3] if losers else []
            
            msg = (
                f"🏁 *NEXUS DAILY CLOSING REPORT* 🏁\n"
                f"⏰ {time_str} WIB\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "Perdagangan hari ini ditutup. Berikut ringkasan market:\n\n"
                "🚀 *Top Gainers*:\n"
            )
            for s in top3_g:
                msg += f"• *{s['ticker']}*: {s['price']:,.0f} (+{s['change_pct']:.1f}%)\n"
                
            msg += "\n🔻 *Top Losers*:\n"
            for s in top3_l:
                msg += f"• *{s['ticker']}*: {s['price']:,.0f} ({s['change_pct']:.1f}%)\n"
                
            msg += "\n🌅 *BSJP Candidates*:\nCek potensi cuan besok hari dengan `/bsjp`."

        else:
            return

        # Send to Channel
        try:
            # Prefer injected ID, fallback to env var logic only if really needed (but Init should handle it)
            cid = self.channel_id
            
            if cid:
                if cid == "@your_channel_id":
                     logger.warning("Channel ID is default/invalid. Skipping report.")
                else:
                     await context.bot.send_message(chat_id=cid, text=msg, parse_mode='Markdown')
            else:
                logger.warning("No Channel ID provided for report")
        except Exception as e:
            logger.error(f"Failed to send report: {e}")
