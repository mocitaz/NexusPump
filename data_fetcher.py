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

def get_batch_historical_data(tickers, period="1mo", interval="1d"):
    """
    Fetches historical data for MULTIPLE tickers efficiently.
    Returns: Dict {ticker: DataFrame}
    """
    try:
        # 1. Format Tickers
        sa_tickers = []
        for t in tickers:
             if not t.endswith(".JK") and not t.endswith(".jk"):
                 sa_tickers.append(f"{t}.JK")
             else:
                 sa_tickers.append(t)
        
        if not sa_tickers: return {}

        # 2. Bulk Download
        # threads=True uses multi-threading
        # group_by='ticker' makes it easier to iterate: data['BBCA.JK'] -> DF
        logger.info(f"Batch downloading {len(sa_tickers)} stocks...")
        data = yf.download(sa_tickers, period=period, interval=interval, group_by='ticker', threads=True, progress=False)
        
        result = {}
        for t_orig, t_sa in zip(tickers, sa_tickers):
            # Extract DF for this ticker
            # Note: If only 1 ticker is downloaded, structure is different (just DF), but we expect list usage.
            # yfinance > 0.2: if multi tickers, columns are MultiIndex if not group_by='ticker'
            # With group_by='ticker':
            try:
                if len(sa_tickers) == 1:
                    df = data
                else:
                    df = data[t_sa]
                
                # Check emptiness
                if not df.empty:
                    result[t_orig.upper()] = df
            except KeyError:
                continue
                
        return result

    except Exception as e:
        logger.error(f"Batch download error: {e}")
        return {}

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
    Fetches top gainers and losers using batch optimized yfinance download.
    Reduces latency from ~30s to ~2s.
    """
    # 1. Prepare Tickers
    tickers_idx = [f"{t}.JK" if not t.endswith(".JK") else t for t in IDX_WATCHLIST]
    
    try:
        # 2. Batch Download (5 days to ensure we have Last and Prev Close)
        # Disable threads to prevent deadlock/hanging. Yahoo API is fast enough for 70 tickers.
        df = yf.download(tickers_idx, period="5d", interval="1d", group_by='column', progress=False, threads=False, actions=False)
        
        if df.empty: return [], []
        
        # Access 'Close' data
        # Depending on yfinance version, structure varies. 
        # Standard: df['Close'] -> Columns are Tickers
        
        # Handle case where MultiIndex might be returned differently
        if 'Close' not in df.columns and isinstance(df.columns, pd.MultiIndex):
             # Try to see if levels are swapped? usually it is (Price, Ticker)
             # But let's assume standard 'Close' key exists or we can extract it
             pass

        closes = df['Close']
        res_data = []
        
        for t in tickers_idx:
            try:
                # Extract series
                if t in closes:
                    series = closes[t]
                else:
                    continue
                    
                series = series.dropna()
                if len(series) < 2: continue
                
                last = series.iloc[-1]
                prev = series.iloc[-2]
                
                if prev == 0: continue
                
                change_pct = ((last - prev) / prev) * 100
                
                res_data.append({
                    'ticker': t.replace(".JK", ""),
                    'price': last,
                    'change_pct': change_pct
                })
            except Exception: continue
            
        # 3. Sort
        final_df = pd.DataFrame(res_data)
        if final_df.empty: return [], []
        
        final_df = final_df.sort_values(by="change_pct", ascending=False)
        
        gainers = final_df.head(5).to_dict(orient="records")
        losers = final_df.tail(5).sort_values(by="change_pct", ascending=True).to_dict(orient="records")
        
        return gainers, losers
        
    except Exception as e:
        logger.error(f"Error in batch scan gainers/losers: {e}")
        return [], []

def get_stock_fundamentals(ticker):
    """
    Fetches fundamental data (Investor View).
    (PER, PBV, ROE, MarketCap, DividendYield).
    Note: 'info' request is slower than fast_info.
    """
    try:
        if not ticker.endswith(".JK") and not ticker.endswith(".jk"):
            ticker = f"{ticker}.JK"
            
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Extract safe values
        data = {
            "pe_ratio": info.get("trailingPE", 0),
            "pbv_ratio": info.get("priceToBook", 0),
            "roe": info.get("returnOnEquity", 0),
            "market_cap": info.get("marketCap", 0),
            "dividend_yield": info.get("dividendYield", 0),
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "-"),
            "currency": info.get("currency", "IDR")
        }
        return data
    except Exception as e:
        logger.error(f"Error fetching fundamentals for {ticker}: {e}")
        return None
