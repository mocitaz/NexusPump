import yfinance as yf
import pandas as pd
import logging
import datetime

logger = logging.getLogger(__name__)

def get_stock_price(ticker, detailed=False):
    """
    Fetches price + fundamentals. 
    detailed=True: Fetches 1m interval for exact Last Trade Time (Slower).
    """
    try:
        if not ticker.endswith(".JK") and not ticker.endswith(".jk"):
            ticker = f"{ticker}.JK"
        
        stock = yf.Ticker(ticker)
        
        # 1. Fast Info (Price)
        info = stock.fast_info
        last_price = info.last_price
        prev_close = info.previous_close
        
        if last_price is None:
            # Fallback
            hist = stock.history(period="1d")
            if hist.empty: return None
            last_price = hist["Close"].iloc[-1]
            prev_close = stock.info.get("previousClose", last_price)

        change = last_price - prev_close
        change_pct = (change / prev_close) * 100
        
        # 2. Fundamentals (Lazy load from stock.info if needed, but fast_info is limited)
        # We need stock.info for mcap/sector usually.
        # Optimized: Only fetch if critical? No, /harga needs it.
        # But stock.info is slow.
        # Let's try to get what we can.
        
        # Note: stock.info triggers a request
        base_info = stock.info
        
        long_name = base_info.get('longName', ticker)
        sector = base_info.get('sector', 'Unknown')
        market_cap = base_info.get('marketCap', 0)
        pe_ratio = base_info.get('trailingPE', None)
        
        # 3. Detailed Mode (Time & Volume)
        last_updated_str = "N/A"
        
        if detailed:
            hist_intraday = stock.history(period="1d", interval="1m")
            if not hist_intraday.empty:
                high = hist_intraday["High"].max()
                low = hist_intraday["Low"].min()
                volume = hist_intraday["Volume"].sum()
                last_ts = hist_intraday.index[-1]
                last_updated_str = last_ts.strftime('%H:%M')
            else:
                high = info.day_high if info.day_high else last_price
                low = info.day_low if info.day_low else last_price
                volume = info.last_volume
                last_updated_str = "End of Day"
        else:
            # Fast Mode
            high = info.day_high if info.day_high else last_price
            low = info.day_low if info.day_low else last_price
            volume = info.last_volume
            last_updated_str = "End of Day"

        return {
            "ticker": ticker.upper(),
            "price": last_price,
            "change": change,
            "change_pct": change_pct,
            "high": high,
            "low": low,
            "volume": volume,
            "last_updated": last_updated_str,
            "long_name": long_name,
            "sector": sector,
            "market_cap": market_cap,
            "pe_ratio": pe_ratio
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

def get_stock_news(ticker):
    """
    Fetches latest news for the stock using yfinance.
    Returns list of dicts: title, link, publisher, published.
    """
    try:
        if not ticker.endswith(".JK") and not ticker.endswith(".jk"):
            ticker = f"{ticker}.JK"
            
        stock = yf.Ticker(ticker)
        news_items = stock.news
        
        results = []
        for item in news_items:
            # Calculate readable time
            ts = item.get('providerPublishTime', 0)
            dt = datetime.datetime.fromtimestamp(ts)
            time_str = dt.strftime('%d %b %H:%M')
            
            results.append({
                'title': item.get('title', 'No Title'),
                'link': item.get('link', '#'),
                'source': item.get('publisher', 'Unknown'),
                'published': time_str
            })
            
        return results
    except Exception as e:
        logger.error(f"Error fetching news for {ticker}: {e}")
        return []

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
