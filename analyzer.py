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
