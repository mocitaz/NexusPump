import logging
import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from data_fetcher import get_stock_price, get_top_gainers_losers_idx
from chart_generator import generate_chart
from analyzer import analyze_stock, predict_future_price, scan_bsjp_strategy, scan_market_screener
from idx_tickers import IDX_WATCHLIST
from alerts import StockMonitor

# ... (Previous imports)

# ...

async def bsjp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔎 Scanning Market untuk peluang BSJP (Beli Sore Jual Pagi)...\n_Mohon tunggu, memproses data 70+ saham..._")
    
    candidates = scan_bsjp_strategy(IDX_WATCHLIST)
    
    if not candidates:
        await update.message.reply_text("❌ Tidak ada saham yang memenuhi kriteria BSJP hari ini (Market mungkin bearish/sideways).")
        return
        
    msg = "🌅 *Rekomendasi BSJP (High Risk)*\n\n"
    for c in candidates[:10]: # Top 10 only
        msg += (
            f"🎯 *{c['ticker']}* @ {c['price']:,.0f}\n"
            f"   📈 Naik: {c['change']:.1f}% | 🔊 Vol: {c['volume_ratio']:.1f}x Avg\n"
        )
        
    msg += "\n_Syarat: Uptrend, Vol > Avg, Close near High._\n_DYOR! Not Financial Advice._"
    await update.message.reply_text(msg, parse_mode='Markdown')


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
        f"👋 *Halo, {user}! Selamat datang di Nexus Pump - Professional Trading Assistant.*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Fitur Utama & Cara Penggunaan:\n\n"
        "🔍 *MARKET SCREENER* (Baru!)\n"
        "• `/screener` - Pindai pasar untuk mencari saham potensial (Data, Akumulasi Bandar, Safety).\n"
        "• `/gainers` - Top Gainers hari ini.\n\n"
        "📊 *DEEP ANALYSIS*\n"
        "• `/analisa <kode>` - Analisis AI, Pivot Point, Sinyal & Indikator Lengkap.\n"
        "• `/chart <kode>` - Chart Professional (MA, RSI, MACD).\n"
        "• `/predict <kode>` - Proyeksi harga 7 hari kedepan dengan alasan statistik.\n\n"
        "ℹ️ *FUNDAMENTAL INFO*\n"
        "• `/harga <kode>` - Data harga, Market Cap, PE, dan Sektor.\n"
        "• `/news <kode>` - Berita terkini untuk sentimen pasar.\n\n"
        "_Tip: Cobalah fitur /screener setiap pagi/sore untuk melihat potensi market._"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def screener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🕵️‍♂️ *Running Market Screener...*\n_Memproses indikator Bandar & Volatilitas..._", parse_mode='Markdown')
    
    results = scan_market_screener(IDX_WATCHLIST)
    if not results:
        await update.message.reply_text("❌ Tidak ada data yang tersedia/Pasar tutup.")
        return
        
    # Create Table
    msg = "📟 *NEXUS MARKET SCREENER* 📟\n"
    msg += f"📅 Data: {results[0]['date']}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "`Kode  | Harga  | Potensi | Bandar | Safety`\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    # Show Top 15
    for r in results[:15]:
        # Truncate for formatting
        ticker = f"{r['ticker']:<5}"
        price = f"{r['price']:<6,.0f}"
        pot = f"+{r['potential']:<4.1f}%"
        bandar = "🐳" if "AKUM" in r['bandar'] else "🔻" if "DIST" in r['bandar'] else "➖"
        safe = "✅" if "AMAN" in r['bsjp'] else "⚠️"
        
        msg += f"`{ticker} {price} {pot}  {bandar}    {safe}`\n"
        
    msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "_Ket: Potensi (Jarak ke R1), Bandar (Vol Flow), Safety (Volatilitas)_"
    
    await update.message.reply_text(msg, parse_mode='Markdown')

async def harga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⛔ Gunakan format: `/harga <kode saham>`\nContoh: `/harga BBCA`", parse_mode='Markdown')
        return

    ticker = context.args[0].upper()
    waiting_msg = await update.message.reply_text(f"🔄 Sedang mengambil data lengkap *{ticker}*...", parse_mode='Markdown')
    
    data = get_stock_price(ticker)
    
    if data:
        emoji = "💹" if data['change'] >= 0 else "🔻"
        color_indicator = "🟢 Bullish" if data['change'] >= 0 else "🔴 Bearish"
        
        # Format Market Cap to Triliun/Miliar
        mcap = data['market_cap']
        if mcap >= 1_000_000_000_000:
            mcap_str = f"{mcap/1_000_000_000_000:.2f} T"
        elif mcap >= 1_000_000_000:
            mcap_str = f"{mcap/1_000_000_000:.0f} M"
        else:
            mcap_str = f"{mcap:,.0f}"

        msg = (
            f"🏢 *{data['long_name']} ({data['ticker']})*\n"
            f"Kategori: _{data['sector']}_\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 *Harga*: Rp {data['price']:,.0f}\n"
            f"{emoji} *Perubahan*: {data['change']:+,.0f} ({data['change_pct']:.2f}%)\n"
            f"📊 *Status*: {color_indicator}\n\n"
            f"📉 *Rentang Harian*:\n"
            f"Low: {data['low']:,.0f} — High: {data['high']:,.0f}\n\n"
            f"📦 *Statistik Kunci*:\n"
            f"• Vol: {data['volume']:,.0f}\n"
            f"• M.Cap: Rp {mcap_str}\n"
            f"• PE Ratio: {data['pe_ratio'] if data['pe_ratio'] else '-'}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"ℹ️ _Ketik /analisa {ticker} untuk sinyal beli/jual._"
        )
        await waiting_msg.edit_text(msg, parse_mode='Markdown')
    else:
        await waiting_msg.edit_text(f"❌ Data *{ticker}* tidak ditemukan atau simbol salah.", parse_mode='Markdown')

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

if __name__ == '__main__':
    if TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        print("Set ENV 'TELEGRAM_BOT_TOKEN' first!")
        
    application = ApplicationBuilder().token(TOKEN).build()
    
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
    
    # Setup JobQueue for background alerts
    job_queue = application.job_queue
    # Run every 5 minutes (300s)
    job_queue.run_repeating(market_alert_job, interval=300, first=10)
    
    print("--- NEXUS PUMP BOT V2 STARTING ---")
    print("Bot is running...")
    application.run_polling()
