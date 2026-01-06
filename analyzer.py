import pandas as pd
import ta
import logging
from sklearn.linear_model import LinearRegression
import numpy as np
from data_fetcher import get_historical_data, get_stock_price

logger = logging.getLogger(__name__)

def analyze_stock(ticker):
    """
    V18 DEEP INTELLIGENCE ANALYSIS.
    Multi-Timeframe Moving Averages, Volume Dynamics, and Narrative Engineering.
    """
    try:
        # 1. Fetch Data (Need at least 200 days for MA200 if possible, but 6mo is ~120 days)
        # Let's try 1y for comprehensive analysis
        df = get_historical_data(ticker, period="1y")
        if df.empty:
            return "🔍 *Data tidak ditemukan*. Pastikan kode saham benar.", "NEUTRAL"
        
        # Ensure sufficient data
        if len(df) < 50:
            return "⚠️ *Data tidak cukup* (Min 50 hari untuk analisa akurat).", "NEUTRAL"

        # 2. Key Indicators Calculation
        close = df['Close']
        volume = df['Volume']
        
        # Moving Averages
        df['MA20'] = close.rolling(20).mean()
        df['MA50'] = close.rolling(50).mean()
        df['MA200'] = close.rolling(200).mean()
        
        # RSI & MACD
        df['RSI'] = ta.momentum.RSIIndicator(close, window=14).rsi()
        macd = ta.trend.MACD(close)
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        df['MACD_Hist'] = macd.macd_diff()
        
        # Bollinger Bands
        bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
        df['BB_High'] = bb.bollinger_hband()
        df['BB_Low'] = bb.bollinger_lband()
        
        # Stochastic Oscillator (Fast)
        stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], close, window=14, smooth_window=3)
        df['Stoch_K'] = stoch.stoch()
        df['Stoch_D'] = stoch.stoch_signal()
        
        # Volume Analysis
        df['Vol_MA20'] = volume.rolling(20).mean()
        
        # --- Current State ---
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        price = last['Close']
        
        # 3. Comprehensive Logic Scoring
        score = 50
        factors = []
        
        # Trend Analysis (Weight: 40%)
        # Long Term
        if pd.notna(last['MA200']):
            if price > last['MA200']: 
                score += 10
                factors.append("Above MA200 (Long Uptrend)")
            else: 
                score -= 10
        
        # Medium Term
        if pd.notna(last['MA50']):
            if price > last['MA50']:
                score += 10
                factors.append("Above MA50 (Medium Bullish)")
            else:
                score -= 10
                
        # Short Term & Momentum (Weight: 30%)
        if price > last['MA20']:
            score += 5
        else:
            score -= 5
            
        # MACD
        if last['MACD'] > last['MACD_Signal']:
            score += 10
            factors.append("MACD Bullish")
        
        # RSI
        rsi = last['RSI']
        if 50 < rsi < 70: score += 5
        elif rsi > 70: score -= 5 # Overbought risk
        elif rsi < 30: score += 10 # Oversold bounce potential
        
        # Volume Flow (Weight: 20%)
        vol_ratio = last['Volume'] / last['Vol_MA20'] if last['Vol_MA20'] > 0 else 1.0
        if vol_ratio > 1.5 and price > prev['Close']:
            score += 10
            factors.append(f"High Vol Accumulation ({vol_ratio:.1f}x)")
        elif vol_ratio > 1.5 and price < prev['Close']:
            score -= 10
            factors.append(f"High Vol Distribution")
            
        # candlestick pattern check (Simple)
        candle_signal = "Normal"
        body = abs(last['Close'] - last['Open'])
        if body < (last['High'] - last['Low']) * 0.1:
            candle_signal = "Doji (Indecision)"
        
        # 4. Generate Narrative & Conclusion
        
        # Determine Signal Label
        if score >= 80: 
            signal_type = "STRONG BUY 🚀"
            recommendation = "Aggressive Entry possible."
        elif score >= 60: 
            signal_type = "BUY 🟢"
            recommendation = "Accumulate on Weakness (BoW)."
        elif score <= 20: 
            signal_type = "STRONG SELL 🩸"
            recommendation = "Exit immediately / Cash is King."
        elif score <= 40: 
            signal_type = "SELL 🔴"
            recommendation = "Sell on Strength (SoS)."
        else: 
            signal_type = "NEUTRAL 🟡"
            recommendation = "Wait and See. Monitoring."
            
        # Construct Pivot Levels
        pivot = (last['High'] + last['Low'] + last['Close']) / 3
        r1 = (2 * pivot) - last['Low']
        s1 = (2 * pivot) - last['High']
        
        # Generate Text
        
        summary = (
            f"🧠 *NEXUS DEEP INTELLIGENCE: {ticker}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 *EXECUTIVE SUMMARY*\n"
            f"• *Signal*      : {signal_type}\n"
            f"• *Score*       : {score}/100 (Bullishness)\n"
            f"• *Advice*      : _{recommendation}_\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔬 *TECHNICAL DEEP DIVE*\n"
            f"1. **Trend Alignment**:\n"
            f"   - Short (MA20) : {'✅ Bullish' if price > last['MA20'] else '❌ Bearish'}\n"
            f"   - Mid (MA50)   : {'✅ Bullish' if pd.notna(last['MA50']) and price > last['MA50'] else '❌ Bearish' if pd.notna(last['MA50']) else '⚪ N/A'}\n"
            f"   - Long (MA200) : {'✅ Bullish' if pd.notna(last['MA200']) and price > last['MA200'] else '❌ Bearish' if pd.notna(last['MA200']) else '⚪ N/A'}\n\n"
            f"2. **Momentum & Flow**:\n"
            f"   - RSI (14)    : {rsi:.1f} ({'Overbought' if rsi>70 else 'Oversold' if rsi<30 else 'Neutral'})\n"
            f"   - MACD        : {'Golden Cross ↗️' if last['MACD'] > last['MACD_Signal'] else 'Dead Cross ↘️'} (Hist: {last['MACD_Hist']:.2f})\n"
            f"   - Volume      : {vol_ratio:.1f}x Avg ({'High Interest' if vol_ratio > 1.2 else 'Normal'})\n\n"
            f"3. **Price Action**:\n"
            f"   - Candle      : {candle_signal}\n"
            f"   - BB Pos      : {'Upper Band (Strong)' if price > last['BB_High'] else 'Lower Band (Weak)' if price < last['BB_Low'] else 'Middle Area'}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🧱 *TRADING PLAN (Intraday/Swing)*\n"
            f"🎯 Target Tech : {r1:,.0f} - {r1*1.02:,.0f}\n"
            f"🛡️ Stop Loss   : Under {s1:,.0f}\n"
            f"⚖️ Pivot Point : {pivot:,.0f}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 *AI NARRATIVE*:\n"
            f"\"Analisis multi-timeframe menunjukkan saham ini {'didominasi buyer' if score > 50 else 'dibawah tekanan seller'}. "
            f"Struktur tren {'Short-term Bullish' if price > last['MA20'] else 'Short-term Bearish'} dikonfirmasi oleh momentum {'positif' if last['MACD'] > last['MACD_Signal'] else 'negatif'}. "
            f"Level {s1:,.0f} adalah kunci pertahanan terakhir.\""
        )
        
        return summary, score # Return score for use elsewhere if needed, but signature assumes (summary, signal)
        # Wait, main.py expects (summary, signal). I better stick to returning signal string as second arg.
        return summary, signal_type

    except Exception as e:
        logger.error(f"Error analyzing {ticker}: {e}")
        return "⚠️ *Error*. Gagal melakukan analisa mendalam.", "ERROR"

def scan_bsjp_strategy(watchlist):
    """
    BSJP Logic (Unchanged from V16)
    """
    from data_fetcher import get_historical_data
    candidates = []
    
    for ticker in watchlist:
        try:
            df = get_historical_data(ticker, period="2mo")
            if df.empty or len(df) < 21: continue
            last_row = df.iloc[-1]
            prev_close = df.iloc[-2]['Close']
            change_pct = ((last_row['Close'] - prev_close) / prev_close) * 100
            
            if not (2.0 <= change_pct <= 15.0): continue
            
            ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
            if last_row['Close'] < ma20: continue
            
            avg_vol = df['Volume'].rolling(window=20).mean().iloc[-1]
            if last_row['Volume'] < (avg_vol * 1.2): continue
            
            if last_row['Close'] < (last_row['High'] * 0.97): continue
                
            candidates.append({
                "ticker": ticker,
                "price": last_row['Close'],
                "change": change_pct,
                "volume_ratio": last_row['Volume'] / avg_vol
            })
        except Exception: continue
            
    candidates.sort(key=lambda x: x['volume_ratio'], reverse=True)
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
    V22 HARMONY UPDATE: MOMENTUM ANCHORED PREDICTION
    Fixes the discrepancy where Strong Buy stocks get Bearish predictions due to lag.
    """
    try:
        # 1. Data Fetch (Still 1 Month for Sensitivity)
        df = get_historical_data(ticker, period="1mo")
        if df.empty or len(df) < 15:
            return "⚠️ *Prediction Failed*. Data saham tidak cukup."

        # 2. Key Metrics for Anchoring
        last_close = df['Close'].iloc[-1]
        
        # Calculate RSI for Momentum Context
        try:
            rsi_series = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
            current_rsi = rsi_series.iloc[-1]
        except:
            current_rsi = 50 # Default Neutral
            
        # 3. Model Prep
        df = df.reset_index()
        df['ordinal_date'] = df['Date'].apply(lambda x: x.toordinal())
        X = df[['ordinal_date']].values
        y = df['Close'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        # 4. Forecast
        last_date = df_raw = df['Date'].iloc[-1]
        future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, days+1)]
        future_ordinal = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)
        
        raw_pred = model.predict(future_ordinal)
        target_raw = raw_pred[-1]
        
        # 5. V22 HARMONY LOGIC: "MOMENTUM ANCHORING"
        # If Momentum is Bullish (RSI > 55), we shouldn't predict a crash unless structure breaks.
        # Linear Regression often drags price down to 'mean'.
        # We weigh the 'Last Price' heavily if momentum is strong.
        
        momentum_weight = 0.0
        if current_rsi > 60: momentum_weight = 0.7 # High Trust in Current Price
        elif current_rsi < 40: momentum_weight = 0.7 # High Trust in Current Drop
        else: momentum_weight = 0.3 # Trust the Mean Reversion more
        
        # Final Target = (TrendlineTarget * (1-Weight)) + (LastClose * Weight)
        # We project the LastClose taking the Slope into account too (Drift)
        
        slope = model.coef_[0]
        drift = slope * days
        projected_close = last_close + drift
        
        # Hybrid Target
        # If Bullish, bias towards Projected Close (Recent + Slope) rather than Raw Regression Line (Mean)
        if current_rsi > 55:
            target_main = max(target_raw, projected_close) # Take the higher path
        elif current_rsi < 45:
            target_main = min(target_raw, projected_close) # Take the lower path
        else:
            target_main = (target_raw + projected_close) / 2 # Balance
            
        # 6. Scenarios (Volatility Based)
        # Recalculate residuals based on this new target logic? No, keep simple std dev.
        preds = model.predict(X)
        std_dev = np.std(y - preds)
        
        target_best = target_main + (1.5 * std_dev)
        target_worst = target_main - (1.5 * std_dev)
        
        # 7. Formatting
        pot_main = ((target_main - last_close) / last_close) * 100
        
        if slope > 0:
            trend = "📈 UPTREND"
            bias = "Bias Bullish"
        else:
            trend = "📉 DOWNTREND"
            bias = "Bias Bearish"
            
        # Override Trend Label if RSI contradicts Slope
        if slope < 0 and current_rsi > 60:
            bias = "Reversal Bullish (Strong Momentum)"
        elif slope > 0 and current_rsi < 40:
            bias = "Reversal Bearish (Weak Momentum)"
            
        score = model.score(X, y) * 100
        prob = score if score < 95 else 95
        
        msg = (
            f"🔮 *NEXUS PROJECTION AI: {ticker}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 *EXECUTIVE FORECAST*\n"
            f"• *Target Utama* : Rp {target_main:,.0f} ({pot_main:+.1f}%)\n"
            f"• *Probabilitas* : {prob:.0f}%\n"
            f"• *Status*       : {trend} ({bias})\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 *SCENARIO MAPPING (7 Days)*\n"
            f"🟢 *Best Case*   : Rp {target_best:,.0f} (Optimis)\n"
            f"🔵 *Base Case*   : Rp {target_main:,.0f} (Wajar)\n"
            f"🔴 *Worst Case*  : Rp {target_worst:,.0f} (Pessimis)\n\n"
            f"⚙️ *MODEL INSIGHTS*:\n"
            f"• Volatility   : ±Rp {std_dev:,.0f}/hari\n"
            f"• RSI Impact   : {current_rsi:.1f} (Weighted)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 *AI CONCLUSION*:\n"
            f"\"Model V22 mengintegrasikan momentum RSI. Target disesuaikan dengan {'tekanan beli' if current_rsi > 50 else 'tekanan jual'} saat ini, "
            f"mengurangi bias regresi linear. Potensi arah {bias.lower()}.\""
        )
        
        return msg

    except Exception as e:
        logger.error(f"Prediction error for {ticker}: {e}")
        return "⚠️ *System Error*. Gagal melakukan prediksi."

def scan_whale_flow(watchlist):
    """
    V21 NEXUS FLOW: WHALE / BANDARMOLOGY SCANNER
    Detects:
    1. Silent Accumulation (Price Stable, Vol High)
    2. Golden Flow (Price Up, Vol Exploding)
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
            confidence = 0
            
            # Logic 1: Silent Accumulation (The dangerous one)
            # Price sideway (-1% to +2%) BUT Volume massive (> 2x)
            if (-1.0 <= price_change <= 2.0) and (vol_ratio > 2.0):
                signal = "SILENT ACCUMULATION 🤫"
                confidence = min(99, vol_ratio * 20) # 2x vol = 40%, 5x = 100%
                desc = "Harga stabil tapi volume meledak. Indikasi Smart Money entry diam-diam."
                
            # Logic 2: Golden Flow (Confirmation)
            # Price breakout (> 3%) AND Volume massive (> 2.5x)
            elif (price_change > 3.0) and (vol_ratio > 2.5):
                signal = "GOLDEN FLOW (WHALE ENTRY) 🐳"
                confidence = min(99, vol_ratio * 15 + price_change * 2)
                desc = "Ledakan volume disertai kenaikan harga signifikan."
                
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
