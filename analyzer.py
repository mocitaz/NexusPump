import pandas as pd
import ta
import logging
from sklearn.linear_model import LinearRegression
import numpy as np
from data_fetcher import get_historical_data, get_stock_price

logger = logging.getLogger(__name__)

def calculate_fibonacci(high, low):
    """
    Returns Fib Supports and Resistances based on recent High/Low.
    """
    diff = high - low
    levels = {
        '0.0': low,
        '0.236': low + diff * 0.236,
        '0.382': low + diff * 0.382,
        '0.5': low + diff * 0.5,
        '0.618': low + diff * 0.618,
        '1.0': high
    }
    return levels

def analyze_stock(ticker):
    """
    V23 ULTRA INTELLIGENCE ANALYSIS.
    Includes: Market Structure (HH/HL), Fibonacci, Volume Flow, and Smart Money Insights.
    """
    try:
        # 1. Fetch Data
        df = get_historical_data(ticker, period="1y")
        if df.empty or len(df) < 50:
            return "⚠️ *Data tidak cukup* (Min 50 hari).", "NEUTRAL"

        # 2. Key Indicators
        close = df['Close']
        volume = df['Volume']
        last = df.iloc[-1]
        price = last['Close']
        
        # Moving Averages
        ma20 = close.rolling(20).mean().iloc[-1]
        ma50 = close.rolling(50).mean().iloc[-1]
        ma200 = close.rolling(200).mean().iloc[-1]
        
        # Momentum
        rsi = ta.momentum.RSIIndicator(close, window=14).rsi().iloc[-1]
        macd = ta.trend.MACD(close)
        macd_line = macd.macd().iloc[-1]
        macd_signal = macd.macd_signal().iloc[-1]
        
        # 3. Market Structure (Dow Theory Simplified)
        # Check last 3 peaks/valleys
        # Simplified: Is High > Prev High?
        recent_highs = df['High'].rolling(20).max()
        recent_lows = df['Low'].rolling(20).min()
        
        structure = "Sideways ➡️"
        if price > recent_highs.iloc[-20]: structure = "Breakout HH 🚀"
        elif price < recent_lows.iloc[-20]: structure = "Breakdown LL 🔻"
        elif price > ma50: structure = "Uptrend Structure ↗️"
        
        # 4. Fibonacci Levels (last 3 months swing)
        curr_idx = len(df)
        lookback = min(curr_idx, 60)
        swing_high = df['High'].tail(lookback).max()
        swing_low = df['Low'].tail(lookback).min()
        fibs = calculate_fibonacci(swing_high, swing_low)
        
        # Find nearest Support/Resist
        next_res = min([v for k,v in fibs.items() if v > price], default=swing_high*1.05)
        next_sup = max([v for k,v in fibs.items() if v < price], default=swing_low*0.95)

        # 5. Smart Money / Volume Flow
        avg_vol = volume.rolling(20).mean().iloc[-1]
        vol_ratio = volume.iloc[-1] / avg_vol
        
        money_flow = "Normal"
        if vol_ratio > 2.0 and price > df.iloc[-2]['Close']:
            money_flow = "Big Accumulation 🐳"
        elif vol_ratio > 1.5 and price < df.iloc[-2]['Close']:
            money_flow = "Distribution Detected 📤"
            
        # 6. Scoring Logic
        score = 50
        reasons = []
        
        if price > ma20: score += 10; reasons.append("Price > MA20")
        if price > ma50: score += 10; reasons.append("Price > MA50")
        if price > ma200: score += 15; reasons.append("Long Term Bullish")
        if rsi > 50 and rsi < 70: score += 10; reasons.append("RSI Bullish Zone")
        elif rsi < 30: score += 15; reasons.append("RSI Oversold (Bounce)")
        if macd_line > macd_signal: score += 10; reasons.append("MACD Golden Cross")
        if "Breakout" in structure: score += 10; reasons.append("New High Breakout")
        
        # 7. Final Output Construction
        if score >= 75: 
            signal = "STRONG BUY 🚀"; advice = "Aggressive Entry / Hold"
        elif score >= 55: 
            signal = "BUY 🟢"; advice = "Accumulate on Dip"
        elif score <= 25: 
            signal = "STRONG SELL 🩸"; advice = "Exit Immediately"
        elif score <= 45: 
            signal = "SELL 🔴"; advice = "Sell on Strength"
        else: 
            signal = "NEUTRAL 🟡"; advice = "Wait & See"
            
        summary = (
            f"🧠 *NEXUS ULTRA INTELLIGENCE: {ticker}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 *STRATEGIC VIEW*\n"
            f"• **Signal**    : {signal}\n"
            f"• **Score**     : {score}/100\n"
            f"• **Structure** : {structure}\n"
            f"• **Flow**      : {money_flow}\n\n"
            f"📏 *KEY LEVELS (FIBONACCI)*\n"
            f"🛑 Res : {next_res:,.0f} (Target)\n"
            f"🛡️ Sup : {next_sup:,.0f} (Entry Area)\n"
            f"⚖️ Pivot: {(next_res+next_sup)/2:,.0f}\n\n"
            f"🔬 *DEEP DIVE METRICS*\n"
            f"• **MA Status** : {'✅ Bullish' if price > ma50 else '❌ Bearish'} (Above MA50)\n"
            f"• **Momentum**  : RSI {rsi:.1f} | MACD {'Bullish' if macd_line > macd_signal else 'Bearish'}\n"
            f"• **Volume**    : {vol_ratio:.1f}x Avg\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 *AI VERDICT*:\n"
            f"\"Market structure {structure.lower()}. Detected {money_flow.lower()}. "
            f"Recommending {advice} with Stop Loss under {next_sup:,.0f}.\""
        )
        return summary, signal

    except Exception as e:
        logger.error(f"Error analyzing {ticker}: {e}")
        return "⚠️ *Analysis Error. Try Again.*", "ERROR"

def scan_bsjp_strategy(watchlist):
    """
    V23 NEXUS SNIPER: BSJP PRO
    Adds Win Probability Calculation.
    """
    from data_fetcher import get_historical_data
    candidates = []
    
    for ticker in watchlist:
        try:
            df = get_historical_data(ticker, period="2mo")
            if df.empty or len(df) < 21: continue
            last = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Logic: Up > 2%, Vol > Avg, Close near High
            change = ((last['Close'] - prev['Close']) / prev['Close']) * 100
            avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
            vol_ratio = last['Volume'] / avg_vol
            
            if 2.0 <= change <= 15.0 and last['Close'] > df['Close'].rolling(20).mean().iloc[-1] and vol_ratio > 1.2:
                # Calculate "Win Probability" based on trend
                win_prob = 60
                if last['Close'] > df['Close'].rolling(50).mean().iloc[-1]: win_prob += 10
                if vol_ratio > 2.0: win_prob += 10
                if change < 5.0: win_prob += 5 # Safe entry
                
                candidates.append({
                    "ticker": ticker,
                    "price": last['Close'],
                    "change": change,
                    "vol_ratio": vol_ratio,
                    "win_prob": min(win_prob, 95)
                })
        except Exception: continue
        
    candidates.sort(key=lambda x: x['win_prob'], reverse=True)
    return candidates

def scan_market_screener(watchlist):
    """
    Screener Logic (Unchanged from V16)
    """
    from data_fetcher import get_historical_data
    results = []
    for ticker in watchlist:
        try:
            df = get_historical_data(ticker, period="1mo")
            if df.empty or len(df) < 20: continue
            last = df.iloc[-1]
            prev = df.iloc[-2]
            pivot = (last['High'] + last['Low'] + last['Close']) / 3
            r1 = (2 * pivot) - last['Low']
            potential_upside = ((r1 - last['Close']) / last['Close']) * 100
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            is_uptrend = last['Close'] > ma20
            body_size = abs(last['Close'] - last['Open']) / last['Open']
            is_stable = body_size < 0.03
            bsjp_status = "AMAN ✅" if (is_uptrend and is_stable) else "RISK ⚠️"
            avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
            vol_ratio = last['Volume'] / avg_vol
            if vol_ratio > 1.5 and last['Close'] > prev['Close']: bandar_sts = "AKUM 🐳"
            elif vol_ratio > 1.5 and last['Close'] < prev['Close']: bandar_sts = "DIST 🔻"
            elif vol_ratio < 0.8: bandar_sts = "SEPI 💤"
            else: bandar_sts = "NORMAL"
            results.append({
                "ticker": ticker, "price": last['Close'], "potential": potential_upside,
                "bsjp": bsjp_status, "bandar": bandar_sts, "date": last.name.strftime('%d-%m')
            })
        except Exception: continue
    results.sort(key=lambda x: x['potential'], reverse=True)
    return results

def predict_future_price(ticker, days=7):
    """
    V23 ULTRA PREDICTION: VISUAL CONFIDENCE
    """
    try:
        # 1. Fetch Data
        df = get_historical_data(ticker, period="3mo") # Need more history for better context
        if df.empty or len(df) < 30: return "⚠️ Data Insufficient."
        
        last_close = df['Close'].iloc[-1]
        
        # 2. Linear Regression (Trend)
        df['ordinal'] = df.index.map(pd.Timestamp.toordinal)
        X = df[['ordinal']].values[-30:] # Last 30 days focus
        y = df['Close'].values[-30:]
        
        model = LinearRegression().fit(X, y)
        score = model.score(X, y) # R-squared
        
        # 3. Momentum Adjustment (V22 Logic +)
        rsi = ta.momentum.RSIIndicator(df['Close'], window=14).rsi().iloc[-1]
        
        slope = model.coef_[0]
        base_target = last_close + (slope * days)
        
        # Anchor Logic
        # If RSI > 60 and Slope is Negative -> Ignore Slope, Use Momentum Drift
        if rsi > 60 and slope < 0:
            target = last_close * 1.05 # Assume 5% gain
            confidence = 65
            reason = "Bullish Divergence (Price Reversal)"
            bias = "Bullish ↗️"
        elif rsi < 40 and slope > 0:
            target = last_close * 0.95
            confidence = 65
            reason = "Bearish Divergence"
            bias = "Bearish ↘️"
        else:
            target = base_target
            confidence = int(score * 100)
            reason = "Trend Continuation"
            bias = "Uptrend ↗️" if slope > 0 else "Downtrend ↘️"
            
        # 4. Visuals (Confidence Bar)
        # Scale 0-100 to 10 blocks
        conf_blocks = int(confidence / 10)
        conf_bar = "█" * conf_blocks + "░" * (10 - conf_blocks)
        
        change_pct = ((target - last_close) / last_close) * 100
        
        msg = (
            f"🔮 *NEXUS FUTURE SIGHT: {ticker}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 *TARGET (7 Days)*\n"
            f"Rp {target:,.0f} ({change_pct:+.1f}%)\n\n"
            f"⚖️ *CONFIDENCE LEVEL*\n"
            f"`[{conf_bar}]` {confidence}%\n"
            f"Status: *{bias}*\n\n"
            f"🛠️ *LOGIC BREAKDOWN*\n"
            f"• **Reasoning**: {reason}\n"
            f"• **Momentum** : RSI {rsi:.1f}\n"
            f"• **Trend**    : Slope {slope:.1f}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ _Disclaimer: AI Projection using Linear Regression & Momentum._"
        )
        return msg
        
    except Exception as e:
        logger.error(f"Predict error {ticker}: {e}")
        return "⚠️ Error."

def scan_whale_flow(watchlist):
    """
    V21 NEXUS FLOW (Unchanged)
    """
    from data_fetcher import get_historical_data
    results = []
    
    for ticker in watchlist:
        try:
            # Need strict 20 days for Avg Vol
            df = get_historical_data(ticker, period="1mo")
            if df.empty or len(df) < 20: continue
            
            last = df.iloc[-1]
            avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
            
            # Avoid division by zero
            if avg_vol == 0: continue
            
            vol_ratio = last['Volume'] / avg_vol
            price_change = ((last['Close'] - df.iloc[-2]['Close']) / df.iloc[-2]['Close']) * 100
            
            signal = None
            
            # Logic 1: Silent Accumulation (The dangerous one)
            # Price sideway (-1% to +2%) BUT Volume massive (> 2x)
            if (-1.0 <= price_change <= 2.0) and (vol_ratio > 2.0):
                signal = "SILENT ACCUMULATION 🤫"
                desc = "Stable Price, Giant Volume."
                
            # Logic 2: Golden Flow (Confirmation)
            # Price breakout (> 3%) AND Volume massive (> 2.5x)
            elif (price_change > 3.0) and (vol_ratio > 2.5):
                signal = "GOLDEN FLOW 🐳"
                desc = "Price Breakout + Volume Explosion."
                
            if signal:
                results.append({
                    "ticker": ticker,
                    "signal": signal,
                    "vol_ratio": vol_ratio,
                    "change": price_change,
                    "desc": desc
                })
                
        except Exception:
            continue
            
    # Sort by Vol Ratio (Highest Abnormal Volume first)
    results.sort(key=lambda x: x['vol_ratio'], reverse=True)
    return results
