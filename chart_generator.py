import matplotlib
matplotlib.use('Agg') # Force non-interactive backend
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
    Fetches '1y' data regardless of requested period to ensure valid MA50/MA200, 
    then slices for display.
    """
    try:
        # 1. Fetch SUFFICIENT Data (Always 1y minimum for MA200)
        df_full = get_historical_data(ticker, period="1y")
        if df_full.empty or len(df_full) < 50:
            logger.warning(f"Insufficient data for {ticker}")
            return None
            
        # 2. Technical Calculations (On Full Data)
        close = df_full['Close']
        
        # MAs
        df_full['MA20'] = close.rolling(window=20).mean()
        df_full['MA50'] = close.rolling(window=50).mean()
        df_full['MA100'] = close.rolling(window=100).mean()
        
        # RSI
        df_full['rsi'] = ta.momentum.RSIIndicator(close, window=14).rsi()
        
        # MACD
        macd = ta.trend.MACD(close)
        df_full['macd'] = macd.macd()
        df_full['macd_signal'] = macd.macd_signal()
        df_full['macd_hist'] = macd.macd_diff()
        
        # 3. Slice Data for Display
        # Determine slice length based on requested period
        slice_map = {
            "1mo": 25,   # ~1 Month trading days
            "3mo": 65,   # ~3 Months
            "6mo": 130,  # ~6 Months
            "1y": 250    # ~1 Year
        }
        lookback = slice_map.get(period, 25) # Default 1mo
        
        if len(df_full) > lookback:
            df_plot = df_full.tail(lookback).copy()
        else:
            df_plot = df_full.copy()
            
        # 4. Prepare AddPlots (Using SLICED Data)
        # We must recalculate addplots based on the sliced dataframe columns ??
        # No, we just use the columns we added to df_full, which are now in df_plot
        
        # Check if we have enough valid data in the slice (avoid all-NaN plot crash)
        # But even if MA200 is NaN in the displayed region, mpf should handle it if other data exists.
        # However, to be safe, fillna? No, gaps are better.
        
        addplots = [
             # MA Lines
            mpf.make_addplot(df_plot['MA20'], color='#00f2ff', width=1.5, panel=0), # Cyan
            mpf.make_addplot(df_plot['MA50'], color='#ff9100', width=1.5, panel=0), # Orange
            # Only plot MA100 if it has values in the slice
            # mpf.make_addplot(df_plot['MA100'], color='#ffffff', width=1, panel=0),
            
            # RSI
            mpf.make_addplot(df_plot['rsi'], panel=2, color='#b026ff', ylabel='RSI', width=1.5),
            mpf.make_addplot([70]*len(df_plot), panel=2, color='#ff0055', linestyle='--', width=0.8),
            mpf.make_addplot([30]*len(df_plot), panel=2, color='#00ff44', linestyle='--', width=0.8),
            
            # MACD
            mpf.make_addplot(df_plot['macd'], panel=3, color='#00f2ff', ylabel='MACD', width=1),
            mpf.make_addplot(df_plot['macd_signal'], panel=3, color='#ff9100', width=1),
            mpf.make_addplot(df_plot['macd_hist'], panel=3, type='bar', color='#444444', alpha=0.6),
        ]
        
        # 5. Visual Styling
        mc = mpf.make_marketcolors(
            up='#00ff44', down='#ff0055', 
            edge='inherit', wick='inherit', 
            volume={'up': '#00ff44', 'down': '#ff0055'},
            ohlc='inherit'
        )
        s = mpf.make_mpf_style(
            base_mpf_style='nightclouds', 
            marketcolors=mc,
            gridstyle=':', gridcolor='#2a2a2a',
            y_on_right=True,
            rc={'font.size': 10, 'figure.facecolor': '#0a0a0a', 'axes.facecolor': '#0a0a0a', 
                'text.color': '#e0e0e0', 'axes.labelcolor': '#e0e0e0', 'xtick.color': '#808080', 'ytick.color': '#808080'}
        )
        
        buf = io.BytesIO()
        
        mpf.plot(
            df_plot,
            type='candle',
            volume=True,
            addplot=addplots,
            title=dict(title=f"\n{ticker} - {period.upper()} (NEXUS AI)", color='#ffffff', fontsize=14),
            style=s,
            panel_ratios=(4, 1, 1, 1), 
            datetime_format='%d-%b',
            tight_layout=True,
            scale_width_adjustment=dict(volume=0.7, candle=1.2),
            savefig=dict(fname=buf, dpi=120, bbox_inches='tight', facecolor='#0a0a0a')
        )
        
        buf.seek(0)
        return buf
        
    except Exception as e:
        logger.error(f"Error generating chart for {ticker}: {e}")
        return None
