import json
import os
import logging
from datetime import datetime

# File to store user portfolios
PORTO_FILE = "user_portfolios.json"

logger = logging.getLogger(__name__)

class PortfolioManager:
    def __init__(self):
        self.file_path = PORTO_FILE
        self.data = self._load_data()

    def _load_data(self):
        if not os.path.exists(self.file_path):
            return {}
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load portfolio: {e}")
            return {}

    def _save_data(self):
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save portfolio: {e}")

    def buy_stock(self, user_id, ticker, price, lots):
        """
        Record a BUY transaction. Updates Avg Price.
        """
        user_id = str(user_id)
        ticker = ticker.upper()
        
        if user_id not in self.data:
            self.data[user_id] = {"holdings": {}}
            
        holdings = self.data[user_id]["holdings"]
        
        if ticker in holdings:
            # Average Down/Up Logic
            current = holdings[ticker]
            total_cost = (current['avg_price'] * current['lots']) + (price * lots)
            total_lots = current['lots'] + lots
            new_avg = total_cost / total_lots
            
            holdings[ticker] = {
                "avg_price": new_avg,
                "lots": total_lots
            }
        else:
            # New Position
            holdings[ticker] = {
                "avg_price": price,
                "lots": lots
            }
            
        self._save_data()
        return self.data[user_id]["holdings"][ticker]

    def sell_stock(self, user_id, ticker, lots):
        """
        Record a SELL transaction. Reduces lots. 
        Does NOT change Avg Price (FIFO/Avg logic usually keeps avg price same until position closed).
        Returns Remaining Lots.
        """
        user_id = str(user_id)
        ticker = ticker.upper()
        
        if user_id not in self.data or ticker not in self.data[user_id]["holdings"]:
            return -1 # Not found
            
        holding = self.data[user_id]["holdings"][ticker]
        
        if holding['lots'] < lots:
            return -2 # Not enough lots
            
        holding['lots'] -= lots
        
        if holding['lots'] == 0:
            del self.data[user_id]["holdings"][ticker]
        
        self._save_data()
        
        # Return remaining lots (or 0 if deleted)
        return holding['lots'] if ticker in self.data[user_id]["holdings"] else 0

    def get_portfolio(self, user_id):
        """
        Get user holdings.
        """
        user_id = str(user_id)
        return self.data.get(user_id, {}).get("holdings", {})

    def reset_portfolio(self, user_id):
        user_id = str(user_id)
        if user_id in self.data:
            del self.data[user_id]
            self._save_data()
            return True
        return False
