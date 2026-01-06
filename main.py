import logging
import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from data_fetcher import get_stock_price, get_top_gainers_losers_idx
from chart_generator import generate_chart
from analyzer import analyze_stock, predict_future_price, scan_bsjp_strategy
from idx_tickers import IDX_WATCHLIST

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
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "@your_channel_id")

# Global Monitor Instance
monitor = StockMonitor()

# --- Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 *IDX PREMIUM BOT V2*\n"
        "------------------------------\n"
        "/harga <kode> - Harga Live & Data Kunci\n"
        "/chart <kode> - Chart Dark Mode + RSI/MACD\n"
        "/analisa <kode> - Sinyal AI + Pola Candle\n"
        "/news <kode> - Berita Terupdate (EKSKLUSIF)\n"
        "/predict <kode> - Prediksi Algoritma\n"
        "/gainers - Top Movers Hari Ini\n"
        "------------------------------\n"
        "_Data delay 15 min (Free)_"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def harga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gunakan: /harga <kode>")
        return

    ticker = context.args[0].upper()
    waiting_msg = await update.message.reply_text(f"🔍 Mencari data premium {ticker}...")
    
    data = get_stock_price(ticker)
    
    if data:
        emoji = "🚀" if data['change'] >= 0 else "🔻"
        color = "🟢" if data['change'] >= 0 else "🔴"
        
        # Premium Card Style
        msg = (
            f"{color} *{data['ticker']}* {emoji}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💰 *Harga*: Rp {data['price']:,.0f}\n"
            f"📊 *Change*: {data['change']:+,.0f} ({data['change_pct']:.2f}%)\n"
            f"📈 *High/Low*: {data['high']:,.0f} - {data['low']:,.0f}\n"
            f"📦 *Volume*: {data['volume']:,.0f}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"_Gunakan /analisa {ticker} untuk detil teknikal_"
        )
        await waiting_msg.edit_text(msg, parse_mode='Markdown')
    else:
        await waiting_msg.edit_text(f"❌ Data {ticker} tidak ditemukan.")

async def chart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gunakan: /chart <kode> [periode: 1d, 5d, 1mo, 3mo]")
        return

    ticker = context.args[0].upper()
    period = context.args[1] if len(context.args) > 1 else "3mo"
    
    await update.message.reply_text(f"🎨 Generating Premium Chart {ticker} ({period})...")
    
    # Send 'typing' action or just wait
    img_buf = generate_chart(ticker, period)
    if img_buf:
        await update.message.reply_photo(
            photo=img_buf, 
            caption=f"📊 *Chart Premium: {ticker} ({period})*\n_Dilengkapi RSI & MACD_"
        )
    else:
        await update.message.reply_text("❌ Gagal membuat chart. Cek kode saham.")

async def analisa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gunakan: /analisa <kode>")
        return
        
    ticker = context.args[0].upper()
    waiting_msg = await update.message.reply_text(f"🧠 AI sedang menganalisis {ticker}...")
    
    summary, signal = analyze_stock(ticker)
    await waiting_msg.edit_text(summary, parse_mode='Markdown')

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gunakan: /news <kode>")
        return
        
    ticker = context.args[0].upper()
    waiting_msg = await update.message.reply_text(f"📰 Mengambil berita {ticker}...")
    
    items = get_stock_news(ticker)
    msg = format_news_message(ticker, items)
    
    await waiting_msg.edit_text(msg, parse_mode='Markdown')

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Gunakan: /predict <kode>")
        return
        
    ticker = context.args[0].upper()
    waiting_msg = await update.message.reply_text(f"🔮 Menghitung prediksi {ticker}...")
    
    res = predict_future_price(ticker)
    await waiting_msg.edit_text(res, parse_mode='Markdown')

async def gainers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Scanning Top Gainers...")
    g, _ = get_top_gainers_losers_idx()
    if not g:
        await update.message.reply_text("Data tidak tersedia.")
        return
        
    msg = "🚀 *Top Gainers Hari Ini*\n"
    for s in g:
        msg += f"{s['ticker']}: {s['price']:,.0f} (+{s['change_pct']:.2f}%)\n"
    await update.message.reply_text(msg, parse_mode='Markdown')

async def losers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Scanning Top Losers...")
    _, l = get_top_gainers_losers_idx()
    if not l:
        await update.message.reply_text("Data tidak tersedia.")
        return
        
    msg = "🔻 *Top Losers Hari Ini*\n"
    for s in l:
        msg += f"{s['ticker']}: {s['price']:,.0f} ({s['change_pct']:.2f}%)\n"
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
    
    # Setup JobQueue for background alerts
    job_queue = application.job_queue
    # Run every 5 minutes (300s)
    job_queue.run_repeating(market_alert_job, interval=300, first=10)
    
    print("Bot is running...")
    application.run_polling()
