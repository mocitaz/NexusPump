import logging
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from data_fetcher import get_stock_price, get_top_gainers_losers_idx, get_stock_news
from chart_generator import generate_chart
from analyzer import analyze_stock, predict_future_price, scan_bsjp_strategy, scan_market_screener
from idx_tickers import IDX_WATCHLIST
from alerts import StockMonitor, MarketSessionReporter
import datetime
import pytz

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Configuration ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8446598251:AAE7EnK-1qwtr4hVLJF5TotPvcqYqB4jiCw")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "@nexuspump")

# Global Monitor Instance
monitor = StockMonitor()

# --- Helpers ---

def get_common_keyboard(ticker):
    """
    Returns the standard Navigation Keyboard for a ticker.
    """
    keyboard = [
        [
            InlineKeyboardButton("📊 Chart", callback_data=f"CHART:{ticker}"),
            InlineKeyboardButton("🧠 Analisa", callback_data=f"ANALYSIS:{ticker}"),
        ],
        [
            InlineKeyboardButton("🔮 Predict", callback_data=f"PREDICT:{ticker}"),
            InlineKeyboardButton("📰 Berita", callback_data=f"NEWS:{ticker}"),
        ],
        [
            InlineKeyboardButton("💵 Live Price", callback_data=f"PRICE:{ticker}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

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
        "💡 _Tip: Klik tombol pada pesan balasan untuk navigasi cepat._"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

# ...

async def harga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Support direct call or callback context override
    args = context.args if hasattr(context, 'args') and context.args else context.args
    
    if not args:
         if update.message:
            await update.message.reply_text("⛔ Gunakan format: `/harga <kode saham>`", parse_mode='Markdown')
         return

    ticker = args[0].upper()
    
    # Determines where to reply
    message_source = update.message if update.message else update.callback_query.message
    
    waiting_msg = await message_source.reply_text(f"🔄 *Fetching Live Data {ticker}...* (Wait)", parse_mode='Markdown')
    
    data = get_stock_price(ticker, detailed=True)
    
    if data:
        emoji = "🚀" if data['change'] >= 0 else "🔻"
        color_indicator = "🟢 BULLISH" if data['change'] >= 0 else "🔴 BEARISH"
        
        mcap = data.get('market_cap', 0)
        if mcap >= 1_000_000_000_000: mcap_str = f"{mcap/1_000_000_000_000:.2f} T"
        elif mcap >= 1_000_000_000: mcap_str = f"{mcap/1_000_000_000:.0f} M"
        else: mcap_str = f"{mcap:,.0f}"

        last_upd = data.get('last_updated', 'N/A')
        
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
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )
        
        # Add Buttons
        kb = get_common_keyboard(ticker)
        await waiting_msg.edit_text(msg, parse_mode='Markdown', reply_markup=kb)
        
    else:
        await waiting_msg.edit_text(f"❓ *Data tidak ditemukan*.\nPastikan kode saham benar.", parse_mode='Markdown')

async def chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args if hasattr(context, 'args') and context.args else context.args
    if not args:
        if update.message: await update.message.reply_text("⛔ Gunakan format: `/chart <kode>`", parse_mode='Markdown')
        return

    ticker = args[0].upper()
    period = args[1] if len(args) > 1 else "3mo"
    
    # Reply target
    target_msg = update.message if update.message else update.callback_query.message
    status_msg = await target_msg.reply_text(f"🎨 *Menggambar Chart {ticker}...*", parse_mode='Markdown')
    
    img_buf = generate_chart(ticker, period)
    if img_buf:
        time_str = datetime.datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%H:%M')
        kb = get_common_keyboard(ticker)
        
        # Send photo (cannot edit text to photo easily, so delete status and send new)
        await status_msg.delete()
        await target_msg.reply_photo(
            photo=img_buf, 
            caption=(
                f"📈 *PROFESSIONAL CHART: {ticker}*\n"
                f"⏰ {time_str} WIB\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "• 🔵 Line Biru: MA20 (Short Term)\n"
                "• 🟠 Line Oranye: MA50 (Medium Term)\n"
                "• ⚫ Line Hitam: MA100 (Long Term)\n"
                "• 📊 Sub-plot: RSI & MACD Momentum"
            ),
            parse_mode='Markdown',
            reply_markup=kb
        )
    else:
        await status_msg.edit_text("❌ Gagal membuat chart.")

async def analisa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args if hasattr(context, 'args') and context.args else context.args
    if not args:
        if update.message: await update.message.reply_text("⛔ Gunakan format: `/analisa <kode>`", parse_mode='Markdown')
        return
        
    ticker = args[0].upper()
    target_msg = update.message if update.message else update.callback_query.message
    waiting_msg = await target_msg.reply_text(f"🧠 AI sedang melakukan analisis mendalam *{ticker}*...", parse_mode='Markdown')
    
    summary, signal = analyze_stock(ticker)
    kb = get_common_keyboard(ticker)
    
    await waiting_msg.edit_text(summary, parse_mode='Markdown', reply_markup=kb)

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args if hasattr(context, 'args') and context.args else context.args
    if not args:
        if update.message: await update.message.reply_text("⛔ Gunakan format: `/news <kode>`", parse_mode='Markdown')
        return
        
    ticker = args[0].upper()
    target_msg = update.message if update.message else update.callback_query.message
    waiting_msg = await target_msg.reply_text(f"📰 Mengumpulkan berita terkini *{ticker}*...", parse_mode='Markdown')
    
    items = get_stock_news(ticker)
    
    if not items:
        msg = f"❌ Tidak ada berita terbaru untuk *{ticker}*."
    else:
        time_str = datetime.datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%H:%M')
        msg = f"📰 *HEADLINES: {ticker}*\n⏰ {time_str} WIB\n━━━━━━━━━━━━━━━━━━━━━━\n"
        for item in items[:5]:
            msg += f"• [{item['title']}]({item['link']})\n  _Sumber: {item['source']} - {item['published']}_\n\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━"

    kb = get_common_keyboard(ticker)
    await waiting_msg.edit_text(msg, parse_mode='Markdown', reply_markup=kb)

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args if hasattr(context, 'args') and context.args else context.args
    if not args:
        if update.message: await update.message.reply_text("⛔ Gunakan format: `/predict <kode>`", parse_mode='Markdown')
        return
        
    ticker = args[0].upper()
    target_msg = update.message if update.message else update.callback_query.message
    waiting_msg = await target_msg.reply_text(f"🔮 Mengkalkulasi proyeksi harga *{ticker}*...", parse_mode='Markdown')
    
    res = predict_future_price(ticker)
    time_str = datetime.datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%H:%M')
    res += f"\n\n⏰ Generated: {time_str} WIB"
    
    kb = get_common_keyboard(ticker)
    await waiting_msg.edit_text(res, parse_mode='Markdown', reply_markup=kb)

# --- Button Callback Handler ---

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer() # Stop loading animation
    
    data = query.data.split(":")
    if len(data) < 2: return
    
    cmd = data[0]
    ticker = data[1]
    
    # Inject args so functions know what to do
    context.args = [ticker]
    
    # Route
    if cmd == "CHART":
        await chart(update, context)
    elif cmd == "PRICE":
        await harga(update, context)
    elif cmd == "ANALYSIS":
        await analisa(update, context)
    elif cmd == "PREDICT":
        await predict(update, context)
    elif cmd == "NEWS":
        await news(update, context)


async def gainers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_msg = update.message if update.message else update.callback_query.message
    waiting = await target_msg.reply_text("🔎 *Scanning Top Gainers...*", parse_mode='Markdown')
    
    g, _ = get_top_gainers_losers_idx()
    if not g:
        await waiting.edit_text("❌ Data pasar tidak tersedia.")
        return
        
    # Build msg
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
    # We can add a refresh button or check details for top 1?
    # For now keep simple.
    await waiting.edit_text(msg, parse_mode='Markdown')

async def losers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_msg = update.message if update.message else update.callback_query.message
    waiting = await target_msg.reply_text("🔎 *Scanning Top Losers...*", parse_mode='Markdown')
    
    _, l = get_top_gainers_losers_idx()
    if not l:
        await waiting.edit_text("❌ Data pasar tidak tersedia.")
        return
        
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
    
    msg = "🔻 *TOP LOSERS HARI INI*\n" + f"```\n{chr(10).join(lines)}\n```\n"
    await waiting.edit_text(msg, parse_mode='Markdown')

async def screener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_msg = update.message if update.message else update.callback_query.message
    waiting = await target_msg.reply_text("🕵️‍♂️ *Menganalisis Market... (Mohon tunggu)*", parse_mode='Markdown')
    
    results = scan_market_screener(IDX_WATCHLIST)
    if not results:
        await waiting.edit_text("❌ *Market Screener*: Data tidak tersedia atau pasar tutup.", parse_mode='Markdown')
        return
        
    header = "ROKET  HARGA  POT%  STS"
    lines = []
    lines.append(header)
    lines.append("-" * 25)
    
    for r in results[:15]:
        ticker = r['ticker'][:4]
        p_val = r['price']
        if p_val >= 1000: p_str = f"{p_val/1000:.1f}K"
        else: p_str = f"{p_val:.0f}"
        pot_val = r['potential']
        pot_str = f"{pot_val:+.0f}%"
        bandar_icon = "🐳" if "AKUM" in r['bandar'] else "🔻" if "DIST" in r['bandar'] else "➖"
        safety_icon = "✅" if "AMAN" in r['bsjp'] else "⚠️"
        status = f"{bandar_icon}{safety_icon}"
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
    await waiting.edit_text(final_msg, parse_mode='Markdown')

async def bsjp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_msg = update.message if update.message else update.callback_query.message
    waiting = await target_msg.reply_text("🔎 Scanning Market untuk peluang BSJP...\n_Mohon tunggu..._", parse_mode='Markdown')
    
    candidates = scan_bsjp_strategy(IDX_WATCHLIST)
    time_str = datetime.datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%H:%M')
    
    if not candidates:
        await waiting.edit_text(f"❌ Tidak ada rekomendasi BSJP hari ini.\n⏰ Checked: {time_str} WIB")
        return
        
    msg = f"🌅 *Rekomendasi BSJP (High Risk)*\n⏰ Pukul: {time_str} WIB\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for c in candidates[:10]: 
        msg += (
            f"🎯 *{c['ticker']}* @ {c['price']:,.0f}\n"
            f"   📈 Naik: {c['change']:.1f}% | 🔊 Vol: {c['volume_ratio']:.1f}x Avg\n"
        )
    msg += "\n_Syarat: Uptrend, Vol > Avg, Close near High._"
    await waiting.edit_text(msg, parse_mode='Markdown')

# --- Background Tasks ---

async def market_alert_job(context: ContextTypes.DEFAULT_TYPE):
    """
    Background job to scan for alerts and send to channel.
    Double-Check Market Hours here to prevent Spam Loop.
    """
    tz_jkt = pytz.timezone('Asia/Jakarta')
    now = datetime.datetime.now(tz_jkt)
    
    if now.weekday() > 4: return # No weekend

    current_time = now.time()
    start_time = datetime.time(9, 0)
    end_time = datetime.time(16, 15)
    
    if not (start_time <= current_time <= end_time): return

    alerts = await monitor.scan_market()
    if alerts:
        # Alerts is now a list of dicts: {'text': str, 'ticker': str}
        for item in alerts:
            alert_text = item['text']
            ticker = item['ticker']
            
            # Attach Action Buttons
            kb = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📊 Chart", callback_data=f"CHART:{ticker}"),
                    InlineKeyboardButton("🧠 Analisa", callback_data=f"ANALYSIS:{ticker}")
                ]
            ])
            
            try:
                if CHANNEL_ID and CHANNEL_ID != "@your_channel_id":
                    await context.bot.send_message(chat_id=CHANNEL_ID, text=alert_text, parse_mode='Markdown', reply_markup=kb)
                else:
                    logger.warning("Channel ID not set.")
            except Exception as e:
                logger.error(f"Failed to send alert: {e}")

# ... Session reporters (unchanged) ...
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
    if not update.channel_post or not update.channel_post.text: return
    text = update.channel_post.text
    if not text.startswith('/'): return
    parts = text.split()
    command = parts[0].lower().split('@')[0].replace('/', '')
    args = parts[1:]
    context.args = args
    # ... logic same as before ... using map
    cmd_map = {
        'start': start, 'harga': harga, 'chart': chart, 'analisa': analisa,
        'news': news, 'predict': predict, 'screener': screener, 'bsjp': bsjp,
        'gainers': gainers, 'losers': losers
    }
    if command in cmd_map:
        await cmd_map[command](update, context)

if __name__ == '__main__':
    if TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        print("Set ENV 'TELEGRAM_BOT_TOKEN' first!")
        
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Handlers
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
    
    # CALLBACK HANDLER (The New V14 Core)
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Channel Handler
    channel_filter = filters.ChatType.CHANNEL & filters.Regex(r'^/')
    application.add_handler(MessageHandler(channel_filter, channel_command_dispatcher))
    
    # Jobs
    job_queue = application.job_queue
    job_queue.run_repeating(market_alert_job, interval=300, first=10)
    
    tz_jkt = pytz.timezone('Asia/Jakarta')
    weekdays = (0, 1, 2, 3, 4)
    job_queue.run_daily(session_open, time=datetime.time(hour=9, minute=0, tzinfo=tz_jkt), days=weekdays)
    job_queue.run_daily(session_mid, time=datetime.time(hour=12, minute=0, tzinfo=tz_jkt), days=weekdays)
    job_queue.run_daily(session_open2, time=datetime.time(hour=13, minute=30, tzinfo=tz_jkt), days=weekdays)
    job_queue.run_daily(session_close, time=datetime.time(hour=16, minute=0, tzinfo=tz_jkt), days=weekdays)
    
    print("--- NEXUS PUMP BOT V14 (Inline Buttons) STARTING ---")
    application.run_polling()
