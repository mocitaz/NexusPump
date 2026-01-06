import pandas as pd
import ta
import logging
from sklearn.linear_model import LinearRegression
import numpy as np
from data_fetcher import get_historical_data, get_stock_price

logger = logging.getLogger(__name__)

def analyze_stock(ticker):
    """
    Performs technical analysis on the stock: RSI, MACD, Bollinger Bands.
    Returns a summary string and signal.
    """
    try:
        # Need enough data for technical indicators (at least 2-3 months)
        df = get_historical_data(ticker, period="6mo")
        if df.empty:
            return "Data saham tidak ditemukan.", "NEUTRAL"
        
        # Ensure we have enough data points
        if len(df) < 50:
            return "Data tidak cukup untuk analisis teknikal.", "NEUTRAL"

        # --- Indicators ---
        # RSI (14)
        df['rsi'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        
        # MACD
        macd = ta.trend.MACD(df['Close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        
        # Bollinger Bands
        bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
        df['bb_high'] = bb.bollinger_hband()
        df['bb_low'] = bb.bollinger_lband()
        
        # --- Pivot Points (Classic) ---
        # Based on yesterday's data
        last_complete_candle = df.iloc[-2] # Assuming -1 is current live candle (incomplete)
        high = last_complete_candle['High']
        low = last_complete_candle['Low']
        close = last_complete_candle['Close']
        
        pivot = (high + low + close) / 3
        r1 = (2 * pivot) - low
        s1 = (2 * pivot) - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        current_price = last_row['Close']
        rsi_val = last_row['rsi']
        
        # --- Pattern Recognition (Simple) ---
        patterns = []
        
        # Doji: Open and Close are very close
        body_size = abs(last_row['Close'] - last_row['Open'])
        full_range = last_row['High'] - last_row['Low']
        if full_range > 0 and (body_size / full_range) < 0.1:
            patterns.append("Doji (Ketidakpastian)")
            
        # Hammer: Small body at top, long lower wick
        lower_wick = min(last_row['Open'], last_row['Close']) - last_row['Low']
        upper_wick = last_row['High'] - max(last_row['Open'], last_row['Close'])
        if full_range > 0 and lower_wick > (2 * body_size) and upper_wick < body_size:
            patterns.append("Hammer (Potensi Reversal Bullish)")
            
        # Bullish Engulfing
        prev_body = prev_row['Close'] - prev_row['Open']
        curr_body = last_row['Close'] - last_row['Open']
        if prev_body < 0 and curr_body > 0 and last_row['Close'] > prev_row['Open'] and last_row['Open'] < prev_row['Close']:
             patterns.append("Bullish Engulfing (Kuat Bullish)")

        # --- Signals & Scoring ---
        signals = []
        score = 50 # Neutral 50
        
        # RSI Analysis
        if rsi_val > 70:
            signals.append("RSI Overbought (>70)")
            score -= 20
        elif rsi_val < 30:
            signals.append("RSI Oversold (<30)")
            score += 20
        elif 45 <= rsi_val <= 55:
            score += 0 # Neutral
        elif rsi_val > 55:
            score += 5 # Slight Bullish
        else:
            score -= 5 # Slight Bearish
            
        # MACD
        if (prev_row['macd'] < prev_row['macd_signal']) and (last_row['macd'] > last_row['macd_signal']):
            signals.append("MACD Golden Cross")
            score += 30
        elif (prev_row['macd'] > prev_row['macd_signal']) and (last_row['macd'] < last_row['macd_signal']):
            signals.append("MACD Death Cross")
            score -= 30
        elif last_row['macd'] > last_row['macd_signal']:
            score += 10 # Bullish Trend
        else:
            score -= 10 # Bearish Trend
            
        # Support/Resistance Check
        dist_r1 = abs(current_price - r1) / current_price
        dist_s1 = abs(current_price - s1) / current_price
        
        if dist_r1 < 0.01:
            signals.append("Dekat Resistance R1")
        if dist_s1 < 0.01:
            signals.append("Dekat Support S1")
            
        # Bollinger
        if current_price >= last_row['bb_high']:
            signals.append("Break Upper BB")
        elif current_price <= last_row['bb_low']:
            signals.append("Break Lower BB")

        # Determine Signal
        if score >= 75: signal_type = "STRONG BUY 🟢"
        elif score >= 60: signal_type = "BUY 🟢"
        elif score <= 25: signal_type = "STRONG SELL 🔴"
        elif score <= 40: signal_type = "SELL 🔴"
        else: signal_type = "NEUTRAL 🟡"
        
        # Formatting Output with "Professional Card" style
        rsi_desc = "Oversold (Cheap)" if rsi_val < 30 else "Overbought (Expensive)" if rsi_val > 70 else "Neutral Area"
        macd_desc = "Bullish Momentum" if last_row['macd'] > last_row['macd_signal'] else "Bearish Momentum"
        
        summary = (
            f"🧠 *NEXUS INTELLIGENCE: {ticker}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🚨 *SIGNAL: {signal_type}*\n"
            f"• Confidence : {score}%\n"
            f"• Trend      : {macd_desc}\n"
            f"• Strength   : {rsi_desc}\n\n"
            f"📐 *KEY LEVELS (Pivot)*:\n"
            f"🔴 resisten  : {r1:,.0f}\n"
            f"🔵 support   : {s1:,.0f}\n"
            f"⚪ pivot     : {pivot:,.0f}\n\n"
            f"📊 *TECHNICAL DATA*:\n"
            f"• RSI (14)   : {rsi_val:.1f}\n"
            f"• MACD       : {last_row['macd']:.2f}\n"
            f"• Pattern    : {', '.join(patterns) if patterns else 'No Pattern'}\n\n"
            f"💡 *STRATEGY NOTE*:\n"
            f"_{ 'Accumulate at Support. Valid breakout soon.' if score > 50 else 'Wait for bottom. Do not catch falling knife.' }_\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )
        
        return summary, signal_type

    except Exception as e:
        logger.error(f"Error analyzing {ticker}: {e}")
        return "⚠️ *Analysis Failed*. Data insufficient.", "ERROR"

# ... (skip scan_bsjp_strategy, scan_market_screener as they return dicts) ...

def predict_future_price(ticker, days=7):
    """
    Simple Linear Regression prediction.
    """
    try:
        # Linear Regression Logic (Hidden for brevity, assuming context has model initialization)
        # Actually I need to keep the logic valid.
        # Wait, the tool only replaces what I select. I need to select the FUNCTION BODY or relevant parts.
        # I will replace the LOGIC + STRING.
        
        df = get_historical_data(ticker, period="3mo")
        if df.empty or len(df) < 20:
            return "⚠️ *Prediction Failed*. Not enough data."

        # Model Training
        df = df.reset_index()
        df['ordinal_date'] = df['Date'].apply(lambda x: x.toordinal())
        X = df[['ordinal_date']].values
        y = df['Close'].values
        
        model = LinearRegression() # Need to ensure import, it is at top
        model.fit(X, y)
        
        score = model.score(X, y) * 100
        slope = model.coef_[0]
        
        # Trend Desc
        if slope > 10: trend_desc = "Bullish Strong 🚀"
        elif slope > 0: trend_desc = "Bullish 📈"
        elif slope > -10: trend_desc = "Bearish 📉"
        else: trend_desc = "Bearish Strong 🩸"
        
        # Predict
        last_date = df['Date'].iloc[-1]
        future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, days+1)]
        future_ordinal = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)
        predictions = model.predict(future_ordinal)
        target_price = predictions[-1]
        
        current_price = y[-1]
        potential = ((target_price - current_price) / current_price) * 100
        
        # Professional Table output
        table_lines = []
        for i, val in enumerate(predictions):
            table_lines.append(f"Day {i+1}: {val:,.0f}")
            
        # Join nicely? No, list is too long for vertical.
        # "Day 1: 1000 | Day 2: 1020" format?
        # Or just Top Target.
        
        msg = (
            f"🔮 *NEXUS PROJECTION: {ticker}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 *TARGET (7 Days)*\n"
            f"Rp {target_price:,.0f} ({potential:+.2f}%)\n\n"
            f"⚙️ *MODEL STATS*:\n"
            f"• Trend    : {trend_desc}\n"
            f"• Accuracy : {score:.1f}% (R-Squared)\n"
            f"• Slope    : {slope:.2f}\n\n"
            f"📅 *FORECAST ROADMAP*:\n"
        )
        
        for i, val in enumerate(predictions):
            msg += f"• H+{i+1} : Rp {val:,.0f}\n"
            
        msg += f"━━━━━━━━━━━━━━━━━━━━━━\n💡 _Statistical projection only._"
        return msg

    except Exception as e:
        logger.error(f"Prediction error for {ticker}: {e}")
        return "⚠️ *Error*. Could not calculate prediction."
