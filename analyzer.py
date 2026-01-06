import pandas as pd
import ta
import logging
from sklearn.linear_model import LinearRegression
import numpy as np
from data_fetcher import get_historical_data, get_stock_price

logger = logging.getLogger(__name__)

def analyze_stock(ticker):
    """
    V16 DEEP INTELLIGENCE ANALYSIS.
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
            recommendation = "Aggressive Entry. Trend is your friend."
        elif score >= 60: 
            signal_type = "BUY 🟢"
            recommendation = "Buy on Weakness (BoW). Cicil bertahap."
        elif score <= 20: 
            signal_type = "STRONG SELL 🩸"
            recommendation = "Exit immediately / Stay Cash."
        elif score <= 40: 
            signal_type = "SELL 🔴"
            recommendation = "Sell on Strength (SoS). Kurangi posisi."
        else: 
            signal_type = "NEUTRAL 🟡"
            recommendation = "Wait and See. Tunggu konfirmasi volume."
            
        # Construct Pivot Levels
        pivot = (last['High'] + last['Low'] + last['Close']) / 3
        r1 = (2 * pivot) - last['Low']
        s1 = (2 * pivot) - last['High']
        
        # Generate Text
        
        summary = (
            f"🧠 *NEXUS DEEP INTELLIGENCE: {ticker}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 *EXECUTIVE SUMMARY*\n"
            f"• **Signal**    : {signal_type}\n"
            f"• **Score**     : {score}/100 (Confidence Level)\n"
            f"• **Action**    : _{recommendation}_\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔬 *TECHNICAL DEEP DIVE*\n"
            f"1. **Trend Alignment**:\n"
            f"   - Short Term (MA20) : {'✅ Bullish' if price > last['MA20'] else '❌ Bearish'}\n"
            f"   - Mid Term (MA50)   : {'✅ Bullish' if pd.notna(last['MA50']) and price > last['MA50'] else '❌ Bearish' if pd.notna(last['MA50']) else '⚪ N/A'}\n"
            f"   - Long Term (MA200) : {'✅ Bullish' if pd.notna(last['MA200']) and price > last['MA200'] else '❌ Bearish' if pd.notna(last['MA200']) else '⚪ N/A'}\n\n"
            f"2. **Momentum & Flow**:\n"
            f"   - RSI (14)    : {rsi:.1f} ({'Overbought' if rsi>70 else 'Oversold' if rsi<30 else 'Neutral'})\n"
            f"   - Stochastic  : K={last['Stoch_K']:.1f} | D={last['Stoch_D']:.1f}\n"
            f"   - MACD        : {'Golden Cross ↗️' if last['MACD'] > last['MACD_Signal'] else 'Dead Cross ↘️'} (Hist: {last['MACD_Hist']:.2f})\n"
            f"   - Volume      : {vol_ratio:.1f}x Avg ({'High Interest' if vol_ratio > 1.2 else 'Normal'})\n\n"
            f"3. **Price Action**:\n"
            f"   - Candle      : {candle_signal}\n"
            f"   - Posisi BB   : {'Upper Band (Strong)' if price > last['BB_High'] else 'Lower Band (Weak)' if price < last['BB_Low'] else 'Middle Area'}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🧱 *TRADING PLAN (Intraday/Swing)*\n"
            f"🎯 Target Tech : {r1:,.0f} - {r1*1.02:,.0f}\n"
            f"🛡️ Stop Loss   : Under {s1:,.0f}\n"
            f"⚖️ Pivot Point : {pivot:,.0f}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 *AI NARRATIVE*:\n"
            f"\"Saham ini secara teknikal menunjukkan {'dominasi buyer' if score > 50 else 'tekanan seller'}. "
            f"Indikator {'RSI mendukung potensi upside' if rsi < 60 and score > 50 else 'MACD mengonfirmasi momentum' if last['MACD'] > last['MACD_Signal'] else 'sedang konsolidasi'}. "
            f"Perhatikan level {s1:,.0f} sebagai area support krusial.\""
        )
        
        return summary, signal_type

    except Exception as e:
        logger.error(f"Error analyzing {ticker}: {e}")
        return "⚠️ *Error*. Gagal melakukan analisa mendalam.", "ERROR"

def scan_bsjp_strategy(watchlist):
    """
    Screens for 'Beli Sore Jual Pagi' (BSJP) candidates.
    Criteria:
    1. Uptrend (Price > MA20)
    2. Strong Momentum (Gain > 2% but < 10%)
    3. High Volume (> 1.2x Avg Vol 20)
    4. Strong Close (Close near High, upper wick < 30% of body)
    """
    from data_fetcher import get_historical_data # Import here to avoid circular if using threading later
    
    candidates = []
    
    for ticker in watchlist:
        try:
            # We need history for MA and Avg Volume
            df = get_historical_data(ticker, period="2mo")
            if df.empty or len(df) < 21:
                continue
                
            last_row = df.iloc[-1]
            
            # 1. Gain Check
            prev_close = df.iloc[-2]['Close']
            change_pct = ((last_row['Close'] - prev_close) / prev_close) * 100
            
            if not (2.0 <= change_pct <= 15.0):
                continue
                
            # 2. Uptrend Check (Price > MA20)
            ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
            if last_row['Close'] < ma20:
                continue
                
            # 3. Volume Check
            avg_vol = df['Volume'].rolling(window=20).mean().iloc[-1]
            if last_row['Volume'] < (avg_vol * 1.2):
                continue
            
            # 4. Strong Close (Upper wick small)
            # Upper wick = High - Max(Open, Close)
            # We want Close to be very close to High.
            # Safe threshold: Close > High * 0.97
            if last_row['Close'] < (last_row['High'] * 0.97):
                continue
                
            candidates.append({
                "ticker": ticker,
                "price": last_row['Close'],
                "change": change_pct,
                "volume_ratio": last_row['Volume'] / avg_vol
            })
            
        except Exception as e:
            continue
            
    # Sort by strongest volume relative to avg
    candidates.sort(key=lambda x: x['volume_ratio'], reverse=True)
    return candidates

def scan_market_screener(watchlist):
    """
    Scans for the /screener command.
    Returns list of dicts: Ticker, Price, Potential%, BSJP Score, Bandar Status.
    """
    results = []
    
    # We reuse get_historical_data but need to be careful with rate limits if list is huge.
    # Assuming watchlist is ~50-70 stocks.
    
    for ticker in watchlist:
        try:
            df = get_historical_data(ticker, period="1mo")
            if df.empty or len(df) < 20: continue
            
            last = df.iloc[-1]
            prev = df.iloc[-2]
            
            # 1. Potential (Upside to Resistance)
            pivot = (last['High'] + last['Low'] + last['Close']) / 3
            r1 = (2 * pivot) - last['Low']
            potential_upside = ((r1 - last['Close']) / last['Close']) * 100
            
            # 2. BSJP Safe Score (Volatility & Trend)
            # Safe if Uptrend AND Low Volatility on Close
            ma20 = df['Close'].rolling(20).mean().iloc[-1]
            is_uptrend = last['Close'] > ma20
            body_size = abs(last['Close'] - last['Open']) / last['Open']
            is_stable = body_size < 0.03 # Candle body < 3%
            
            bsjp_status = "AMAN ✅" if (is_uptrend and is_stable) else "RISK ⚠️"
            
            # 3. Bandar / Akumulasi Proxy
            # Logic: High Volume + Price Up = Accumulation
            # Low Volume + Price Down = Distribution (Weak)
            # High Volume + Price Down = Distribution (Strong)
            
            avg_vol = df['Volume'].rolling(20).mean().iloc[-1]
            vol_ratio = last['Volume'] / avg_vol
            
            if vol_ratio > 1.5 and last['Close'] > prev['Close']:
                bandar_sts = "AKUM 🐳"
            elif vol_ratio > 1.5 and last['Close'] < prev['Close']:
                bandar_sts = "DIST 🔻"
            elif vol_ratio < 0.8:
                bandar_sts = "SEPI 💤"
            else:
                bandar_sts = "NORMAL"
                
            results.append({
                "ticker": ticker,
                "price": last['Close'],
                "potential": potential_upside,
                "bsjp": bsjp_status,
                "bandar": bandar_sts,
                "date": last.name.strftime('%d-%m')
            })
            
        except Exception:
            continue
            
    # Sort by best potential
    results.sort(key=lambda x: x['potential'], reverse=True)
    return results

def predict_future_price(ticker, days=7):
    """
    Advanced Linear Regression + Volatility Channel Prediction.
    Uses 1-month data for sensitive momentum tracking.
    """
    try:
        # 1. Fetch Data (Short Term Momentum - 1 Month)
        # Using shorter timeframe makes it more "accurate" for trading trends.
        df = get_historical_data(ticker, period="1mo")
        if df.empty or len(df) < 15:
            return "⚠️ *Prediction Failed*. Data saham tidak cukup (IPO baru/Suspend)."

        # 2. Prepare Data
        df = df.reset_index()
        df['ordinal_date'] = df['Date'].apply(lambda x: x.toordinal())
        
        X = df[['ordinal_date']].values
        y = df['Close'].values
        
        # 3. Model Training
        model = LinearRegression()
        model.fit(X, y)
        
        # 4. Metrics & Volatility
        score = model.score(X, y) * 100
        slope = model.coef_[0]
        
        # Calculate Volatility (Standard Deviation of Residuals)
        predictions_historical = model.predict(X)
        residuals = y - predictions_historical
        volatility = np.std(residuals)
        
        # 5. Future Projection
        last_date = df['Date'].iloc[-1]
        future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, days+1)]
        future_ordinal = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)
        
        future_pred = model.predict(future_ordinal)
        target_price = future_pred[-1]
        
        # Volatility Bands (Probabilistic Range)
        target_high = target_price + volatility
        target_low = target_price - volatility
        
        current_price = y[-1]
        potential = ((target_price - current_price) / current_price) * 100
        
        # 6. Smart Explanation Logic
        if score > 70: quality = "Sangat Kuat (High Confidence)"
        elif score > 50: quality = "Moderat"
        else: quality = "Lemah (Volatile/Sideways)"
        
        if slope > 0:
            trend_idx = "📈 UPTREND"
            advice = "Momentum positif. Potensi lanjut naik."
        else:
            trend_idx = "📉 DOWNTREND"
            advice = "Tekanan jual dominan. Hati-hati."
            
        # 7. Construct Output
        msg = (
            f"🔮 *NEXUS PROJECTION AI: {ticker}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 *TARGET HARGA (7 Hari)*\n"
            f"🔹 *Rp {target_price:,.0f}* ({potential:+.2f}%)\n"
            f"⚠️ _Range Wajar: {target_low:,.0f} - {target_high:,.0f}_\n\n"
            f"⚙️ *ANALISIS MODEL*:\n"
            f"• Tren Base  : {trend_idx}\n"
            f"• Kekuatan   : {quality} (R² {score:.0f}%)\n"
            f"• Volatilitas: ±Rp {volatility:,.0f}/hari\n\n"
            f"📝 *KESIMPULAN AI*:\n"
            f"\"{advice} Berdasarkan regresi linear momentum 30 hari terakhir. Harga bergerak dalam channel standar deviasi normal.\"\n\n"
            f"📅 *PREDIKSI HARIAN*:"
        )
        
        # Limit to 3 days detailed to save space, or show all 7 compact
        rows = []
        for i, val in enumerate(future_pred):
            day_label = f"H+{i+1}"
            rows.append(f"• {day_label}: Rp {val:,.0f}")
            
        msg += "\n" + "\n".join(rows)
        msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n💡 _Disclaimer: Prediksi statistik, bukan kepastian masa depan._"
        
        return msg

    except Exception as e:
        logger.error(f"Prediction error for {ticker}: {e}")
        return "⚠️ *System Error*. Gagal melakukan prediksi."
