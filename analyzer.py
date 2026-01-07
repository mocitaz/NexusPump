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
    V30 NEXUS SNIPER: BSJP PRO
    Uses Batch Data Fetch (Performance Optimized)
    And Real Backtest Data for Win Rate.
    """
    from data_fetcher import get_batch_historical_data
    from backtester import calculate_bsjp_winrate
    candidates = []
    
    # 1. Batch Fetch Data (Much Faster)
    # We need ~1-2 months for the Strategy Filter
    # Backtester needs more (6mo), but we only fetch that for Candidates.
    batch_data = get_batch_historical_data(watchlist, period="2mo")
    
    for ticker, df in batch_data.items():
        try:
           if df.empty or len(df) < 21: continue
           
           last = df.iloc[-1]
           prev = df.iloc[-2]
           
           # Logic: Up > 2%, Vol > Avg, Close near High
           if prev['Close'] == 0: continue
           change = ((last['Close'] - prev['Close']) / prev['Close']) * 100
           
           # Handle missing Volume
           if 'Volume' not in df.columns: continue
           
           avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
           if avg_vol == 0: continue
           
           vol_ratio = last['Volume'] / avg_vol
           
           # Rolling means for trend check
           ma20 = df['Close'].rolling(20).mean().iloc[-1]
           ma50 = df['Close'].rolling(50).mean().iloc[-1]
           
           if 2.0 <= change <= 15.0 and last['Close'] > ma20 and vol_ratio > 1.2:
               # Calculate REAL Win Rate via Backtest (Only for candidates)
               # Still individual fetch, but only for ~5-10 stocks max.
               bt = calculate_bsjp_winrate(ticker, period="6mo")
               
               win_prob = 0
               trade_count = 0
               avg_gain = 0
               
               if bt:
                   win_prob = bt['win_rate']
                   trade_count = bt['trades']
                   avg_gain = bt['avg_gain']
               else:
                   # Fallback Heuristic
                   win_prob = 60
                   if last['Close'] > ma50: win_prob += 10
               
               candidates.append({
                   "ticker": ticker,
                   "price": last['Close'],
                   "change": change,
                   "vol_ratio": vol_ratio,
                   "win_prob": win_prob,
                   "trades": trade_count,
                   "avg_gain": avg_gain
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
    V21 NEXUS FLOW (Performance Optimized)
    Criteria: Silent Accumulation or Golden Flow.
    """
    from data_fetcher import get_batch_historical_data
    results = []
    
    # 1. Batch Fetch
    batch_data = get_batch_historical_data(watchlist, period="1mo")
    
    for ticker, df in batch_data.items():
        try:
            if df.empty or len(df) < 20: continue
            
            last = df.iloc[-1]
            if df['Volume'].empty: continue
            avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
            
            # Avoid division by zero
            if avg_vol == 0: continue
            
            vol_ratio = last['Volume'] / avg_vol
            if df.iloc[-2]['Close'] == 0: price_change = 0
            else:
                price_change = ((last['Close'] - df.iloc[-2]['Close']) / df.iloc[-2]['Close']) * 100
            
            signal = None
            desc = ""
            
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

def scan_top_picks(watchlist):
    """
    V24 NEXUS WATCHLIST: TOP PICKS FOR TOMORROW
    Uses Batch Data Fetch (Performance Optimized)
    Criteria: Strong Uptrend, Healthy RSI, Accumulation Volume.
    """
    from data_fetcher import get_batch_historical_data
    candidates = []
    
    # Batch Fetch Data (Much Faster)
    batch_data = get_batch_historical_data(watchlist, period="3mo")
    
    for ticker, df in batch_data.items():
        try:
            if df.empty or len(df) < 50: continue
            
            last = df.iloc[-1]
            close = df['Close']
            
            # Indicators
            ma20 = close.rolling(20).mean().iloc[-1]
            ma50 = close.rolling(50).mean().iloc[-1]
            rsi = ta.momentum.RSIIndicator(close, window=14).rsi().iloc[-1]
            
            avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
            vol_ratio = last['Volume'] / avg_vol if avg_vol > 0 else 0
            
            # FILTERS
            # 1. Uptrend: Close > MA20 & MA20 > MA50 (Golden Alignment)
            if not (last['Close'] > ma20 and ma20 > ma50): continue
            
            # 2. RSI Healthy (45-75) - Not Oversold, Not Extreme Overbought (Relaxed slightly)
            if not (45 <= rsi <= 78): continue
            
            # 3. Volume Check (Liquid & Active)
            if vol_ratio < 0.6: continue # Relaxed to 0.6 to catch more
            
            # SCORING
            score = 0
            reasons = []
            
            if vol_ratio > 1.2: 
                score += 20; reasons.append("Accumulation 🐳")
            if rsi > 55: 
                score += 10; reasons.append("Strong Momentum ⚡")
            if last['Close'] > df['High'].iloc[-20:].max(): 
                score += 30; reasons.append("Breakout 🚀")
            
            # Avoid too high pumps
            if df.iloc[-2]['Close'] == 0: change_pct = 0
            else:
                 change_pct = ((last['Close'] - df.iloc[-2]['Close']) / df.iloc[-2]['Close']) * 100
                 
            if change_pct > 20: continue # Too risky already pumped
            
            candidates.append({
                "ticker": ticker,
                "price": last['Close'],
                "change": change_pct,
                "score": score,
                "reasons": ", ".join(reasons) if reasons else "Trend Follow",
                "vol_ratio": vol_ratio
            })
            
        except Exception: continue
        
    # Sort by Score -> Vol Ratio
    candidates.sort(key=lambda x: (x['score'], x['vol_ratio']), reverse=True)
    return candidates

def scan_sector_performance():
    """
    V26 NEXUS SECTOR RADAR: Rotational Analysis
    Calculates average performance of each sector based on available data.
    """
    from idx_tickers import SECTOR_MAP
    from data_fetcher import get_top_gainers_losers_idx
    
    # Reuse the batch fetcher (Efficient)
    # This returns tuple (gainers, losers), so we combine them or fetch raw
    # Actually get_top_gainers_losers_idx fetches ALL and splits. 
    # Let's modify logic: The function separates them. 
    # We can just fetch them and combine, or better, make a new lightweight fetcher?
    # No, reuse is best to keep code DRY. `get_top_gainers_losers_idx` logic:
    # It sorts and cuts. We want ALL. 
    # Ah, the function `get_top_gainers_losers_idx` in data_fetcher returns ONLY top 10.
    # We need the RAW list.
    # Let's import the RAW fetching logic or create a helper in data_fetcher?
    # For now, I will create a focused fetcher here or use `get_stock_price` in loop? 
    # Loop is slow.
    # Better: Use `get_top_gainers_losers_idx` but I might need to edit data_fetcher to return all?
    # Let's checking data_fetcher again.
    
    # Re-reading data_fetcher shows it sorts and returns [:10]. 
    # I should add `get_all_market_data` in data_fetcher.py ideally.
    # But to avoid editing too many files, I will Implement a local batch fetch here similar to that one.
    
    import yfinance as yf
    from idx_tickers import IDX_WATCHLIST
    
    tickers_idx = [t + ".JK" for t in IDX_WATCHLIST]
    try:
        # Batch Fetch 2d is enough for calculating change (Previous Close vs Last Close)
        # Optimized for speed.
        # Use group_by='ticker' to access via df['Ticker']['Close'] or df['Ticker']
        df = yf.download(tickers_idx, period="2d", interval="1d", group_by='ticker', progress=False, threads=False, actions=False)
        if df.empty: return []
        
        sector_perf = []
        
        for sector, tickers in SECTOR_MAP.items():
            total_change = 0
            count = 0
            top_ticker = None
            top_change = -999
            
            for t in tickers:
                t_jk = t + ".JK"
                if t_jk not in df.columns.levels[0]: continue # Skip if no data
                
                try:
                    # Get Close
                    closes = df[t_jk]['Close'].dropna()
                    if len(closes) < 2: continue
                    
                    last = closes.iloc[-1]
                    prev = closes.iloc[-2]
                    change = ((last - prev) / prev) * 100
                    
                    total_change += change
                    count += 1
                    
                    if change > top_change:
                        top_change = change
                        top_ticker = t
                except: continue
            
            if count > 0:
                avg_change = total_change / count
                stats = "🔥" if avg_change > 1.0 else "❄️" if avg_change < -0.5 else "➡️"
                sector_perf.append({
                    "sector": sector,
                    "avg_change": avg_change,
                    "top_stock": top_ticker,
                    "top_change": top_change,
                    "stats": stats
                })
        
        # Sort by Performance
        sector_perf.sort(key=lambda x: x['avg_change'], reverse=True)
        return sector_perf
        
    except Exception as e:
        logger.error(f"Sector Scan Error: {e}")
        return []

def calculate_fibonacci_levels(ticker, period="6mo"):
    """
    V31 AUTO-FIBONACCI
    Calculates Fibonacci Retracement Levels based on Swing High/Low.
    """
    from data_fetcher import get_historical_data
    try:
        df = get_historical_data(ticker, period=period)
        if df.empty or len(df) < 20: return None
        
        # 1. Identify Swing High & Low
        # We assume the Trend is Uptrend for Retracement (Low -> High)
        # Or Downtrend (High -> Low).
        # Simple Logic: Max High and Min Low in the period.
        
        high_price = df['High'].max()
        low_price = df['Low'].min()
        current_price = df['Close'].iloc[-1]
        
        diff = high_price - low_price
        
        # Fibonacci Ratios
        ratios = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
        levels = {}
        
        # Determine Direction?
        # Usually we draw from recent major swing. 
        # If Current Close is closer to High -> Retracement from Low to High? No.
        # Standard: Just plot the levels between High and Low.
        # Retracement Level = High - (Difference * Ratio)
        
        for r in ratios:
            price_level = high_price - (diff * r)
            levels[f"Fib {r:.3f}"] = price_level
            
        return {
            "high": high_price,
            "low": low_price,
            "levels": levels,
            "current": current_price,
            "trend": "UP" if current_price > (low_price + high_price)/2 else "DOWN"
        }
        
    except Exception as e:
        logger.error(f"Fibonacci Error {ticker}: {e}")
        return None

def analyze_radar_metrics(ticker):
    """
    V32 X-RAY: Radar Chart Metrics (0-100 Scale)
    Returns dict for visual plotting.
    """
    from data_fetcher import get_historical_data, get_stock_fundamentals
    import numpy as np
    
    try:
        # 1. Fetch Tech Data
        df = get_historical_data(ticker, period="6mo")
        if df.empty or len(df) < 50: return None
        
        # 2. Fetch Fundamentals
        fund = get_stock_fundamentals(ticker) # {'pe': 15, 'pbv': 2...} or None
        
        scores = {
            "Valuation": 50, "Trend": 50, "Momentum": 50, "Volatility": 50, "Volume": 50
        }
        
        # --- A. VALUATION (Fundamental) ---
        if fund:
            val_score = 50
            # PE Ratio (Lower is Better, typically)
            pe = fund.get('trailingPE')
            if pe:
                if pe < 10: val_score += 30
                elif pe < 20: val_score += 10
                elif pe > 40: val_score -= 20
            
            # PBV (Lower is Better)
            pbv = fund.get('priceToBook')
            if pbv:
                if pbv < 1: val_score += 20
                elif pbv > 5: val_score -= 10
                
            scores['Valuation'] = max(10, min(95, val_score))
        else:
            scores['Valuation'] = 50 # Neutral if no data
            
        # --- B. TREND (MA Alignment) ---
        close = df['Close']
        ma20 = close.rolling(20).mean().iloc[-1]
        ma50 = close.rolling(50).mean().iloc[-1]
        ma200 = close.rolling(200).mean().iloc[-1]
        price = close.iloc[-1]
        
        trend_score = 30
        if price > ma20: trend_score += 20
        if price > ma50: trend_score += 20
        if price > ma200: trend_score += 30 # Strong Bull
        scores['Trend'] = trend_score
        
        # --- C. MOMENTUM (RSI + MACD) ---
        rsi = ta.momentum.RSIIndicator(close, window=14).rsi().iloc[-1]
        macd = ta.trend.MACD(close)
        macd_diff = macd.macd_diff().iloc[-1]
        
        mom_score = 50
        # RSI 50-70 is sweet spot
        if 50 <= rsi <= 70: mom_score += 30
        elif rsi > 70: mom_score += 10 # Overbought but strong
        elif rsi < 30: mom_score -= 20 # Oversold (unless reversal)
        
        if macd_diff > 0: mom_score += 20
        scores['Momentum'] = max(10, min(95, mom_score))
        
        # --- D. VOLATILITY (Stability = High Score) ---
        # If volatile, score low (Risk). If stable uptrend, score high.
        # Use Bollinger width or ATR check.
        # Simplified: Daily Return Std Dev
        returns = close.pct_change().tail(30)
        std_dev = returns.std() * 100 # e.g. 2.5%
        
        # Lower std dev is better stability? Depends. 
        # For "Quality", Stability is good.
        vol_score = 100 - (std_dev * 10) # If std=2%, score=80. If std=5%, score=50.
        scores['Volatility'] = max(10, min(95, vol_score))
        
        # --- E. VOLUME (Flow) ---
        avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
        curr_vol = df['Volume'].iloc[-1]
        
        vol_score = 50
        ratio = curr_vol / avg_vol if avg_vol > 0 else 1
        
        if ratio > 1.0: vol_score += 10
        if ratio > 2.0: vol_score += 20
        if ratio > 5.0: vol_score += 20 # Massive
        
        # OBV Slope check could be better but Ratio is simple
        scores['Volume'] = max(10, min(95, vol_score))
        
        return scores
        
    except Exception as e:
        logger.error(f"Radar Analysis Error {ticker}: {e}")
        return None
