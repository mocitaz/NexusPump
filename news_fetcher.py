import feedparser
import logging
import urllib.parse

logger = logging.getLogger(__name__)

def get_stock_news(ticker):
    """
    Fetches latest 3 news from Google News RSS for the given ticker.
    """
    try:
        # Use a more specific query
        query = f"Saham {ticker} Indonesia"
        encoded_query = urllib.parse.quote(query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=id-ID&gl=ID&ceid=ID:id"
        
        feed = feedparser.parse(rss_url)
        
        if not feed.entries:
            return []
            
        news_items = []
        for entry in feed.entries[:3]:
            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.published
            })
            
        return news_items
    except Exception as e:
        logger.error(f"Error fetching news for {ticker}: {e}")
        return []

def format_news_message(ticker, news_items):
    if not news_items:
        return f"📰 Tidak ada berita terbaru untuk {ticker}."
        
    msg = f"📰 *Berita Terkini: {ticker}*\n\n"
    for item in news_items:
        msg += f"• [{item['title']}]({item['link']})\n"
        # msg += f"  _{item['published']}_\n" # Optional date
        
    msg += "\n_Sumber: Google News_"
    return msg
