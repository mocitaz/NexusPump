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
        
        # Formatting Output with "Cards" style
        summary = (
            f"📊 *Analisis Teknikal Premium: {ticker}*\n"
            f"Harga: {current_price:,.0f}\n\n"
            f"🧠 *Signal AI*: _{signal_type}_ (Score: {score}/100)\n\n"
            f"📐 *Key Levels (Pivot)*:\n"
            f"• R1: {r1:,.0f}\n"
            f"• Pivot: {pivot:,.0f}\n"
            f"• S1: {s1:,.0f}\n\n"
            f"📈 *Indikator*:\n"
            f"• RSI(14): {rsi_val:.2f}\n"
            f"• MACD: {last_row['macd']:.2f}\n\n"
            f"🕯 *Pola Candle*:\n"
            f"{', '.join(patterns) if patterns else '-'}\n\n"
            f"⚡ *Catatan*:\n"
            f"{' • '.join(signals) if signals else 'Tidak ada trigger khusus.'}"
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
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Predict next 'days'
        last_date = df['Date'].iloc[-1]
        future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, days+1)]
        future_ordinal = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)
        
        predictions = model.predict(future_ordinal)
        
        msg = f"🔮 *Prediksi Harga (Linear Regression) - {days} hari ke depan*:\n"
        for i, val in enumerate(predictions):
            msg += f"+ {i+1} hari: Rp {val:,.0f}\n"
            
        msg += "\n_Disclaimer: Prediksi ini menggunakan model statistik sederhana dan bukan saran keuangan._"
        return msg

    except Exception as e:
        logger.error(f"Prediction error for {ticker}: {e}")
        return "Gagal melakukan prediksi."
