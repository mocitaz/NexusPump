import logging
import os
import asyncio
import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# Modules
from data_fetcher import get_stock_price, get_top_gainers_losers_idx, get_stock_news, get_stock_fundamentals
from chart_generator import generate_chart, generate_portfolio_pie, generate_xray_image, generate_prediction_card
from analyzer import analyze_stock, predict_future_price, scan_bsjp_strategy, scan_market_screener, scan_whale_flow, scan_top_picks, scan_sector_performance, calculate_fibonacci_levels, analyze_radar_metrics
from market_pulse import calculate_market_mood, generate_gauge_chart
from idx_tickers import IDX_WATCHLIST
from alerts import StockMonitor, MarketSessionReporter
from portfolio_manager import PortfolioManager

# ...

async def xray(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Support callback override
    args = context.args if hasattr(context, 'args') and context.args else context.args
    
    if not args:
         if update.message:
            await update.message.reply_text("🩻 Gunakan format: `/xray <kode saham>`", parse_mode='Markdown')
         return

    ticker = args[0].upper()
    target_msg = update.message if update.message else update.callback_query.message
    waiting_msg = await target_msg.reply_text(f"🩻 *Initiating Nexus X-Ray for {ticker}...*\n_Generating Infographic..._", parse_mode='Markdown')
    
    try:
        # 1. Parallel Fetching for Speed
        # We need Radar Scores AND Fibo Levels
        radar_task = asyncio.to_thread(analyze_radar_metrics, ticker)
        fibo_task = asyncio.to_thread(calculate_fibonacci_levels, ticker, period="6mo")
        
        radar_scores, fibo_data = await asyncio.gather(radar_task, fibo_task)
        
        if not radar_scores:
            await waiting_msg.edit_text("❌ Data X-Ray tidak cukup.")
            return
            
        fibo_levels = fibo_data['levels'] if fibo_data else None
        
        # 2. Generate Image
        buf = await asyncio.to_thread(generate_xray_image, ticker, period="6mo", radar_scores=radar_scores, fibo_levels=fibo_levels)
        
        if buf:
            caption = f"🩻 *NEXUS X-RAY: {ticker}* 🩻\n_All-in-One Deep Dive Analysis_"
            await target_msg.reply_photo(photo=buf, caption=caption, parse_mode='Markdown')
            await waiting_msg.delete()
        else:
             await waiting_msg.edit_text("❌ Gagal membuat X-Ray Infographic.")
             
    except Exception as e:
        logger.error(f"XRay Handler Error: {e}")
        await waiting_msg.edit_text("❌ Error system.")

async def channel_command_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.channel_post or not update.channel_post.text: return
    text = update.channel_post.text
    if not text.startswith('/'): return
    parts = text.split()
    command = parts[0].lower().split('@')[0].replace('/', '')
    args = parts[1:]
    context.args = args
    cmd_map = {
        'start': start, 'harga': harga, 'chart': chart, 'analisa': analisa,
        'news': news, 'predict': predict, 'screener': screener, 'bsjp': bsjp,
        'picks': picks, 'sector': sectors, 'pulse': pulse, 'flow': flow, 
        'buy': buy, 'sell': sell, 'porto': porto, 'fibo': fibo, 'xray': xray
    }
    if command in cmd_map:
        await cmd_map[command](update, context)

# ... (rest of code)

    application.add_handler(CommandHandler('fibo', fibo))
    application.add_handler(CommandHandler('xray', xray)) # NEW
    
    # Portfolio Handlers
    application.add_handler(CommandHandler('buy', buy))


# ... (Previous code) ...

async def fibo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Support direct call or callback context override
    args = context.args if hasattr(context, 'args') and context.args else context.args
    
    if not args:
         if update.message:
            await update.message.reply_text("📐 Gunakan format: `/fibo <kode saham>`", parse_mode='Markdown')
         return

    ticker = args[0].upper()
    target_msg = update.message if update.message else update.callback_query.message
    waiting_msg = await target_msg.reply_text(f"📐 *Calculating Golden Ratio {ticker}...*", parse_mode='Markdown')
    
    # 1. Calculate Fibonacci
    fibo_data = await asyncio.to_thread(calculate_fibonacci_levels, ticker, period="6mo")
    
    if not fibo_data:
        await waiting_msg.edit_text(f"❌ *Fibonacci Error*.\nData tidak cukup untuk menentukan Swing High/Low.", parse_mode='Markdown')
        return

    # 2. Generate Chart with Fibo Lines
    buf = await asyncio.to_thread(generate_chart, ticker, period="6mo", fibo_levels=fibo_data['levels'])
    
    if buf:
        # Format Analysis Text
        levels = fibo_data['levels']
        current = fibo_data['current']
        
        # Determine closest support/resistance
        closest_sup = 0
        closest_res = 999999
        
        for k, v in levels.items():
            if v < current and v > closest_sup: closest_sup = v
            if v > current and v < closest_res: closest_res = v
            
        trend_icon = "📈" if fibo_data['trend'] == "UP" else "📉"
        
        caption = (
            f"📐 *NEXUS AUTO-FIBONACCI* 📐\n"
            f"🎯 *{ticker}* (6-Month Swing)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏷️ *Price*: {current:,.0f} {trend_icon}\n"
            f"🏔️ *Swing High*: {fibo_data['high']:,.0f}\n"
            f"🌊 *Swing Low*: {fibo_data['low']:,.0f}\n\n"
            f"🔑 *KEY LEVELS (Golden Ratio)*:\n"
            f"• 0.000: {levels['Fib 0.000']:,.0f}\n"
            f"• 0.236: {levels['Fib 0.236']:,.0f}\n"
            f"• 0.382: {levels['Fib 0.382']:,.0f}\n"
            f"• 0.500: {levels['Fib 0.500']:,.0f} (Mid)\n"
            f"• 0.618: {levels['Fib 0.618']:,.0f} ⭐\n"
            f"• 0.786: {levels['Fib 0.786']:,.0f}\n"
            f"• 1.000: {levels['Fib 1.000']:,.0f}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 *INSIGHT*:\n"
            f"Support Terdekat: {closest_sup:,.0f}\n"
            f"Resistance Terdekat: {closest_res:,.0f}\n"
            f"_Golden Ratio 0.618 adalah area pantulan terkuat._"
        )
        
        await target_msg.reply_photo(photo=buf, caption=caption, parse_mode='Markdown')
        await waiting_msg.delete()
    else:
        await waiting_msg.edit_text("❌ Gagal membuat chart Fibonacci.", parse_mode='Markdown')

async def channel_command_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.channel_post or not update.channel_post.text: return
    text = update.channel_post.text
    if not text.startswith('/'): return
    parts = text.split()
    command = parts[0].lower().split('@')[0].replace('/', '')
    args = parts[1:]
    context.args = args
    cmd_map = {
        'start': start, 'harga': harga, 'chart': chart, 'analisa': analisa,
        'news': news, 'predict': predict, 'screener': screener, 'bsjp': bsjp,
        'picks': picks, 'sector': sectors, 'pulse': pulse, 'flow': flow, 
        'buy': buy, 'sell': sell, 'porto': porto, 'fibo': fibo
    }
    if command in cmd_map:
        await cmd_map[command](update, context)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Configuration ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8446598251:AAE7EnK-1qwtr4hVLJF5TotPvcqYqB4jiCw")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "@nexuspump")

# Global Instances
monitor = StockMonitor()
portfolio_db = PortfolioManager()

# --- Helpers ---

def get_common_keyboard(ticker):
    """
    Returns the standard Navigation Keyboard for a ticker.
    Includes Timeframe Buttons for Chart.
    """
    keyboard = [
        [
            InlineKeyboardButton("1W", callback_data=f"CHART:{ticker}:1wk"),
            InlineKeyboardButton("1M", callback_data=f"CHART:{ticker}:1mo"),
            InlineKeyboardButton("3M", callback_data=f"CHART:{ticker}:3mo"),
            InlineKeyboardButton("1Y", callback_data=f"CHART:{ticker}:1y"),
        ],
        [
            InlineKeyboardButton("📊 Chart Default", callback_data=f"CHART:{ticker}:1mo"),
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
        "👋 *Halo, Boss {user}!*\n"
        "👑 *NEXUS GOD MODE: ENABLED* ⚡\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Saya bukan sekadar bot. Saya adalah *Investment Intelligence System* tercanggih untuk Anda.\n"
        "Gunakan tools premium di bawah ini:\n\n"
        "🩺 *MARKET PULSE*\n"
        "• `/pulse`    : Indikator Fear & Greed Market.\n"
        "• `/flow`     : Radar 'Bandar Flow' & Whale Accumulation.\n"
        "• `/screener` : Scanner Saham Potensial (Top Picks).\n"
        "• `/sectors`  : Peta Rotasi Sektor (Flow of Funds).\n"
        "• `/picks`    : Top 5 Saham Pilihan Besok (Prime Watchlist).\n"
        "• `/bsjp`     : Sinyal Beli Sore Jual Pagi (Scalping Mode).\n\n"
        "💼 *PORTFOLIO MANAGER* 🆕\n"
        "• `/buy`      : Catat Pembelian (`/buy BBCA 9000 10`).\n"
        "• `/sell`     : Catat Penjualan.\n"
        "• `/porto`    : Cek Valuasi & Floating PnL.\n\n"
        "🧠 *DEEP INTELLIGENCE*\n"
        "• `/analisa <kode>` : AI Professional Analysis (Multi-Timeframe).\n"
        "• `/predict <kode>` : Future Projection (Scenario Mapping).\n"
        "• `/fibo <kode>`    : Auto-Fibonacci Golden Ratio 📐\n"
        "• `/chart <kode>`   : Ultimate Neon Chart (30 Days Focus).\n"
        "• `/xray <kode>`    : Infografis Deep Dive (Chart + Radar + Stats) 🩻\n"
        "• `/harga <kode>`   : Info Harga Live & Fundamental.\n\n"
        "ℹ️ *QUICK INFO*\n"
        "• `/gainers` : Top 5 Saham Paling Untung.\n"
        "• `/losers`  : Top 5 Saham Paling Boncos.\n"
        "• `/news <kode>` : Berita Terkini & Sentimen.\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 _Level Anda: VIP User (God Mode)_"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

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
    
    waiting_msg = await message_source.reply_text(f"⏳ *Accessing Exchange Data {ticker}...*", parse_mode='Markdown')
    
    msg_id = waiting_msg.message_id
    chat_id = waiting_msg.chat_id
    
    # Simple Animation Logic
    try:
        await asyncio.to_thread(asyncio.sleep, 0.5) 
        # Optional: Edit message to show progress
        if hasattr(context.bot, 'edit_message_text'):
             await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"🔍 *Analyzing Fundamentals {ticker}...*", parse_mode='Markdown')
    except: pass

    # Fetch Data Parallel
    # Pricing is fast, Fundamentals (info) is slower
    data = await asyncio.to_thread(get_stock_price, ticker, detailed=True)
    fund = await asyncio.to_thread(get_stock_fundamentals, ticker)
    
    if data:
        emoji = "🚀" if data['change'] >= 0 else "🔻"
        color_indicator = "🟢 BULLISH" if data['change'] >= 0 else "🔴 BEARISH"
        
        # Fundamentals formatting
        pe = "N/A"
        pbv = "N/A"
        roe = "N/A"
        div = "N/A"
        mcap_val = data.get('market_cap', 0)

        if fund:
             pe = f"{fund['pe_ratio']:.2f}x" if fund['pe_ratio'] else "N/A"
             pbv = f"{fund['pbv_ratio']:.2f}x" if fund['pbv_ratio'] else "N/A"
             roe = f"{fund['roe']*100:.2f}%" if fund['roe'] else "N/A"
             div = f"{fund['dividend_yield']*100:.2f}%" if fund['dividend_yield'] else "N/A"
             # Use fundamental mcap if available and valid
             if fund['market_cap'] > 0: mcap_val = fund['market_cap']

        if mcap_val >= 1_000_000_000_000: mcap_str = f"{mcap_val/1_000_000_000_000:.2f} T"
        elif mcap_val >= 1_000_000_000: mcap_str = f"{mcap_val/1_000_000_000:.0f} M"
        else: mcap_str = f"{mcap_val:,.0f}"

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
            f"💎 *INVESTOR VIEW*:\n"
            f"• M.Cap   : Rp {mcap_str}\n"
            f"• PER Ratio  : {pe}\n"
            f"• PBV Ratio  : {pbv}\n"
            f"• ROE        : {roe}\n"
            f"• Div Yield  : {div}\n"
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
    period = args[1] if len(args) > 1 else "1mo"
    
    # Reply target
    target_msg = update.message if update.message else update.callback_query.message
    status_msg = await target_msg.reply_text(f"🎨 *Menggambar Chart {ticker}...*", parse_mode='Markdown')
    
    # Get Pivot Points for S/R Lines
    # We use analyze_stock (reusing logic is smart)
    # But analyze_stock is heavy (AI scoring etc).
    # Let's assume we want S/R. analyze_stock returns 'pivot_points': {'S1':.., 'R1':..}
    # It might be slightly slower but gives consistent levels with /analisa.
    
    analysis = await asyncio.to_thread(analyze_stock, ticker)
    levels = []
    if analysis and 'pivot_points' in analysis:
        p = analysis['pivot_points']
        levels = [p['S1'], p['S2'], p['R1'], p['R2']]
        # Filter out 0 or None
        levels = [l for l in levels if l and l > 0]
    
    img_buf = await asyncio.to_thread(generate_chart, ticker, period, levels)
    
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
                "• ⚪ Putus-Putus: Support & Resistance\n"
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
    waiting_msg = await target_msg.reply_text(f"🔮 Mengkalkulasi proyeksi masa depan *{ticker}*...", parse_mode='Markdown')
    
    # 1. Calculate Prediction (Async)
    data = await asyncio.to_thread(predict_future_price, ticker)
    
    if not data:
        await waiting_msg.edit_text(f"⚠️ Maaf, data {ticker} tidak cukup untuk prediksi AI.", parse_mode='Markdown')
        return
        
    # 2. Generate Card (Async)
    buf = await asyncio.to_thread(generate_prediction_card, data)
    
    # 3. Construct Caption
    time_str = datetime.datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%H:%M')
    
    caption = (
        f"🔮 *NEXUS FUTURE SIGHT: {ticker}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 *TARGET PRICE*: Rp {data['target']:,.0f}\n"
        f"⏳ *TIMEFRAME*: 7 Days (Short Term)\n\n"
        f"🛠️ *ANALYSIS LOGIC*\n"
        f"• **Bias**: {data['bias']}\n"
        f"• **Driver**: {data['reason']}\n"
        f"• **Momentum**: RSI {data['rsi']:.1f}\n"
        f"• **Confidence**: {data['confidence']}%\n\n"
        f"⏰ *Generated*: {time_str} WIB\n"
        f"💡 _Disclaimer: Prediction based on Linear Regression & Momentum Algorithm._"
    )
    
    # 4. Send Result
    kb = get_common_keyboard(ticker)
    
    if buf:
        await target_msg.reply_photo(photo=buf, caption=caption, parse_mode='Markdown', reply_markup=kb)
        await waiting_msg.delete()
    else:
        await waiting_msg.edit_text(caption, parse_mode='Markdown', reply_markup=kb)

async def pulse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_msg = update.message if update.message else update.callback_query.message
    status_msg = await target_msg.reply_text("🩺 *Mendiagnosa Market Mood (Big Caps)...*", parse_mode='Markdown')
    
    score, desc = calculate_market_mood()
    img_buf = generate_gauge_chart(score)
    
    if img_buf:
        time_str = datetime.datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%H:%M')
        await status_msg.delete()
        await target_msg.reply_photo(
            photo=img_buf,
            caption=(
                f"🩺 *NEXUS MARKET PULSE*\n"
                f"⏰ {time_str} WIB\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                f"{desc}\n"
                "━━━━━━━━━━━━━━━━━━━━━━\n"
                "💡 _Indeks ini mengukur psikologi pasar berdasarkan Tren & Breadth saham Big Caps._"
            ),
            parse_mode='Markdown'
        )
    else:
        await status_msg.edit_text("❌ Gagal membuat visualisasi Market Pulse.")

async def flow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_msg = update.message if update.message else update.callback_query.message
    waiting = await target_msg.reply_text("🐳 *Scanning Whale Flow (Bandarmology)...*", parse_mode='Markdown')
    
    results = scan_whale_flow(IDX_WATCHLIST)
    
    if not results:
        await waiting.edit_text("🤷‍♂️ *Market Sepi*. Tidak ada aktivitas Whale/Bandar yang mencolok saat ini.", parse_mode='Markdown')
        return
        
    msg = "🕵️‍♂️ *NEXUS FLOW (WHALE RADAR)*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    count = 0
    for r in results[:10]:
        ticker = r['ticker']
        sig = r['signal']
        vol = r['vol_ratio']
        chg = r['change']
        
        # Icon logic
        icon = "🤫" if "SILENT" in sig else "🐳"
        
        msg += (
            f"{icon} *{ticker}* ({chg:+.1f}%)\n"
            f"   📊 Volume: {vol:.1f}x Avg\n"
            f"   🚨 *{sig}*\n"
            f"   _{r['desc']}_\n\n"
        )
        count += 1
        
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n💡 _Radar mendeteksi anomali volume dan aktivitas Smart Money._"
    await waiting.edit_text(msg, parse_mode='Markdown')

async def sectors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_msg = update.message if update.message else update.callback_query.message
    waiting = await target_msg.reply_text("⏳ *Initializing Radar...*", parse_mode='Markdown')
    
    msg_id = waiting.message_id
    chat_id = waiting.chat_id
    try:
         await asyncio.sleep(0.5)
         if hasattr(context.bot, 'edit_message_text'):
             await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text="🗺️ *Scanning Sector Map...*", parse_mode='Markdown')
    except: pass

    try:
        data = await asyncio.wait_for(
            asyncio.to_thread(scan_sector_performance),
            timeout=60.0
        )
    except asyncio.TimeoutError:
        await waiting.edit_text("⚠️ *Timeout*. Server sibuk (Data Sector berat).")
        return
    except Exception as e:
        logger.error(f"Sectors error: {e}")
        await waiting.edit_text("❌ Gagal scan sektor.")
        return
        
    if not data:
        await waiting.edit_text("❌ Data Sektor tidak tersedia.")
        return
        
    time_str = datetime.datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%H:%M')
    msg = f"🗺️ *NEXUS SECTOR RADAR*\n⏰ {time_str} WIB\n━━━━━━━━━━━━━━━━━━━━━━\n"
    
    for d in data:
        sector_name = d['sector']
        avg = d['avg_change']
        stats = d['stats']
        top = d['top_stock']
        top_chg = d['top_change']
        msg += (
            f"{stats} *{sector_name}* ({avg:+.1f}%)\n"
            f"   🏆 Lead: {top} ({top_chg:+.1f}%)\n\n"
        )
        
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n💡 _Rotasi sektor menunjukkan arus uang Smart Money._"
    await waiting.edit_text(msg, parse_mode='Markdown')

# --- PORTFOLIO HANDLERS ---

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args if hasattr(context, 'args') and context.args else context.args
    # /buy BBCA 9500 10
    if not args or len(args) < 3:
        if update.message: await update.message.reply_text("⛔ Format: `/buy <kode> <harga> <lot>`\nContoh: `/buy BBCA 9500 10`", parse_mode='Markdown')
        return
    
    try:
        ticker = args[0].upper()
        price = int(args[1])
        lots = int(args[2])
        
        user_id = update.effective_user.id
        new_pos = portfolio_db.buy_stock(user_id, ticker, price, lots)
        
        avg = new_pos['avg_price']
        tot = new_pos['lots']
        
        msg = (
            f"✅ *BUY RECORDED: {ticker}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💵 Price : {price}\n"
            f"📦 Lots  : {lots}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 *New Position*:\n"
            f"Avg Price: {avg:,.0f}\n"
            f"Total Lot: {tot}"
        )
        if update.message: await update.message.reply_text(msg, parse_mode='Markdown')
        
    except ValueError:
        if update.message: await update.message.reply_text("❌ Error: Harga/Lot harus angka.", parse_mode='Markdown')

async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args if hasattr(context, 'args') and context.args else context.args
    # /sell BBCA 9600 5
    if not args or len(args) < 3:
        if update.message: await update.message.reply_text("⛔ Format: `/sell <kode> <harga> <lot>`\nContoh: `/sell BBCA 9600 5`", parse_mode='Markdown')
        return

    try:
        ticker = args[0].upper()
        price = int(args[1])
        lots = int(args[2])
        user_id = update.effective_user.id
        
        # Calculate PnL Preview (Need current Avg)
        holdings = portfolio_db.get_portfolio(user_id)
        avg_price = 0
        if holdings and ticker in holdings:
            avg_price = holdings[ticker]['avg_price']
        
        res = portfolio_db.sell_stock(user_id, ticker, lots)
        
        if res == -1:
            await update.message.reply_text(f"❌ Anda tidak punya saham *{ticker}*.", parse_mode='Markdown')
        elif res == -2:
             await update.message.reply_text(f"❌ Lot tidak cukup. Cek `/porto`.", parse_mode='Markdown')
        else:
            # PnL Calc
            pnl = (price - avg_price) * lots * 100
            pnl_pct = ((price - avg_price) / avg_price * 100) if avg_price > 0 else 0
            icon = "🟢" if pnl >= 0 else "🔴"
            
            msg = (
                f"✅ *SELL SUCCESS: {ticker}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"💵 Sell Price: {price:,.0f}\n"
                f"📦 Sold Lots : {lots}\n"
                f"{icon} Realized PnL: *{pnl_pct:+.1f}%* (Rp {pnl:,.0f})\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Sisa Lot: {res}"
            )
            await update.message.reply_text(msg, parse_mode='Markdown')
            
    except ValueError:
        await update.message.reply_text("❌ Error: Harga/Lot harus angka.", parse_mode='Markdown')

async def porto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_msg = update.message if update.message else update.callback_query.message
    waiting = await target_msg.reply_text("💼 *Calculating Portfolio Valuation...*", parse_mode='Markdown')
    
    user_id = update.effective_user.id
    holdings = portfolio_db.get_portfolio(user_id)
    
    if not holdings:
        await waiting.edit_text("💼 *Portfolio Kosong*.\nGunakan `/buy` untuk mulai mencatat.", parse_mode='Markdown')
        return

    tickers = list(holdings.keys())
    
    total_val = 0
    total_cost = 0
    lines = []
    
    # Prepare data for Pie Chart
    pie_data = {}
    
    for t, data in holdings.items():
        # Get Price
        p_data = get_stock_price(t) # Live price
        curr_price = p_data['price'] if p_data else data['avg_price']
        
        lots = data['lots']
        avg = data['avg_price']
        
        mkt_val = curr_price * lots * 100
        cost_val = avg * lots * 100
        pnl = mkt_val - cost_val
        pnl_pct = ((curr_price - avg) / avg) * 100
        
        total_val += mkt_val
        total_cost += cost_val
        
        pie_data[t] = {'current_value': mkt_val}
        
        icon = "🟢" if pnl >= 0 else "🔴"
        lines.append(
            f"{icon} *{t}* ({lots} Lot)\n"
            f"   💵 Avg: {avg:,.0f} | Curr: {curr_price:,.0f}\n"
            f"   📈 PnL: *{pnl_pct:+.2f}%* (Rp {pnl:,.0f})"
        )
        
    pnl_total = total_val - total_cost
    pnl_total_pct = ((total_val - total_cost) / total_cost * 100) if total_cost > 0 else 0
    
    header = (
        "💼 *NEXUS PORTFOLIO SUMMARY*\n"
        f"💰 *Total Asset: Rp {total_val:,.0f}*\n"
        f"💸 Floating PnL: *{pnl_total_pct:+.2f}%* (Rp {pnl_total:,.0f})\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    
    msg = header + "\n\n".join(lines)
    
    # Generate Pie Chart
    try:
        pie_buf = await asyncio.to_thread(generate_portfolio_pie, pie_data, total_val)
        if pie_buf:
            await waiting.delete()
            await target_msg.reply_photo(
                photo=pie_buf,
                caption=msg,
                parse_mode='Markdown'
            )
        else:
             await waiting.edit_text(msg, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error sending portfolio pie: {e}")
        await waiting.edit_text(msg, parse_mode='Markdown')    

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
    
    # Handle Chart Period if present
    if cmd == "CHART" and len(data) > 2:
        period = data[2]
        context.args.append(period)

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
    
    # Async Fix: Run blocking IO in thread pool with Timeout
    try:
        g, _ = await asyncio.wait_for(
            asyncio.to_thread(get_top_gainers_losers_idx),
            timeout=25.0
        )
    except asyncio.TimeoutError:
        logger.error("Gainers scan timed out.")
        await waiting.edit_text("⚠️ *Timeout*. Server sibuk. Coba lagi dalam 1 menit.")
        return
    except Exception as e:
        logger.error(f"Gainers error: {e}")
        await waiting.edit_text("❌ Terjadi kesalahan saat mengambil data.")
        return

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
    await waiting.edit_text(msg, parse_mode='Markdown')

async def losers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_msg = update.message if update.message else update.callback_query.message
    waiting = await target_msg.reply_text("🔎 *Scanning Top Losers...*", parse_mode='Markdown')
    
    # Async Fix with Timeout
    try:
        _, l = await asyncio.wait_for(
            asyncio.to_thread(get_top_gainers_losers_idx),
            timeout=25.0
        )
    except asyncio.TimeoutError:
        logger.error("Losers scan timed out.")
        await waiting.edit_text("⚠️ *Timeout*. Server sibuk. Coba lagi dalam 1 menit.")
        return
    except Exception as e:
        logger.error(f"Losers error: {e}")
        await waiting.edit_text("❌ Terjadi kesalahan saat mengambil data.")
        return

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
    waiting = await target_msg.reply_text("⏳ *Scanning Market Data...*", parse_mode='Markdown')

    msg_id = waiting.message_id
    chat_id = waiting.chat_id
    try:
         await asyncio.sleep(0.5)
         if hasattr(context.bot, 'edit_message_text'):
             await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text="🕵️‍♂️ *Filtering Top Potential...*", parse_mode='Markdown')
    except: pass
    
    results = await asyncio.to_thread(scan_market_screener, IDX_WATCHLIST)
    
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
    waiting = await target_msg.reply_text("🦅 *NEXUS SNIPER: Scanning & Backtesting...*", parse_mode='Markdown')
    
    # Increase timeout for Backtest (45 stocks * fetch)
    try:
        candidates = await asyncio.wait_for(
            asyncio.to_thread(scan_bsjp_strategy, IDX_WATCHLIST),
            timeout=120.0
        )
    except asyncio.TimeoutError:
         await waiting.edit_text("⚠️ *Timeout*. Market Scan terlalu lama. Coba lagi nanti.")
         return
         
    time_str = datetime.datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%H:%M')
    
    if not candidates:
        await waiting.edit_text(f"❌ *NO TARGET FOUND*.\nMarket terlalu lemah untuk Sniper Entry.\n⏰ Checked: {time_str} WIB", parse_mode='Markdown')
        return
        
    msg = f"🦅 *NEXUS SNIPER PRO (BSJP)*\n⏰ Pukul: {time_str} WIB\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for c in candidates[:10]: 
        # Visualization of Win Prob
        win_prob = c.get('win_prob', 0)
        trades = c.get('trades', 0)
        avg_gain = c.get('avg_gain', 0)
        vol_ratio = c.get('vol_ratio', 0)
        
        icon = "🎯" if win_prob >= 75 else "🎲"
        
        # Format Backtest Stats
        if trades > 0:
            stats_str = f"Win Rate: *{win_prob:.1f}%* ({trades} Trades)"
        else:
            stats_str = "Win Rate: *Unknown* (Not enough data)"
            
        msg += (
            f"{icon} *{c['ticker']}* @ {c['price']:,.0f}\n"
            f"   📈 Gain: +{c['change']:.1f}% | 🎲 {stats_str}\n"
            f"   🔊 Vol Ratio: {vol_ratio:.1f}x | Avg Scalp: +{avg_gain:.1f}%\n\n"
        )
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n⚠️ _Win Rate based on 6 Months Backtest._"
    await waiting.edit_text(msg, parse_mode='Markdown')

async def picks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_msg = update.message if update.message else update.callback_query.message
    waiting = await target_msg.reply_text("🔭 *Scanning Nexus Prime Watchlist (Tomorrow)...*", parse_mode='Markdown')
    
    try:
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

# ... Session reporters ...
# ... Session reporters ...
async def session_open(context: ContextTypes.DEFAULT_TYPE):
    reporter = MarketSessionReporter(context.application, channel_id=CHANNEL_ID)
    await reporter.send_report(context, 'open')
async def session_mid(context: ContextTypes.DEFAULT_TYPE):
    reporter = MarketSessionReporter(context.application, channel_id=CHANNEL_ID)
    await reporter.send_report(context, 'mid')
async def session_open2(context: ContextTypes.DEFAULT_TYPE):
    reporter = MarketSessionReporter(context.application, channel_id=CHANNEL_ID)
    await reporter.send_report(context, 'open2')
async def session_close(context: ContextTypes.DEFAULT_TYPE):
    reporter = MarketSessionReporter(context.application, channel_id=CHANNEL_ID)
    await reporter.send_report(context, 'close')
    
async def channel_command_dispatcher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.channel_post or not update.channel_post.text: return
    text = update.channel_post.text
    if not text.startswith('/'): return
    parts = text.split()
    command = parts[0].lower().split('@')[0].replace('/', '')
    args = parts[1:]
    context.args = args
    cmd_map = {
        'start': start, 'harga': harga, 'chart': chart, 'analisa': analisa,
        'news': news, 'predict': predict, 'screener': screener, 'bsjp': bsjp,
        'gainers': gainers, 'losers': losers, 'pulse': pulse, 'flow': flow,
        'picks': picks, 'rekomendasi': picks, 'sectors': sectors,
        'buy': buy, 'sell': sell, 'porto': porto, 'portfolio': porto,
        'fibo': fibo, 'xray': xray
    }
    if command in cmd_map:
        await cmd_map[command](update, context)

async def post_init(application):
    """
    Set up the bot's command menu automatically on startup.
    """
    from telegram import BotCommand
    commands = [
        BotCommand("start", "Main Menu & Dashboard"),
        BotCommand("harga", "Cek Harga & Fundamental"),
        BotCommand("chart", "Lihat Chart Teknikal"),
        BotCommand("analisa", "Analisis AI Lengkap"),
        BotCommand("predict", "Proyeksi Harga Masa Depan"),
        BotCommand("predict", "Proyeksi Harga Masa Depan"),
        BotCommand("fibo", "Auto-Fibonacci Golden Ratio"),
        BotCommand("xray", "Nexus X-Ray Infographic"),
        BotCommand("news", "Berita Saham Terkini"),
        BotCommand("screener", "Market Screener (Potensial)"),
        BotCommand("bsjp", "Sinyal Beli Sore Jual Pagi"),
        BotCommand("picks", "Rekomendasi Besok (Prime Picks)"),
        BotCommand("sectors", "Peta Rotasi Sektor"),
        BotCommand("pulse", "Market Fear & Greed"),
        BotCommand("flow", "Bandar Volume Flow"),
        BotCommand("gainers", "Top Gainers Hari Ini"),
        BotCommand("losers", "Top Losers Hari Ini"),
        BotCommand("porto", "Cek Portofolio"),
        BotCommand("buy", "Catat Pembelian"),
        BotCommand("sell", "Catat Penjualan"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Bot commands set successfully.")

if __name__ == '__main__':
    if TOKEN == "YOUR_TELEGRAM_BOT_TOKEN":
        print("Set ENV 'TELEGRAM_BOT_TOKEN' first!")
        
    application = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    
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
    application.add_handler(CommandHandler('pulse', pulse))
    application.add_handler(CommandHandler('flow', flow))
    application.add_handler(CommandHandler('picks', picks))
    application.add_handler(CommandHandler('sectors', sectors))
    application.add_handler(CommandHandler('rekomendasi', picks))
    
    application.add_handler(CommandHandler('fibo', fibo)) 
    application.add_handler(CommandHandler('xray', xray)) # FIX: Register XRAY Handler
    
    # Portfolio Handlers
    application.add_handler(CommandHandler('buy', buy))
    application.add_handler(CommandHandler('sell', sell))
    application.add_handler(CommandHandler('porto', porto))
    application.add_handler(CommandHandler('portfolio', porto))
    
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
    
    print("--- NEXUS PUMP BOT V19-V26 STARTING ---")
    application.run_polling()
