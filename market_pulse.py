import matplotlib
matplotlib.use('Agg') # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
import io
import logging
from data_fetcher import get_stock_price, get_historical_data
import pandas as pd
import ta

logger = logging.getLogger(__name__)

# Representative Big Caps for Market Breadth
BIG_CAPS = [
    "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "TLKM.JK", 
    "ASII.JK", "GOTO.JK", "AMMN.JK", "ICBP.JK", "UNVR.JK"
]

def calculate_market_mood():
    """
    Calculates the Fear & Greed Index (0-100).
    Components:
    1. IHSG Trend (MA20 & RSI) - 40%
    2. Market Breadth (Big Caps Green/Red) - 40%
    3. Volatility (VIX equivalent - using ATR/Range) - 20% (Simplified to Momentum here)
    """
    score = 50
    details = []
    
    try:
        # 1. IHSG Analysis (Proxy: ^JKSE or manual composite of big caps if index unavailable)
        # yfinance often has issues with ^JKSE delay. Let's use BBCA+BBRI+BMRI average as "Proxy Index" for speed.
        # Actually let's try measuring the "Pulse" of the 10 Big Caps directly.
        
        green_count = 0
        total_rsi = 0
        valid_stocks = 0
        
        for ticker in BIG_CAPS:
            try:
                # We need minimal history for RSI
                df = get_historical_data(ticker, period="1mo")
                if df.empty or len(df) < 15: continue
                
                last = df.iloc[-1]
                prev = df.iloc[-2]
                
                # Breadth: Is it Green?
                if last['Close'] > prev['Close']:
                    green_count += 1
                
                # Momentum: RSI
                rsi = ta.momentum.RSIIndicator(df['Close'], window=14).rsi().iloc[-1]
                total_rsi += rsi
                valid_stocks += 1
                
            except Exception:
                continue
        
        if valid_stocks == 0:
            return 50, "Data Unavailable"
            
        # Component 1: Breadth Score (0-100)
        breadth_score = (green_count / valid_stocks) * 100
        
        # Component 2: Avg RSI Score (0-100)
        avg_rsi = total_rsi / valid_stocks
        # RSI 30 = Score 0 (Fear), RSI 70 = Score 100 (Greed)
        # Scale RSI 30-70 to 0-100
        rsi_score = max(0, min(100, (avg_rsi - 30) * 2.5))
        
        # Final Composite Score
        # 50% Breadth, 50% Momentum
        final_score = (breadth_score * 0.5) + (rsi_score * 0.5)
        
        # Interpretation
        if final_score >= 75: label = "EXTREME GREED 🤑"
        elif final_score >= 60: label = "GREED 🐂"
        elif final_score <= 25: label = "EXTREME FEAR 😱"
        elif final_score <= 40: label = "FEAR 🐻"
        else: label = "NEUTRAL 😐"
        
        description = (
            f"• Big Caps Green : {green_count}/{valid_stocks}\n"
            f"• Avg Momentum   : {avg_rsi:.1f} (RSI)\n"
            f"• Market Mood    : {label}"
        )
        
        return final_score, description
        
    except Exception as e:
        logger.error(f"Error calculating mood: {e}")
        return 50, "Error Calculating Mood"

def generate_gauge_chart(score):
    """
    Generates a Speedometer/Gauge chart for the score (0-100).
    """
    try:
        # Setup plot
        fig, ax = plt.subplots(figsize=(6, 3), subplot_kw={'projection': 'polar'})
        
        # Define 0-100 range in radians (Pi to 0) -> 180 to 0 degrees
        # We want simple half circle
        
        # Ranges
        # 0-25: Red (Extreme Fear)
        # 25-45: Orange (Fear)
        # 45-55: Yellow (Neutral)
        # 55-75: Light Green (Greed)
        # 75-100: Green (Extreme Greed)
        
        # Convert values to angles (0=Pi, 50=Pi/2, 100=0)
        # Angle = Pi - (Value/100 * Pi)
        
        # Draw Bars
        # Red
        ax.barh(1, np.radians(45), left=np.radians(135), height=0.5, color='#ff2a2a', align='center') # 0-25 (Actually 180 to 135 deg)
        # Wait, polar logic is tricky. 
        # 0 is East. Pi is West. We want Pi (Left) to 0 (Right).
        
        # Let's map 0..100 to Pi..0
        
        # Segment 1: 0-25 (Extreme Fear) -> Pi to 0.75Pi
        ax.barh(0.5, np.radians(45), left=np.radians(135), height=0.3, color='#ff0000', alpha=0.8) # Red
        # Segment 2: 25-50 (Fear) -> 0.75Pi to 0.5Pi
        ax.barh(0.5, np.radians(45), left=np.radians(90), height=0.3, color='#ff9900', alpha=0.8) # Orange
        # Segment 3: 50-75 (Greed) -> 0.5Pi to 0.25Pi
        ax.barh(0.5, np.radians(45), left=np.radians(45), height=0.3, color='#ccff00', alpha=0.8) # Yellow-Green
        # Segment 4: 75-100 (Extreme Greed) -> 0.25Pi to 0
        ax.barh(0.5, np.radians(45), left=0, height=0.3, color='#00ff00', alpha=0.8) # Green
        
        # Needle
        val_angle = np.pi - (score / 100.0 * np.pi)
        ax.arrow(val_angle, 0, 0, 0.45, width=0.03, facecolor='white', edgecolor='black', zorder=10)
        
        # Center Circle
        ax.add_patch(plt.Circle((0, 0), 0.1, color='white', zorder=11))
        
        # Styling
        ax.set_axis_off()
        ax.set_theta_direction(-1) # Clockwise? No.
        # Just simple text
        plt.title("\nNEXUS MARKET PULSE", color='white', fontsize=14, pad=20)
        
        # Add Score Text
        plt.text(0, -0.2, f"{score:.0f}", fontsize=30, fontweight='bold', ha='center', color='white')
        
        # Interpret Text
        if score >= 75: txt = "EXTREME GREED"
        elif score >= 60: txt = "GREED"
        elif score <= 25: txt = "EXTREME FEAR"
        elif score <= 40: txt = "FEAR"
        else: txt = "NEUTRAL"
        
        plt.text(0, -0.4, txt, fontsize=12, ha='center', color='cyan')
        
        # Dark Background
        fig.patch.set_facecolor('#0e1117')
        
        # Save
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=120, bbox_inches='tight', facecolor='#0e1117')
        buf.seek(0)
        plt.close(fig)
        
        return buf
        
    except Exception as e:
        logger.error(f"Error generating gauge: {e}")
        return None
