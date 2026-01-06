import pandas as pd
import logging
from data_fetcher import get_historical_data

logger = logging.getLogger(__name__)

def calculate_bsjp_winrate(ticker, period="3mo"):
    """
    Backtests the BSJP strategy on historical data.
    Strategy:
    - BUY: If Price > MA20 AND Volume > MA20_Volume (Strong Momentum)
    - SELL: Next Day's High.
    - WIN: If Next High > Buy Price (even by 1%).
    
    Returns: Dict {win_rate, trades, avg_gain}
    """
    try:
        # 1. Fetch Data
        df = get_historical_data(ticker, period=period)
        if df.empty or len(df) < 25:
            return None
            
        # 2. Calculate Indicators
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['VolMA20'] = df['Volume'].rolling(window=20).mean()
        
        trades = 0
        wins = 0
        total_gain = 0
        
        # 3. Simulate
        # Iterate until 2nd to last day (since we need "Next Day" to check result)
        for i in range(20, len(df) - 1):
            today = df.iloc[i]
            tomorrow = df.iloc[i+1]
            
            # BSJP Condition:
            # 1. Close > MA20 (Uptrend)
            # 2. Volume > VolMA20 (Accumulation)
            # 3. Candle is Green (Close > Open) - Optional but good for BSJP
            
            if (today['Close'] > today['MA20'] and 
                today['Volume'] > today['VolMA20'] and 
                today['Close'] > today['Open']):
                
                trades += 1
                buy_price = today['Close']
                sell_price = tomorrow['High'] # Potential Sell Price
                
                # Did we win?
                if sell_price > buy_price * 1.01: # At least 1% potential gain
                    wins += 1
                    gain = (sell_price - buy_price) / buy_price * 100
                    total_gain += gain
                else:
                    # If high didn't reach target, assume we sold at Close (Loss or Breakeven)
                    change = (tomorrow['Close'] - buy_price) / buy_price * 100
                    total_gain += change

        if trades == 0:
            return {'win_rate': 0, 'trades': 0, 'avg_gain': 0}
            
        win_rate = (wins / trades) * 100
        avg_gain = total_gain / trades
        
        return {
            'win_rate': win_rate,
            'trades': trades,
            'avg_gain': avg_gain
        }
        
    except Exception as e:
        logger.error(f"Backtest error for {ticker}: {e}")
        return None
