import mplfinance as mpf
import pandas as pd
import io
import logging
import ta
from data_fetcher import get_historical_data

logger = logging.getLogger(__name__)

def generate_chart(ticker, period="1mo"):
    """
    Generates a premium Dark Mode candlestick chart with MA, RSI, and MACD.
    Default period is '1mo' for zoomed-in precision (30 days).
    """
    try:
        # Fetch data
        df = get_historical_data(ticker, period=period)
        if df.empty or len(df) < 5: # Allow shorter data for 30 days
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
            # MA 20 & 50 on main chart (Neon Colors)
            mpf.make_addplot(df['Close'].rolling(window=20).mean(), color='#00f2ff', width=1.2, panel=0), # Neon Cyan
            mpf.make_addplot(df['Close'].rolling(window=50).mean(), color='#ff9100', width=1.2, panel=0), # Neon Orange
            
            # RSI on panel 2
            mpf.make_addplot(df['rsi'], panel=2, color='#b026ff', ylabel='RSI', width=1.5), # Neon Purple
            mpf.make_addplot([70]*len(df), panel=2, color='#ff0055', linestyle='--', width=0.8), # Overbought Red
            mpf.make_addplot([30]*len(df), panel=2, color='#00ff44', linestyle='--', width=0.8), # Oversold Green
            
            # MACD on panel 3
            mpf.make_addplot(df['macd'], panel=3, color='#00f2ff', ylabel='MACD', width=1),
            mpf.make_addplot(df['macd_signal'], panel=3, color='#ff9100', width=1),
            mpf.make_addplot(df['macd_hist'], panel=3, type='bar', color='#444444', alpha=0.6),
        ]
        
        # --- Visual Styling (Premium Cyber Dark) ---
        mc = mpf.make_marketcolors(
            up='#00ff44', down='#ff0055', # Bright Green/Red
            edge='inherit', 
            wick='inherit', 
            volume={'up': '#00ff44', 'down': '#ff0055'},
            ohlc='inherit'
        )
        
        # Custom Style
        s = mpf.make_mpf_style(
            base_mpf_style='nightclouds', 
            marketcolors=mc,
            gridstyle=':', 
            gridcolor='#2a2a2a',
            y_on_right=True,
            rc={
                'font.size': 11,
                'font.weight': 'bold', 
                'figure.facecolor': '#0a0a0a', # Pitch Black
                'axes.facecolor': '#0a0a0a', 
                'axes.edgecolor': '#333333',
                'text.color': '#e0e0e0',
                'axes.labelcolor': '#e0e0e0',
                'xtick.color': '#808080',
                'ytick.color': '#808080'
            }
        )
        
        # Ensure we have enough data handles
        # If period is 1mo, we just show daily candles nicely spaced.
        
        buf = io.BytesIO()
        
        mpf.plot(
            df,
            type='candle',
            volume=True,
            addplot=addplots,
            title=dict(title=f"\n{ticker} - {period.upper()} (NEXUS AI)", color='#ffffff', fontsize=15),
            style=s,
            panel_ratios=(4, 1, 1, 1), # Main, Vol, RSI, MACD
            datetime_format='%b %d',
            tight_layout=True,
            scale_width_adjustment=dict(volume=0.7, candle=1.1),
            savefig=dict(fname=buf, dpi=150, bbox_inches='tight', facecolor='#0a0a0a') # Higher DPI for sharpness
        )
        
        buf.seek(0)
        return buf
    except Exception as e:
        logger.error(f"Error generating chart for {ticker}: {e}")
        return None
