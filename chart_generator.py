import matplotlib
matplotlib.use('Agg') # Force non-interactive backend
import mplfinance as mpf
import pandas as pd
import io
import logging
import ta
from data_fetcher import get_historical_data

logger = logging.getLogger(__name__)

# Link: Global Helper for Logo
def add_logo(fig, position='top-right'):
    """
    Overlays logo.png on the figure.
    """
    try:
        import matplotlib.image as mpimg
        import os
        logo_path = "logo.png"
        if not os.path.exists(logo_path): return
        img = mpimg.imread(logo_path)
        
        # Create a new axes for the logo
        if position == 'top-right':
            # (left, bottom, width, height)
            ax_logo = fig.add_axes([0.82, 0.82, 0.15, 0.15], anchor='NE', zorder=10)
        elif position == 'top-left':
            ax_logo = fig.add_axes([0.03, 0.82, 0.15, 0.15], anchor='NW', zorder=10)
        elif position == 'xray': # Custom for X-Ray
            ax_logo = fig.add_axes([0.85, 0.90, 0.10, 0.10], anchor='NE', zorder=10)
            
        ax_logo.imshow(img)
        ax_logo.axis('off')
    except Exception as e:
        logger.error(f"Failed to add logo: {e}")


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
            returnfig=True # Enable Figure manipulation
        )
        
        # Combine S/R and Fibo Lines
        combined_hlines = []
        combined_colors = []
        
        if sup_res_levels:
            combined_hlines.extend(sup_res_levels)
            combined_colors.extend(['#ffffff'] * len(sup_res_levels)) # White for SR
            
        if fibo_levels:
            for label, price in fibo_levels.items():
                combined_hlines.append(price)
                if "0.618" in label: color = '#ffd700' # GOLD
                elif "0.500" in label: color = '#ffffff' # White
                elif "0.382" in label: color = '#00f2ff' # Cyan
                elif "0.236" in label: color = '#ff0055' # Red/Pink
                elif "0.786" in label: color = '#00ff44' # Green
                else: color = '#808080' # Grey
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

        # Plot and Get Figure
        fig, axlist = mpf.plot(df_plot, **plot_kwargs)
        
        # Add Logo
        add_logo(fig, 'top-right')
        
        # Save Manually
        fig.savefig(buf, dpi=120, bbox_inches='tight', facecolor='#0a0a0a')
        buf.seek(0)
        return buf
        
    except Exception as e:
        logger.error(f"Chart Generation Error {ticker}: {e}")
        return None

def generate_xray_image(ticker, period="6mo", radar_scores=None, fibo_levels=None):
    """
    V33 NEXUS X-RAY: Premium Card UI Infographic
    Futuristic Trading Card Design with Glassmorphism and Neon Accents.
    """
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    import matplotlib.patches as patches
    import matplotlib.image as mpimg
    import numpy as np
    import os
    from data_fetcher import get_historical_data
    
    # helper to add logo -> Removed (Using Global)
    
    try:
        # 1. Fetch Data
        df = get_historical_data(ticker, period=period)
        if df.empty: return None
        
        last_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        change_pct = ((last_price - prev_price) / prev_price) * 100
        change_str = f"{change_pct:+.2f}%"
        color_change = "#00ffea" if change_pct >= 0 else "#ff0055"
        
        # 2. Setup Figure (Premium Dark Card)
        # Dimensions tailored for mobile screen (vertical)
        fig = plt.figure(figsize=(10, 20), facecolor='#050505') # Ultra Dark Background
        
        # Add Background Gradient/Texture effect (Simulated via overlay)
        rect = fig.patch
        rect.set_facecolor('#050505')
        
        # Add Logo
        add_logo(fig, 'xray')
        
        # Grid Layout
        gs = gridspec.GridSpec(5, 2, height_ratios=[1.2, 0.8, 4, 3, 1])
        gs.update(wspace=0.15, hspace=0.25, left=0.05, right=0.95, top=0.97, bottom=0.03)
        
        # --- helper: draw_card_bg ---
        def draw_card_bg(ax, title=None, color='#0f0f0f', alpha=0.8):
            ax.set_facecolor(color)
            ax.set_alpha(alpha)
            # Rounded box simulation
            box = patches.FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02,rounding_size=0.05", 
                                         fc=color, ec='#1a1a1a', lw=1, transform=ax.transAxes, zorder=-1)
            ax.add_patch(box)
            if title:
                ax.text(0.05, 0.92, title.upper(), transform=ax.transAxes, 
                        color='#555555', fontsize=10, fontweight='bold')

        # --- A. HEADER SECTION (Identity) ---
        ax_header = fig.add_subplot(gs[0, :])
        ax_header.axis('off')
        
        # Ticker & Badge
        ax_header.text(0.5, 0.65, ticker, color='white', fontsize=52, 
                       fontweight='bold', ha='center', va='center', fontfamily='sans-serif')
        ax_header.text(0.5, 0.35, "ID: STOCK MARKET ASSET", color='#888888', fontsize=12, 
                       ha='center', va='center')
                       
        # Nexus Intelligence Badge
        ax_header.text(0.95, 0.9, "NEXUS INTELLIGENCE", color='#00f2ff', fontsize=10, 
                       ha='right', va='center', alpha=0.8, weight='bold')

        # --- B. PRICE SECTION (Scoreboard) ---
        ax_price = fig.add_subplot(gs[1, :])
        ax_price.axis('off')
        draw_card_bg(ax_price, color='#0a0a0a')
        
        # Price Display
        ax_price.text(0.2, 0.5, "CURRENT PRICE", color='#555555', fontsize=10, ha='center', va='bottom')
        ax_price.text(0.2, 0.25, f"{last_price:,.0f}", color='white', fontsize=38, ha='center', va='center', fontweight='bold')
        
        # Change Pct (Badge style)
        bbox_props = dict(boxstyle="round,pad=0.4", fc=color_change, ec="none", alpha=0.2)
        ax_price.text(0.8, 0.3, change_str, color=color_change, fontsize=28, 
                      ha='center', va='center', fontweight='bold', bbox=bbox_props)
        ax_price.text(0.8, 0.6, "24H CHANGE", color='#555555', fontsize=10, ha='center', va='bottom')

        # --- C. MAIN CHART (Visual Deep Dive) ---
        ax_main = fig.add_subplot(gs[2, :])
        # Manually styling for "Card" look
        ax_main.set_facecolor('#080808')
        for spine in ax_main.spines.values():
            spine.set_edgecolor('#222222')
            
        ax_main.text(0.02, 0.95, "PRICE ACTION & FIBONACCI", transform=ax_main.transAxes, 
                     color='#444444', fontsize=9, fontweight='bold')
        
        df_plot = df.tail(80) # Zoom in for impact
        
        mc = mpf.make_marketcolors(up='#00ff44', down='#ff0055', inherit=True)
        s = mpf.make_mpf_style(base_mpf_style='nightclouds', marketcolors=mc, gridcolor='#151515', 
                               rc={'font.size': 8, 'axes.labelcolor': '#444444'})
        
        # Prepare Fibo Lines
        hlines = []
        colors = []
        if fibo_levels:
            for k,v in fibo_levels.items():
                hlines.append(v)
                if "0.618" in k: colors.append('#ffd700') # Gold
                elif "0.500" in k: colors.append('#ffffff') # White
                else: colors.append('#333333') # Dim others
        
        # Plot Candles
        mpf_kwargs = dict(type='candle', style=s, ax=ax_main, volume=False)
        if hlines:
             mpf_kwargs['hlines'] = dict(hlines=hlines, colors=colors, linewidths=0.7, linestyle='--')
             
        mpf.plot(df_plot, **mpf_kwargs)
        
        ax_main.yaxis.tick_right()
        ax_main.tick_params(colors='#666666', labelsize=8)
        ax_main.grid(True, color='#151515', linestyle='--')

        # --- D. RADAR CHART (5-Factor Analysis) ---
        # Create a polar axes inside the specific grid cell
        # We need a dedicated frame for this
        ax_radar_frame = fig.add_subplot(gs[3, 0])
        ax_radar_frame.axis('off')
        draw_card_bg(ax_radar_frame, title="NEXUS AI SCORE")
        
        # The actual polar plot needs to be floating inside
        pos = ax_radar_frame.get_position()
        # [left, bottom, width, height]
        ax_radar = fig.add_axes([pos.x0 + 0.02, pos.y0 + 0.02, pos.width - 0.04, pos.height - 0.06], polar=True)
        
        categories = ['Valuation', 'Trend', 'Momentum', 'Volatility', 'Volume']
        if radar_scores:
            values = [radar_scores.get(c, 50) for c in categories]
        else:
            values = [50, 50, 50, 50, 50]
        
        # Make it a loop
        values += [values[0]]
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles += [angles[0]]
        
        ax_radar.set_facecolor('#0f0f0f')
        ax_radar.plot(angles, values, color='#00f2ff', linewidth=2)
        ax_radar.fill(angles, values, color='#00f2ff', alpha=0.3)
        
        # Custom Grid
        ax_radar.set_xticks(angles[:-1])
        ax_radar.set_xticklabels(categories, color='#aaaaaa', fontsize=9, fontweight='bold')
        ax_radar.set_yticks([30, 60, 90])
        ax_radar.set_yticklabels(['', '', ''], color='#333333')
        ax_radar.spines['polar'].set_visible(False)
        ax_radar.grid(color='#222222', linestyle=':')
        
        # Center Score
        avg_score = int(np.mean(values[:-1])) if radar_scores else 50
        ax_radar.text(0, 0, str(avg_score), color='white', fontsize=24, fontweight='bold', ha='center', va='center')

        # --- E. STATS GRID (Insights) ---
        ax_stats = fig.add_subplot(gs[3, 1])
        ax_stats.axis('off')
        draw_card_bg(ax_stats, title="KEY INSIGHTS")
        
        # Helper to draw stat row
        def draw_stat_row(ax, y, label, value, color='white'):
            ax.text(0.1, y, label, color='#666666', fontsize=10, transform=ax.transAxes)
            ax.text(0.9, y, value, color=color, fontsize=10, fontweight='bold', ha='right', transform=ax.transAxes)
            
        trend_val = radar_scores.get('Trend', 50)
        mom_val = radar_scores.get('Momentum', 50)
        vol_val = radar_scores.get('Volatility', 50)
        
        trend_str = "BULLISH" if trend_val > 60 else "BEARISH" if trend_val < 40 else "SIDEWAYS"
        trend_col = "#00ff44" if trend_val > 60 else "#ff0055" if trend_val < 40 else "#ffffff"
        
        mom_str = "STRONG" if mom_val > 60 else "WEAK"
        
        draw_stat_row(ax_stats, 0.75, "PRIMARY TREND", trend_str, trend_col)
        draw_stat_row(ax_stats, 0.60, "MOMENTUM", mom_str)
        draw_stat_row(ax_stats, 0.45, "VOLATILITY", f"{vol_val:.1f}")
        draw_stat_row(ax_stats, 0.30, "VOLUME FLOW", f"{radar_scores.get('Volume', 0)}")
        
        # Quality Badge
        q_score = "A" if avg_score > 80 else "B" if avg_score > 60 else "C" if avg_score > 40 else "D"
        q_col = "#00ff44" if q_score in ["A", "B"] else "#ff9100"
        
        ax_stats.text(0.5, 0.1, f"RATING: {q_score}", color=q_col, fontsize=18, 
                      fontweight='bold', ha='center', va='center', 
                      bbox=dict(boxstyle="round,pad=0.3", fc='#1a1a1a', ec=q_col, lw=2))

        # --- F. FOOTER ---
        ax_footer = fig.add_subplot(gs[4, :])
        ax_footer.axis('off')
        ax_footer.text(0.5, 0.3, "GENERATED BY NEXUS TRADING AI | POWERED BY DEEPMIND", 
                       color='#333333', fontsize=8, ha='center')

        # Save
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=120, facecolor='#050505', bbox_inches='tight')
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
        
        # Add Logo
        add_logo(fig, 'top-left')
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', facecolor='#0a0a0a', bbox_inches='tight', dpi=100)
        plt.close(fig)
        buf.seek(0)
        return buf
        
    except Exception as e:
        logger.error(f"Error generating pie chart: {e}")
        return None

def generate_prediction_card(data):
    """
    V35 NEXUS FUTURE SIGHT: Prediction Card
    data: dict returned from predict_future_price
    """
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import io
    
    try:
        ticker = data['ticker']
        target = data['target']
        current = data['current_price']
        change_pct = data['change_pct']
        confidence = data['confidence']
        bias = data['bias']
        reason = data['reason']
        rsi = data['rsi']
        slope = data['slope']
        
        # Setup Figure
        fig = plt.figure(figsize=(10, 12), facecolor='#050505')
        ax = fig.add_axes([0, 0, 1, 1]) # Full bleed
        ax.set_facecolor('#050505')
        ax.axis('off')
        
        # Helper: Draw Card BG
        def draw_box(x, y, w, h, color='#0a0a0a', alpha=1.0):
            rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.05", 
                                          fc=color, ec='#1a1a1a', lw=1, alpha=alpha)
            ax.add_patch(rect)
            
        # 1. Header
        draw_box(0.05, 0.82, 0.9, 0.15, color='#0a0a0a')
        ax.text(0.5, 0.93, f"FUTURE SIGHT: {ticker}", color='white', fontsize=32, fontweight='bold', ha='center', va='center')
        ax.text(0.5, 0.86, "AI PROJECTION ENGINE", color='#00f2ff', fontsize=12, fontweight='bold', ha='center', va='center')
        
        # 2. Target Price (Big Center)
        color_target = "#00ff44" if change_pct > 0 else "#ff0055"
        draw_box(0.05, 0.55, 0.9, 0.25, color='#080808')
        
        ax.text(0.5, 0.75, "TARGET PRICE (7 DAYS)", color='#555555', fontsize=12, ha='center')
        ax.text(0.5, 0.67, f"Rp {target:,.0f}", color='white', fontsize=48, fontweight='bold', ha='center')
        
        # Change Pill
        bbox_props = dict(boxstyle="round,pad=0.3", fc=color_target, ec="none", alpha=0.9)
        ax.text(0.5, 0.59, f"{change_pct:+.2f}%", color='black', fontsize=16, fontweight='bold', ha='center', bbox=bbox_props)
        
        # 3. Confidence & Logic
        draw_box(0.05, 0.15, 0.9, 0.38, color='#0a0a0a')
        
        # Logic Rows
        ax.text(0.1, 0.48, "CONFIDENCE LEVEL", color='#888888', fontsize=10)
        # Visual Bar for Confidence
        # Draw empty bar
        rect_bg = patches.Rectangle((0.1, 0.44), 0.8, 0.02, fc='#222222')
        ax.add_patch(rect_bg)
        # Draw fill bar
        rect_fill = patches.Rectangle((0.1, 0.44), 0.8 * (confidence/100), 0.02, fc='#00f2ff')
        ax.add_patch(rect_fill)
        ax.text(0.9, 0.48, f"{confidence}%", color='#00f2ff', fontsize=12, fontweight='bold', ha='right')
        
        ax.text(0.1, 0.38, "PRIMARY BIAS", color='#888888', fontsize=10)
        ax.text(0.9, 0.38, bias, color='white', fontsize=12, fontweight='bold', ha='right')
        
        ax.text(0.1, 0.30, "KEY DRIVER", color='#888888', fontsize=10)
        ax.text(0.9, 0.30, reason, color='white', fontsize=12, fontweight='bold', ha='right')
        
        ax.text(0.1, 0.22, "MOMENTUM (RSI)", color='#888888', fontsize=10)
        ax.text(0.9, 0.22, f"{rsi:.1f}", color='white', fontsize=12, fontweight='bold', ha='right')
        
        # 4. Footer
        ax.text(0.5, 0.08, "GENERATED BY NEXUS PREDICTIVE AI", color='#333333', fontsize=8, ha='center')
        
        # Logo
        add_logo(fig, 'top-right')
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, facecolor='#050505', bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        return buf
        
    except Exception as e:
        logger.error(f"Prediction Card Error: {e}")
        return None
