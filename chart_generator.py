import matplotlib
matplotlib.use('Agg') # Force non-interactive backend
import mplfinance as mpf
import pandas as pd
import io
import logging
import ta
from data_fetcher import get_historical_data

logger = logging.getLogger(__name__)

def generate_chart(ticker, period="1mo", sup_res_levels=None, fibo_levels=None):
    """
    Generates a premium Dark Mode candlestick chart with MA, RSI, and MACD.
    sup_res_levels: list of prices [S1, R1, ...]
    fibo_levels: dict of {'Fib 0.618': 1234, ...}
    """
    try:
        # 1. Fetch SUFFICIENT Data (Always 1y minimum for MA200)
        df_full = get_historical_data(ticker, period="1y")
        if df_full.empty or len(df_full) < 50:
            logger.warning(f"Insufficient data for {ticker}")
            return None
            
        # ... (Calculations remain same) ...
        close = df_full['Close']
        df_full['MA20'] = close.rolling(window=20).mean()
        df_full['MA50'] = close.rolling(window=50).mean()
        df_full['MA100'] = close.rolling(window=100).mean()
        df_full['rsi'] = ta.momentum.RSIIndicator(close, window=14).rsi()
        macd = ta.trend.MACD(close)
        df_full['macd'] = macd.macd()
        df_full['macd_signal'] = macd.macd_signal()
        df_full['macd_hist'] = macd.macd_diff()
        
        # 3. Slice Data for Display
        slice_map = {
            "1mo": 25, "3mo": 65, "6mo": 130, "1y": 250
        }
        lookback = slice_map.get(period, 25)
        
        if len(df_full) > lookback:
            df_plot = df_full.tail(lookback).copy()
        else:
            df_plot = df_full.copy()
            
        # 4. Prepare AddPlots
        addplots = [
            mpf.make_addplot(df_plot['MA20'], color='#00f2ff', width=1.5, panel=0), 
            mpf.make_addplot(df_plot['MA50'], color='#ff9100', width=1.5, panel=0),
            mpf.make_addplot(df_plot['rsi'], panel=2, color='#b026ff', ylabel='RSI', width=1.5),
            mpf.make_addplot([70]*len(df_plot), panel=2, color='#ff0055', linestyle='--', width=0.8),
            mpf.make_addplot([30]*len(df_plot), panel=2, color='#00ff44', linestyle='--', width=0.8),
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
        
        title_text = f"\n{ticker} - {period.upper()} (NEXUS AI)"
        if fibo_levels: title_text += " [FIBO MODE]"
        
        plot_kwargs = dict(
            type='candle',
            volume=True,
            addplot=addplots,
            title=dict(title=title_text, color='#ffffff', fontsize=14),
            style=s,
            panel_ratios=(4, 1, 1, 1), 
            datetime_format='%d-%b',
            tight_layout=True,
            scale_width_adjustment=dict(volume=0.7, candle=1.2),
            savefig=dict(fname=buf, dpi=120, bbox_inches='tight', facecolor='#0a0a0a')
        )
        
        # Combine S/R and Fibo Lines
        combined_hlines = []
        combined_colors = []
        
        if sup_res_levels:
            combined_hlines.extend(sup_res_levels)
            combined_colors.extend(['#ffffff'] * len(sup_res_levels)) # White for SR
            
        if fibo_levels:
            # Sort levels logic? No need, mpf handles list.
            for label, price in fibo_levels.items():
                combined_hlines.append(price)
                
                # Special Colors for Fibo Ratios
                if "0.618" in label: color = '#ffd700' # GOLD
                elif "0.500" in label: color = '#ffffff' # White
                elif "0.382" in label: color = '#00f2ff' # Cyan
                elif "0.236" in label: color = '#ff0055' # Red/Pink
                elif "0.786" in label: color = '#00ff44' # Green
                else: color = '#808080' # Grey for 0 and 1
                
                combined_colors.append(color)
        
        if combined_hlines:
             hlines_dict = dict(
                hlines=combined_hlines, 
                colors=combined_colors, 
                linestyle='-.', 
                linewidths=0.8,
                alpha=0.7
            )
             plot_kwargs['hlines'] = hlines_dict

        mpf.plot(df_plot, **plot_kwargs)
        
        buf.seek(0)
        return buf
        
    except Exception as e:
        logger.error(f"Chart Generation Error {ticker}: {e}")
        return None

def generate_xray_image(ticker, period="6mo", radar_scores=None, fibo_levels=None):
    """
    V32 NEXUS X-RAY: Infographic Generator
    Combines Price Chart, Radar Chart, and Key Stats in one vertical image.
    """
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    import numpy as np
    from data_fetcher import get_historical_data
    
    try:
        # 1. Fetch Data
        df = get_historical_data(ticker, period=period)
        if df.empty: return None
        
        last_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        change_pct = ((last_price - prev_price) / prev_price) * 100
        change_str = f"{change_pct:+.2f}%"
        color_change = "#00ff44" if change_pct >= 0 else "#ff0055"
        
        # 2. Setup Figure (Portrait)
        fig = plt.figure(figsize=(10, 18), facecolor='#0a0a0a')
        gs = gridspec.GridSpec(4, 2, height_ratios=[1, 4, 3, 2])
        
        # --- A. HEADER (Top Full Width) ---
        ax_header = fig.add_subplot(gs[0, :])
        ax_header.set_facecolor('#0a0a0a')
        ax_header.axis('off')
        
        ax_header.text(0.5, 0.7, f"{ticker}", color='white', fontsize=48, 
                       fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax_header.text(0.5, 0.35, f"Rp {last_price:,.0f}", color='white', fontsize=36, 
                       ha='center', va='center')
        ax_header.text(0.5, 0.15, change_str, color=color_change, fontsize=24, 
                       fontweight='bold', ha='center', va='center')
                       
        # --- B. MAIN CHART (Candles) ---
        # Note: mpf is hard to integrate into existing fig as subplot easily without 'returnfig'.
        # We will use mpf with 'external_axes' mode.
        ax_main = fig.add_subplot(gs[1, :])
        ax_vol =  ax_main.twinx() # Virtual axis for volume to not mess up
        # Actually mpf allows passing [ax_main, ax_vol]
        
        # Need to slice df for visual clarity
        df_plot = df.tail(100)
        
        # Custom Style for sub-plot
        mc = mpf.make_marketcolors(up='#00ff44', down='#ff0055', inherit=True)
        s = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc, gridcolor='#2a2a2a')
        
        # Fibo Lines
        hlines = []
        colors = []
        if fibo_levels:
            for k,v in fibo_levels.items():
                hlines.append(v)
                if "0.618" in k: colors.append('#ffd700')
                else: colors.append('#ffffff')
                
        # Plotting
        mpf.plot(df_plot, type='candle', style=s, ax=ax_main, volume=False, 
                 hlines=dict(hlines=hlines, colors=colors, linewidths=0.7, linestyle='-.') if hlines else None)
        
        ax_main.set_title("Price Action & Fibonacci", color='white', fontsize=12)
        ax_main.tick_params(colors='white')
        ax_main.grid(True, color='#222222', linestyle=':')
        
        # --- C. RADAR CHART (Bottom Left) ---
        # Radar Data
        categories = ['Valuation', 'Trend', 'Momentum', 'Volatility', 'Volume']
        if radar_scores:
            values = [radar_scores.get(c, 50) for c in categories]
        else:
            values = [50, 50, 50, 50, 50]
            
        # Close the loop
        values += [values[0]]
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles += [angles[0]]
        
        ax_radar = fig.add_subplot(gs[2, 0], polar=True)
        ax_radar.set_facecolor('#0a0a0a')
        
        # Draw Poly
        ax_radar.plot(angles, values, color='#00f2ff', linewidth=2, linestyle='solid')
        ax_radar.fill(angles, values, color='#00f2ff', alpha=0.3)
        
        # Fix Labels
        ax_radar.set_xticks(angles[:-1])
        ax_radar.set_xticklabels(categories, color='white', fontsize=10)
        ax_radar.set_yticks([20, 40, 60, 80])
        ax_radar.set_yticklabels(['', '', '', ''], color='#555555')
        ax_radar.spines['polar'].set_visible(False)
        ax_radar.set_title("Nexus AI Score", color='white', pad=20)
        
        # --- D. KEY STATS (Bottom Right) ---
        ax_stats = fig.add_subplot(gs[2, 1])
        ax_stats.set_facecolor('#0a0a0a')
        ax_stats.axis('off')
        
        # Text Content
        stats_text = (
            f"📊 PERFORMANCE\n"
            f"━━━━━━━━━━\n"
            f"• Score: {np.mean(values[:-1]):.0f}/100\n"
            f"• Trend: {radar_scores.get('Trend', 0)}\n"
            f"• Vol  : {radar_scores.get('Volume', 0)}\n\n"
            f"💡 INSIGHT\n"
            f"Valuation is {'Cheap' if radar_scores.get('Valuation',0) > 60 else 'Expensive'}.\n"
            f"Momentum is {'Strong' if radar_scores.get('Momentum',0) > 60 else 'Weak'}."
        )
        
        ax_stats.text(0.1, 0.5, stats_text, color='white', fontsize=14, 
                      fontfamily='monospace', va='center')
        
        # --- E. FOOTER ---
        ax_footer = fig.add_subplot(gs[3, :])
        ax_footer.set_facecolor('#0a0a0a')
        ax_footer.axis('off')
        ax_footer.text(0.5, 0.5, "GENERATED BY NEXUS TRADING AI", color='#555555', 
                       fontsize=10, ha='center')
        
        # Save
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, facecolor='#0a0a0a')
        buf.seek(0)
        plt.close(fig)
        return buf
        
    except Exception as e:
        logger.error(f"X-Ray Generation Error {ticker}: {e}")
        return None
        
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
