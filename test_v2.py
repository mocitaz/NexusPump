import logging
import asyncio
from chart_generator import generate_chart
from analyzer import analyze_stock
from news_fetcher import get_stock_news, format_news_message
from alerts import StockMonitor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_v2_features():
    ticker = "BBCA"
    
    print(f"--- Testing V2 Features for {ticker} ---")
    
    # 1. Test Premium Chart
    print("\n[1] Testing Premium Chart Generator...")
    try:
        buf = generate_chart(ticker, period="3mo")
        if buf:
            print("✅ Chart generated successfully (Buffer size: {} bytes)".format(buf.getbuffer().nbytes))
        else:
            print("❌ Chart generation returned None")
    except Exception as e:
        print(f"❌ Chart Error: {e}")

    # 2. Test Smart Analysis
    print("\n[2] Testing Smart Analyzer (Pivot & Patterns)...")
    try:
        summary, signal = analyze_stock(ticker)
        print(f"✅ Analysis Result ({signal}):")
        print(summary[:150] + "...") # Print first 150 chars
    except Exception as e:
        print(f"❌ Analysis Error: {e}")

    # 3. Test News Fetcher
    print("\n[3] Testing News Fetcher...")
    try:
        items = get_stock_news(ticker)
        msg = format_news_message(ticker, items)
        print(f"✅ News Result ({len(items)} items):")
        print(msg)
    except Exception as e:
        print(f"❌ News Error: {e}")
        
    # 4. Test Alert Logic (Simulation)
    print("\n[4] Testing Smart Alert Logic...")
    monitor = StockMonitor(watchlist=[ticker])
    # Mocking data is hard here without modifying code, so we just run scan_market
    # expecting it not to crash.
    try:
        alerts = await monitor.scan_market()
        print(f"✅ Scan completed. Alerts found: {len(alerts)}")
        if alerts:
            print(alerts[0])
    except Exception as e:
        print(f"❌ Alert Scan Error: {e}")

    # 5. Test BSJP Strategy
    print("\n[5] Testing BSJP Strategy (Sample)...")
    try:
        from analyzer import scan_bsjp_strategy
        # Test with a small list including our test ticker
        candidates = scan_bsjp_strategy([ticker, "TLKM", "GOTO"]) 
        print(f"✅ BSJP Scan completed. Candidates found: {len(candidates)}")
        if candidates:
            print(candidates[0])
    except Exception as e:
        print(f"❌ BSJP Error: {e}")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(test_v2_features())
