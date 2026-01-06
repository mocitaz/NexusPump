import logging
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from data_fetcher import get_stock_price, get_top_gainers_losers_idx, get_stock_news
from chart_generator import generate_chart
from analyzer import analyze_stock, predict_future_price, scan_bsjp_strategy, scan_market_screener, scan_whale_flow, scan_top_picks

# ... existing imports ...

# ... existing code ...

async def picks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_msg = update.message if update.message else update.callback_query.message
    waiting = await target_msg.reply_text("🔭 *Scanning Nexus Prime Watchlist (Tomorrow)...*", parse_mode='Markdown')
    
    # Async Scan
    try:
        # Use timeout to prevent hanging
        candidates = await asyncio.wait_for(
            asyncio.to_thread(scan_top_picks, IDX_WATCHLIST),
            timeout=30.0 
        )
    except asyncio.TimeoutError:
        await waiting.edit_text("⚠️ *Timeout*. Market Screener sibuk.")
        return
    except Exception as e:
        logger.error(f"Picks error: {e}")
        await waiting.edit_text("❌ Terjadi kesalahan saat scanning.")
        return
        
    if not candidates:
        await waiting.edit_text("❌ Tidak ada saham yang memenuhi kriteria *Prime Picks* hari ini.")
        return

    time_str = datetime.datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%H:%M')
    msg = f"🔭 *NEXUS PRIME PICKS (TOMORROW)*\n⏰ Pukul: {time_str} WIB\n━━━━━━━━━━━━━━━━━━━━━━\n"
    
    for c in candidates[:5]:
        msg += (
            f"💎 *{c['ticker']}* @ {c['price']:,.0f}\n"
            f"   📈 Potensi: {c['reasons']}\n"
            f"   📊 Score: {c['score']} | Vol: {c['vol_ratio']:.1f}x Avg\n\n"
        )
    
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n💡 _Top 5 Saham Uptrend + Akumulasi untuk dipantau besok._"
    await waiting.edit_text(msg, parse_mode='Markdown')

# ... existing code ...

    application.add_handler(CommandHandler('flow', flow))
    application.add_handler(CommandHandler('picks', picks))
    application.add_handler(CommandHandler('rekomendasi', picks))
    
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
    
    print("--- NEXUS PUMP BOT V19-V21 STARTING ---")
    application.run_polling()
