import yfinance as yf
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def get_stock_price(ticker):
    """
    Fetches the current price, change %, high, low, and volume for a ticker.
    """
    try:
        # Ensure ticker has .JK suffix if not present (assuming IDX)
        if not ticker.endswith(".JK") and not ticker.endswith(".jk"):
            ticker = f"{ticker}.JK"
        
        stock = yf.Ticker(ticker)
        # fast_info is often faster for current price
        info = stock.fast_info
        
        last_price = info.last_price
        prev_close = info.previous_close
        
        if last_price is None or prev_close is None:
            # Fallback to history if fast_info fails (sometimes happens on weak connections)
            hist = stock.history(period="1d")
            if hist.empty:
                return None
            last_price = hist["Close"].iloc[-1]
            prev_close = stock.info.get("previousClose", last_price) # Fallback

        change = last_price - prev_close
        change_pct = (change / prev_close) * 100
        
        # Get day's range and volume from history for accuracy (fast_info doesn't always have dayHigh/Low accurate during session)
        hist_today = stock.history(period="1d")
        if not hist_today.empty:
            high = hist_today["High"].iloc[-1]
            low = hist_today["Low"].iloc[-1]
            volume = hist_today["Volume"].iloc[-1]
        else:
            high = last_price
            low = last_price
            volume = 0

        return {
            "ticker": ticker.upper(),
            "price": last_price,
            "change": change,
            "change_pct": change_pct,
            "high": high,
            "low": low,
            "volume": volume
        }
    except Exception as e:
        logger.error(f"Error fetching price for {ticker}: {e}")
        return None

def get_historical_data(ticker, period="1mo", interval="1d"):
    """
    Fetches historical data for charting and analysis.
    """
    try:
        if not ticker.endswith(".JK") and not ticker.endswith(".jk"):
            ticker = f"{ticker}.JK"
        
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval=interval)
        return hist
    except Exception as e:
        logger.error(f"Error fetching history for {ticker}: {e}")
        return pd.DataFrame()

from idx_tickers import IDX_WATCHLIST

def get_top_gainers_losers_idx():
    """
    Fetches top gainers and losers from the expanded IDX Watchlist.
    """
    data = []
    # Limit scanning to top 50 to avoid massive delay on user command
    # Or scan all but warn user it takes time. 
    # Let's scan all IDX_WATCHLIST (~60 stocks) - it might take 10-20s on free API
    # Optimization: Use ThreadPool if needed, but for simplicity loop is safer for rate limits.
    
    for symbol in IDX_WATCHLIST:
        res = get_stock_price(symbol)
        if res:
            data.append(res)
    
    df = pd.DataFrame(data)
    if df.empty:
        return [], []
        
    df = df.sort_values(by="change_pct", ascending=False)
    
    gainers = df.head(5).to_dict(orient="records")
    losers = df.tail(5).sort_values(by="change_pct", ascending=True).to_dict(orient="records")
    
    return gainers, losers
