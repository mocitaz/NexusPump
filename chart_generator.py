import matplotlib
matplotlib.use('Agg') # Force non-interactive backend
import mplfinance as mpf
import pandas as pd
import io
import logging
import ta
from data_fetcher import get_historical_data

logger = logging.getLogger(__name__)

def generate_chart(ticker, period="1mo", sup_res_levels=None):
    """
    Generates a premium Dark Mode candlestick chart with MA, RSI, and MACD.
    sup_res_levels: list of prices [S1, R1, ...] to draw dashed lines.
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
        addplots = [
             # MA Lines
            mpf.make_addplot(df_plot['MA20'], color='#00f2ff', width=1.5, panel=0), # Cyan
            mpf.make_addplot(df_plot['MA50'], color='#ff9100', width=1.5, panel=0), # Orange
            
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
        
        # 6. Prepare Plot Arguments
        buf = io.BytesIO()
        
        plot_kwargs = dict(
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
        
        # Add S/R Lines ONLY if valid
        if sup_res_levels:
            hlines_dict = dict(
                hlines=sup_res_levels, 
                colors=['#ffffff'] * len(sup_res_levels), 
                linestyle='-.', 
                linewidths=0.8
            )
            plot_kwargs['hlines'] = hlines_dict

        mpf.plot(df_plot, **plot_kwargs)
        
        buf.seek(0)
        return buf
        
    except Exception as e:
        logger.error(f"Error generating chart for {ticker}: {e}")
        return None

def generate_portfolio_pie(holdings, total_value, cash_balance=0):
    """
    Generates a dark-themed pie chart for portfolio allocation.
    holdings: dict of {ticker: {'current_value': 12345}}
    total_value: float
    cash_balance: float (optional)
    """
    try:
        import matplotlib.pyplot as plt
        
        # Prepare Data
        labels = []
        sizes = []
        colors = []
        
        # Color Palette (Cyberpunk/Neon)
        palette = ['#00f2ff', '#ff0055', '#b026ff', '#ff9100', '#00ff44', '#ffff00', '#ffffff', '#808080']
        
        # Add Stocks
        i = 0
        for ticker, data in holdings.items():
            val = data.get('current_value', 0)
            if val > 0:
                labels.append(ticker)
                sizes.append(val)
                colors.append(palette[i % len(palette)])
                i += 1
                
        # Add Cash (if any/significant) - Assuming fully invested for now or handled outside
        # If we had cash tracking, we'd add it here.
        
        if not sizes: return None
        
        # Plot
        fig, ax = plt.subplots(figsize=(6, 6), facecolor='#0a0a0a')
        
        wedges, texts, autotexts = ax.pie(
            sizes, 
            labels=labels, 
            autopct='%1.1f%%', 
            startangle=90, 
            colors=colors,
            pctdistance=0.85,
            textprops=dict(color="w")
        )
        
        # Donut Style
        centre_circle = plt.Circle((0,0),0.70,fc='#0a0a0a')
        fig.gca().add_artist(centre_circle)
        
        # Styling
        plt.setp(texts, size=10, weight="bold")
        plt.setp(autotexts, size=9, weight="bold", color="#000000")
        
        # Title
        ax.set_title(f"PORTFOLIO ALLOCATION\nRp {total_value:,.0f}", color='white', pad=20, fontsize=12, fontweight='bold')
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', facecolor='#0a0a0a', bbox_inches='tight', dpi=100)
        plt.close(fig)
        buf.seek(0)
        return buf
        
    except Exception as e:
        logger.error(f"Error generating pie chart: {e}")
        return None
