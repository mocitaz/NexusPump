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
        if score >= 75: signal_type = "STRONG BUY"
        elif score >= 60: signal_type = "BUY"
        elif score <= 25: signal_type = "STRONG SELL"
        elif score <= 40: signal_type = "SELL"
        else: signal_type = "NEUTRAL"
        
        # Formatting Output with "Professional Card" style
        # Explanation logic
        rsi_desc = "Jenuh Jual (Potensi Naik)" if rsi_val < 30 else "Jenuh Beli (Potensi Turun)" if rsi_val > 70 else "Normal (Stabil)"
        macd_desc = "Momentum Bullish" if last_row['macd'] > last_row['macd_signal'] else "Momentum Bearish"
        
        summary = (
            f"🏢 *Laporan Analisis Teknikal: {ticker}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💵 *Harga Terkini*: Rp {current_price:,.0f}\n\n"
            f"🧠 *Kesimpulan AI*:\n"
            f"👉 Status: *{signal_type}* (Keyakinan: {score}%)\n"
            f"_Sistem mendeteksi momentum {macd_desc.lower()} dengan kondisi RSI yang {rsi_desc.lower()}._\n\n"
            f"📐 *Level Penting (Pivot Points)*:\n"
            f"🔴 Resistance (R1): {r1:,.0f}\n"
            f"🔵 Support (S1): {s1:,.0f}\n"
            f"⚪ Pivot Tengah: {pivot:,.0f}\n\n"
            f"📊 *Indikator Utama*:\n"
            f"• RSI (14): {rsi_val:.1f} → _{rsi_desc}_\n"
            f"• MACD: {last_row['macd']:.2f} / Signal: {last_row['macd_signal']:.2f}\n"
            f"• Pola Candle: {', '.join(patterns) if patterns else 'Tidak ada pola spesifik'}\n\n"
            f"💡 *Saran Profesional*:\n"
            f"{'Pantau area Support S1 untuk entry terbaik.' if score > 50 else 'Waspada jika harga tembus Support S1.'} "
            f"Tetap disiplin dengan Stop Loss."
        )
        
        return summary, signal_type

    except Exception as e:
        logger.error(f"Error analyzing {ticker}: {e}")
        return "Terjadi kesalahan saat analisis.", "ERROR"

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
    Simple Linear Regression prediction for the next N days.
    """
    try:
        df = get_historical_data(ticker, period="3mo")
        if df.empty or len(df) < 20:
            return "Data tidak cukup untuk prediksi."

        # Prepare data for regression
        df = df.reset_index()
        df['ordinal_date'] = df['Date'].apply(lambda x: x.toordinal())
        
        X = df[['ordinal_date']].values
        y = df['Close'].values
        
        score = model.score(X, y) * 100 # R-Squared confidence
        slope = model.coef_[0]
        
        # Determine trend description
        if slope > 10: trend_desc = "Tren Sangat Positif (Bullish Kuat)"
        elif slope > 0: trend_desc = "Tren Cenderung Naik (Bullish)"
        elif slope > -10: trend_desc = "Tren Cenderung Turun (Bearish)"
        else: trend_desc = "Tren Sangat Negatif (Bearish Kuat)"
        
        # Predict next 'days'
        last_date = df['Date'].iloc[-1]
        future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, days+1)]
        future_ordinal = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)
        
        predictions = model.predict(future_ordinal)
        target_price = predictions[-1]
        current_price = y[-1]
        potential = ((target_price - current_price) / current_price) * 100
        
        emoji_trend = "📈" if slope > 0 else "📉"
        
        msg = (
            f"🔮 *Prediksi Harga Saham Professional: {ticker}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 *Target 7 Hari*: Rp {target_price:,.0f} ({potential:+.2f}%)\n"
            f"⚙️ *Akurasi Model*: {score:.1f}%\n"
            f"📊 *Status Tren*: {trend_desc} {emoji_trend}\n\n"
            f"📝 *Analisis & Alasan*:\n"
            f"Berdasarkan data historis 3 bulan terakhir, pergerakan harga membentuk pola regresi dengan kemiringan {slope:.2f}. "
            f"Model memproyeksikan {'kenaikan' if potential > 0 else 'penurunan'} lanjutan ke level Rp {target_price:,.0f} dalam sepekan kedepan.\n\n"
            f"📅 *Rincian Hari ke Hari*:\n"
        )
        
        for i, val in enumerate(predictions):
            msg += f"• H+{i+1}: Rp {val:,.0f}\n"
            
        msg += "\n💡 _Disclaimer: Prediksi berdasarkan probabilitas statistik. Tetap gunakan manajemen risiko terbaik._"
        return msg

    except Exception as e:
        logger.error(f"Prediction error for {ticker}: {e}")
        return "⚠️ Maaf, terjadi kesalahan saat melakukan kalkulasi prediksi. Data saham mungkin tidak mencukupi."
