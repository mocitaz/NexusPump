import mplfinance as mpf
import pandas as pd
import io
import logging
import ta
from data_fetcher import get_historical_data

logger = logging.getLogger(__name__)

def generate_chart(ticker, period="3mo"):
    """
    Generates a premium Dark Mode candlestick chart with MA, RSI, and MACD.
    """
    try:
        # Fetch data
        df = get_historical_data(ticker, period=period)
        if df.empty or len(df) < 20:
            return None
            
        # --- Technical Calculations for Charting ---
        # RSI
        df['rsi'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        
        # MACD
        macd = ta.trend.MACD(df['Close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_hist'] = macd.macd_diff()
        
        # --- Create Subplots (Addplots) ---
        addplots = [
            # MA 20 & 50 on main chart
            mpf.make_addplot(df['Close'].rolling(window=20).mean(), color='cyan', width=1, panel=0),
            mpf.make_addplot(df['Close'].rolling(window=50).mean(), color='orange', width=1, panel=0),
            
            # RSI on panel 2 (Panel 1 is Volume)
            mpf.make_addplot(df['rsi'], panel=2, color='lime', ylabel='RSI', width=1.5),
            mpf.make_addplot([70]*len(df), panel=2, color='red', linestyle='--', width=0.8), # Overbought
            mpf.make_addplot([30]*len(df), panel=2, color='green', linestyle='--', width=0.8), # Oversold
            
            # MACD on panel 3
            mpf.make_addplot(df['macd'], panel=3, color='cyan', ylabel='MACD', width=1),
            mpf.make_addplot(df['macd_signal'], panel=3, color='orange', width=1),
            mpf.make_addplot(df['macd_hist'], panel=3, type='bar', color='dimgray', alpha=0.5),
        ]
        
        # --- Visual Styling (Premium Dark) ---
        # Custom style based on nightclouds but tweaked
        mc = mpf.make_marketcolors(
            up='#00ff00', down='#ff0000', 
            edge='inherit', 
            wick='inherit', 
            volume={'up': '#00ff00', 'down': '#ff0000'},
            ohlc='inherit'
        )
        s = mpf.make_mpf_style(
            base_mpf_style='nightclouds', 
            marketcolors=mc,
            gridstyle=':', 
            y_on_right=True,
            rc={'font.size': 10, 'figure.facecolor': '#0e1117'}
        )
        
        # Save to buffer
        buf = io.BytesIO()
        
        mpf.plot(
            df,
            type='candle',
            volume=True,
            addplot=addplots,
            title=f"\n{ticker} - {period} (IDX BOT)",
            style=s,
            panel_ratios=(4, 1, 1, 1), # Main, Vol, RSI, MACD
            datetime_format='%b %d',
            tight_layout=True,
            scale_width_adjustment=dict(volume=0.7, candle=1.2),
            savefig=dict(fname=buf, dpi=120, bbox_inches='tight', facecolor='#0e1117')
        )
        
        buf.seek(0)
        return buf
    except Exception as e:
        logger.error(f"Error generating chart for {ticker}: {e}")
        return None
