import logging
import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from data_fetcher import get_stock_price, get_top_gainers_losers_idx
from chart_generator import generate_chart
from analyzer import analyze_stock, predict_future_price, scan_bsjp_strategy, scan_market_screener
from idx_tickers import IDX_WATCHLIST
from alerts import StockMonitor, MarketSessionReporter
import datetime
import pytz

# ... (Previous imports)

# ...

async def bsjp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔎 Scanning Market untuk peluang BSJP (Beli Sore Jual Pagi)...\n_Mohon tunggu, memproses data 70+ saham..._")
    
    candidates = scan_bsjp_strategy(IDX_WATCHLIST)
    time_str = datetime.datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%H:%M')
    
    if not candidates:
        await update.message.reply_text(f"❌ Tidak ada rekomendasi BSJP hari ini.\n⏰ Checked: {time_str} WIB")
        return
        
    msg = f"🌅 *Rekomendasi BSJP (High Risk)*\n⏰ Pukul: {time_str} WIB\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for c in candidates[:10]: 
        msg += (
            f"🎯 *{c['ticker']}* @ {c['price']:,.0f}\n"
            f"   📈 Naik: {c['change']:.1f}% | 🔊 Vol: {c['volume_ratio']:.1f}x Avg\n"
        )
        
    msg += "\n_Syarat: Uptrend, Vol > Avg, Close near High._\n_DYOR! Not Financial Advice._"
    await update.message.reply_text(msg, parse_mode='Markdown')

# ...

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⛔ Gunakan format: `/predict <kode>`", parse_mode='Markdown')
        return
        
    ticker = context.args[0].upper()
    await update.message.reply_text(f"🔮 *Simulasi Prediksi Harga {ticker}...*", parse_mode='Markdown')
    
    res = predict_future_price(ticker)
    
    # Append timestamp
    time_str = datetime.datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%H:%M')
    res += f"\n\n⏰ Generated: {time_str} WIB"
    
    await update.message.reply_text(res, parse_mode='Markdown')


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Configuration ---
# Replace with your actual values or env vars
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8446598251:AAE7EnK-1qwtr4hVLJF5TotPvcqYqB4jiCw")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "@nexuspump")

# Global Monitor Instance
monitor = StockMonitor()

# --- Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    help_text = (
        f"👋 *Halo, {user}! Welcome to Nexus Pump Pro.* 👑\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Saya adalah asisten pasar modal pribadi Anda.\n"
        "Gunakan perintah di bawah untuk analisa mendalam:\n\n"
        "🔍 *MARKET TOOLS*\n"
        "• `/screener` : Pindai saham potensial (Bandar & Safety).\n"
        "• `/gainers`  : Top 5 Saham Paling Cuan Hari Ini.\n"
        "• `/losers`   : Top 5 Saham Paling Boncos.\n\n"
        "📊 *DEEP DIVE*\n"
        "• `/analisa <kode>` : Analisis AI, Sinyal, & Pivot.\n"
        "• `/chart <kode>`   : Chart Professional (MA + Volume).\n"
        "• `/predict <kode>` : Proyeksi Harga 7 Hari.\n"
        "• `/news <kode>`    : Sentimen Berita Terkini.\n"
        "• `/harga <kode>`   : Data Fundamental & Valuasi.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 _Command Secret tersedia bagi yang tahu._"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

# ... screener ...

async def chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⛔ Gunakan format: `/chart <kode>`", parse_mode='Markdown')
        return

    ticker = context.args[0].upper()
    period = context.args[1] if len(context.args) > 1 else "3mo"
    
    await update.message.reply_text(f"🎨 *Menggambar Chart {ticker}...*", parse_mode='Markdown')
    
    img_buf = generate_chart(ticker, period)
    if img_buf:
        time_str = datetime.datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%H:%M')
        await update.message.reply_photo(
            photo=img_buf, 
            caption=(
                f"📈 *PROFESSIONAL CHART: {ticker}*\n"
                f"⏰ {time_str} WIB\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "• 🔵 Line Biru: MA20 (Short Term)\n"
                "• 🟠 Line Oranye: MA50 (Medium Term)\n"
                "• ⚫ Line Hitam: MA100 (Long Term)\n"
                "• 📊 Sub-plot: RSI & MACD Momentum\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "_Analisis visual trend pergerakan harga._"
            ),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Gagal membuat chart. Kode saham salah/tidak ada data.")

# ... analisa ... hiding ...

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⛔ Gunakan format: `/news <kode>`", parse_mode='Markdown')
        return
        
    ticker = context.args[0].upper()
    await update.message.reply_text(f"📰 *Mencari Berita {ticker}...*", parse_mode='Markdown')
    
    items = get_stock_news(ticker)
    
    # Custom Formatter for News
    if not items:
        msg = f"❌ Tidak ada berita terbaru untuk *{ticker}*."
    else:
        time_str = datetime.datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%H:%M')
        msg = f"📰 *HEADLINES: {ticker}*\n⏰ {time_str} WIB\n━━━━━━━━━━━━━━━━━━━━━━\n"
        for item in items[:5]:
            msg += f"• [{item['title']}]({item['link']})\n  _Sumber: {item['source']} - {item['published']}_\n\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━"

    await update.message.reply_text(msg, parse_mode='Markdown')

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⛔ Gunakan format: `/predict <kode>`", parse_mode='Markdown')
        return
        
    ticker = context.args[0].upper()
    await update.message.reply_text(f"🔮 *Simulasi Prediksi Harga {ticker}...*", parse_mode='Markdown')
    
    res = predict_future_price(ticker)
    # Ensure footer timestamp in predict result if possible, or append here.
    # Actually predict_future_price returns a string. Let's assume it's fine or we append.
    # For now, let's trust the analyzer's format, but maybe I should have edited analyzer. 
    # Let's just output it.
    await update.message.reply_text(res, parse_mode='Markdown')

async def gainers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔎 *Scanning Top Gainers...*", parse_mode='Markdown')
    g, _ = get_top_gainers_losers_idx()
    if not g:
        await update.message.reply_text("❌ Data pasar tidak tersedia.")
        return
        
    # Table Format
    lines = ["RANK  KODE   HARGA   NAIK%", "-" * 28]
    for i, s in enumerate(g):
        rank = f"#{i+1}"
        tick = s['ticker'][:4]
        price = f"{s['price']/1000:.1f}K" if s['price'] > 1000 else f"{s['price']:.0f}"
        chg = f"+{s['change_pct']:.1f}%"
        lines.append(f"{rank:<4} {tick:<5} {price:>6} {chg:>6}")
    
    lines.append("-" * 28)
    time_str = datetime.datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%H:%M')
    lines.append(f"⏰ {time_str} WIB")
    
    msg = (
        "🚀 *TOP GAINERS HARI INI*\n"
        f"```\n{chr(10).join(lines)}\n```\n"
        "_Delay data 15 menit_"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def losers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔎 *Scanning Top Losers...*", parse_mode='Markdown')
    _, l = get_top_gainers_losers_idx()
    if not l:
        await update.message.reply_text("❌ Data pasar tidak tersedia.")
        return
        
    # Table Format
    lines = ["RANK  KODE   HARGA   TURUN%", "-" * 28]
    for i, s in enumerate(l):
        rank = f"#{i+1}"
        tick = s['ticker'][:4]
        price = f"{s['price']/1000:.1f}K" if s['price'] > 1000 else f"{s['price']:.0f}"
        chg = f"{s['change_pct']:.1f}%"
        lines.append(f"{rank:<4} {tick:<5} {price:>6} {chg:>6}")
    
    lines.append("-" * 28)
    time_str = datetime.datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%H:%M')
    lines.append(f"⏰ {time_str} WIB")
    
    msg = (
        "🔻 *TOP LOSERS HARI INI*\n"
        f"```\n{chr(10).join(lines)}\n```\n"
        "_Delay data 15 menit_"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def screener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_processing = await update.message.reply_text("🕵️‍♂️ *Menganalisis Market... (Mohon tunggu)*", parse_mode='Markdown')
    
    results = scan_market_screener(IDX_WATCHLIST)
    if not results:
        await msg_processing.edit_text("❌ *Market Screener*: Data tidak tersedia atau pasar tutup.", parse_mode='Markdown')
        return
        
    # Create Neat Table
    # Max width handling for Telegram Mobile
    # Code: 4 chars, Price: 5 chars (9.9K), Pot: 4 chars (+9%), Sts: 2 chars
    
    header = "ROKET  HARGA  POT%  STS"
    lines = []
    lines.append(header)
    lines.append("-" * 25)
    
    for r in results[:15]:
        ticker = r['ticker'][:4]
        
        # Format Price (K for thousands to save space)
        p_val = r['price']
        if p_val >= 1000:
            p_str = f"{p_val/1000:.1f}K"
        else:
            p_str = f"{p_val:.0f}"
            
        pot_val = r['potential']
        pot_str = f"{pot_val:+.0f}%"
        
        # Status Icons
        # Bandar: 🐳(Akum),🔻(Dist), ➖(Normal)
        # Safety: ✅(Aman), ⚠️(Risk)
        bandar_icon = "🐳" if "AKUM" in r['bandar'] else "🔻" if "DIST" in r['bandar'] else "➖"
        safety_icon = "✅" if "AMAN" in r['bsjp'] else "⚠️"
        status = f"{bandar_icon}{safety_icon}"
        
        # Rigid alignment:
        # Ticker: 5 chars left
        # Price: 6 chars right
        # Pot: 5 chars right
        # Sts: 5 chars center/right
        line = f"{ticker:<5} {p_str:>6} {pot_str:>5}  {status}"
        lines.append(line)
        
    lines.append("-" * 25)
    lines.append(f"📅 Data: {results[0]['date']} {datetime.datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%H:%M')} WIB")
    
    table_block = "\n".join(lines)
    
    final_msg = (
        "📟 *NEXUS SCREENER PRO*\n"
        f"```\n{table_block}\n```\n"
        "📖 *Legenda*:\n"
        "• `STS`: Status (Bandar 🐳/🔻 + Safety ✅/⚠️)\n"
        "• `POT%`: Upside ke Resistance terdekat.\n"
        "_Update Sesi Ini_"
    )
    
    await msg_processing.edit_text(final_msg, parse_mode='Markdown')

async def harga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⛔ Gunakan format: `/harga <kode saham>`\nContoh: `/harga BBCA`", parse_mode='Markdown')
        return

    ticker = context.args[0].upper()
    waiting_msg = await update.message.reply_text(f"🔄 *Fetching Live Data {ticker}...* (Wait)", parse_mode='Markdown')
    
    # Enable Detailed Mode for 1m interval timestamp
    data = get_stock_price(ticker, detailed=True)
    
    if data:
        emoji = "🚀" if data['change'] >= 0 else "🔻"
        color_indicator = "🟢 BULLISH" if data['change'] >= 0 else "🔴 BEARISH"
        
        # Format Market Cap
        mcap = data.get('market_cap', 0)
        if mcap >= 1_000_000_000_000:
            mcap_str = f"{mcap/1_000_000_000_000:.2f} T"
        elif mcap >= 1_000_000_000:
            mcap_str = f"{mcap/1_000_000_000:.0f} M"
        else:
            mcap_str = f"{mcap:,.0f}"

        # Live Timestamp
        last_upd = data.get('last_updated', 'N/A')
        
        # Ultimate Professional Card
        msg = (
            f"🏢 *{data.get('long_name', ticker)}* ({data['ticker']})\n"
            f"🏷 _{data.get('sector', 'Unknown')}_\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💵 *IDR {data['price']:,.0f}*   {color_indicator}\n"
            f"{emoji} *{data['change']:+,.0f} ({data['change_pct']:.2f}%)*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 *STATISTIK LIVE*:\n"
            f"• Vol     : {data['volume']:,.0f}\n"
            f"• Range   : {data['low']:,.0f} - {data['high']:,.0f}\n"
            f"• Updated : {last_upd} WIB ⏰\n\n"
            f"💎 *FUNDAMENTAL*:\n"
            f"• M.Cap   : Rp {mcap_str}\n"
            f"• PER     : {data.get('pe_ratio', 'N/A') if data.get('pe_ratio') else 'N/A'}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 _Analisis Lanjut?_ `/analisa {ticker}`\n"
            f"📈 _Lihat Chart?_ `/chart {ticker}`"
        )
        await waiting_msg.edit_text(msg, parse_mode='Markdown')
    else:
        await waiting_msg.edit_text(f"❓ *Data tidak ditemukan*.\nPastikan kode saham benar (misal: BBCA, ANTM).", parse_mode='Markdown')

async def chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⛔ Gunakan format: `/chart <kode>`", parse_mode='Markdown')
        return

    ticker = context.args[0].upper()
    period = context.args[1] if len(context.args) > 1 else "3mo"
    
    await update.message.reply_text(f"🎨 Menggambar Chart Professional *{ticker}* ({period})...", parse_mode='Markdown')
    
    img_buf = generate_chart(ticker, period)
    if img_buf:
        await update.message.reply_photo(
            photo=img_buf, 
            caption=f"📈 *Chart Professional: {ticker}*\n_Indikator: MA20/50/100 + Volume_",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Gagal membuat chart. Pastikan kode saham benar.")

async def analisa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⛔ Gunakan format: `/analisa <kode>`", parse_mode='Markdown')
        return
        
    ticker = context.args[0].upper()
    waiting_msg = await update.message.reply_text(f"🧠 AI sedang melakukan analisis mendalam *{ticker}*...", parse_mode='Markdown')
    
    summary, signal = analyze_stock(ticker)
    await waiting_msg.edit_text(summary, parse_mode='Markdown')

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⛔ Gunakan format: `/news <kode>`", parse_mode='Markdown')
        return
        
    ticker = context.args[0].upper()
    waiting_msg = await update.message.reply_text(f"📰 Mengumpulkan berita terkini *{ticker}*...", parse_mode='Markdown')
    
    items = get_stock_news(ticker)
    msg = format_news_message(ticker, items)
    
    await waiting_msg.edit_text(msg, parse_mode='Markdown')

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⛔ Gunakan format: `/predict <kode>`", parse_mode='Markdown')
        return
        
    ticker = context.args[0].upper()
    waiting_msg = await update.message.reply_text(f"🔮 Mengkalkulasi proyeksi harga *{ticker}*...", parse_mode='Markdown')
    
    res = predict_future_price(ticker)
    await waiting_msg.edit_text(res, parse_mode='Markdown')

async def gainers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Memindai Top Gainers IHSG...", parse_mode='Markdown')
    g, _ = get_top_gainers_losers_idx()
    if not g:
        await update.message.reply_text("❌ Data pasar tidak tersedia saat ini.")
        return
        
    msg = "🚀 *TOP 5 GAINERS HARI INI*\n━━━━━━━━━━━━━━━━━━━━\n"
    for i, s in enumerate(g):
        msg += f"{i+1}. *{s['ticker']}*: {s['price']:,.0f} (+{s['change_pct']:.2f}%)\n"
    
    msg += "\n_Update Real-time (Delay 15m)_"
    await update.message.reply_text(msg, parse_mode='Markdown')

async def losers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Memindai Top Losers IHSG...", parse_mode='Markdown')
    _, l = get_top_gainers_losers_idx()
    if not l:
        await update.message.reply_text("❌ Data pasar tidak tersedia saat ini.")
        return
        
    msg = "🔻 *TOP 5 LOSERS HARI INI*\n━━━━━━━━━━━━━━━━━━━━\n"
    for i, s in enumerate(l):
        msg += f"{i+1}. *{s['ticker']}*: {s['price']:,.0f} ({s['change_pct']:.2f}%)\n"
        
    msg += "\n_Update Real-time (Delay 15m)_"
    await update.message.reply_text(msg, parse_mode='Markdown')

# --- Background Tasks ---

async def market_alert_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Background job to scan for alerts and send to channel.
    """
    alerts = await monitor.scan_market()
    if alerts:
        for alert in alerts:
            # Send to configured channel
            try:
                if CHANNEL_ID and CHANNEL_ID != "@your_channel_id":
                    await context.bot.send_message(chat_id=CHANNEL_ID, text=alert, parse_mode='Markdown')
                else:
                    logger.warning("Channel ID not set, skipping sending alert.")
            except Exception as e:
                logger.error(f"Failed to send alert: {e}")

async def session_open(context: ContextTypes.DEFAULT_TYPE):
    reporter = MarketSessionReporter(context.application)
    await reporter.send_report(context, 'open')

async def session_mid(context: ContextTypes.DEFAULT_TYPE):
    reporter = MarketSessionReporter(context.application)
    await reporter.send_report(context, 'mid')

async def session_open2(context: ContextTypes.DEFAULT_TYPE):
    reporter = MarketSessionReporter(context.application)
    await reporter.send_report(context, 'open2')

async def session_close(context: ContextTypes.DEFAULT_TYPE):
    reporter = MarketSessionReporter(context.application)
    await reporter.send_report(context, 'close')

async def channel_command_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Manually handles commands sent in CHANNELS (Update.channel_post).
    Standard CommandHandler ignores channel posts, so we need this.
    """
    if not update.channel_post or not update.channel_post.text:
        return
        
    text = update.channel_post.text
    if not text.startswith('/'):
        return
        
    parts = text.split()
    command = parts[0].lower().split('@')[0].replace('/', '') # clean /start@BotName -> start
    args = parts[1:]
    
    # Inject args into context for compatibility with existing string handlers
    context.args = args
    
    # Route to functions
    if command == 'start':
        await start(update, context)
    elif command == 'harga':
        await harga(update, context)
    elif command == 'chart':
        await chart(update, context)
    elif command == 'analisa':
        await analisa(update, context)
    elif command == 'news':
        await news(update, context)
    elif command == 'predict':
        await predict(update, context)
    elif command == 'screener':
        await screener(update, context)
    elif command == 'bsjp':
        await bsjp(update, context)
    elif command == 'gainers':
        await gainers(update, context)
    elif command == 'losers':
        await losers(update, context)
    # else: ignore unknown commands

if __name__ == '__main__':
    if TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        print("Set ENV 'TELEGRAM_BOT_TOKEN' first!")
        
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Standard Handlers (Private & Group)
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('harga', harga))
    application.add_handler(CommandHandler('chart', chart))
    application.add_handler(CommandHandler('analisa', analisa))
    application.add_handler(CommandHandler('news', news))
    application.add_handler(CommandHandler('bsjp', bsjp))
    application.add_handler(CommandHandler('predict', predict))
    application.add_handler(CommandHandler('gainers', gainers))
    application.add_handler(CommandHandler('losers', losers))
    application.add_handler(CommandHandler('screener', screener))
    
    # SPECIAL HANDLER FOR CHANNELS
    # Listen to text in Channels that looks like a command
    from telegram.ext import filters, MessageHandler
    channel_filter = filters.ChatType.CHANNEL & filters.Regex(r'^/')
    application.add_handler(MessageHandler(channel_filter, channel_command_dispatcher))
    
    # Setup JobQueue for background alerts
    
    # Setup JobQueue for background alerts
    job_queue = application.job_queue
    
    # 1. Regular Alert Scan (Every 5 mins)
    job_queue.run_repeating(market_alert_job, interval=300, first=10)
    
    # 2. Scheduled Market Reports (WIB / UTC+7)
    # Railway might be UTC, so we must be precise with Timezone object.
    tz_jkt = pytz.timezone('Asia/Jakarta')
    
    # Days: 0=Mon, 4=Fri
    weekdays = (0, 1, 2, 3, 4)
    
    # 09:00 WIB - Opening
    job_queue.run_daily(session_open, time=datetime.time(hour=9, minute=0, tzinfo=tz_jkt), days=weekdays)
    
    # 12:00 WIB - Mid Break
    job_queue.run_daily(session_mid, time=datetime.time(hour=12, minute=0, tzinfo=tz_jkt), days=weekdays)
    
    # 13:30 WIB - Sesi 2
    job_queue.run_daily(session_open2, time=datetime.time(hour=13, minute=30, tzinfo=tz_jkt), days=weekdays)
    
    # 16:00 WIB - Closing
    job_queue.run_daily(session_close, time=datetime.time(hour=16, minute=0, tzinfo=tz_jkt), days=weekdays)
    
    print("--- NEXUS PUMP BOT V5 (Screener + Reporter) STARTING ---")
    print("Bot is running...")
    application.run_polling()
