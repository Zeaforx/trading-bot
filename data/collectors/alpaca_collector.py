from datetime import datetime, timedelta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from config.settings import settings

class AlpacaCollector:
    def __init__(self):
        # 1. Data Client: Handles fetching candles/bars
        self.data_client = StockHistoricalDataClient(
            settings.ALPACA_API_KEY,
            settings.ALPACA_SECRET_KEY
        )
        
        # 2. Trading Client: Handles Account info and Clock
        self.trading_client = TradingClient(
            settings.ALPACA_API_KEY,
            settings.ALPACA_SECRET_KEY,
            paper=settings.ALPACA_PAPER
        )
    
    def fetch_latest_bars(self, symbols, limit=100):
        """
        Fetches the latest N bars for a list of symbols.
        Uses a sliding window (Now - N minutes) to ensure data is fresh.
        """
        # Calculate 'start' time to force fresh data (Sliding Window logic)
        # We ask for 2x the limit in minutes to account for gaps/holidays
        time_ago = datetime.utcnow() - timedelta(minutes=limit*2)
        
        # Build the Request Object (Required by new SDK)
        request_params = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=TimeFrame.Minute,
            limit=limit,
            start=time_ago
        )
        
        # Returns a Multi-Index DataFrame
        return self.data_client.get_stock_bars(request_params).df
    
    def get_current_price(self, symbol):
        """
        Gets the very latest close price for a single symbol.
        Useful for execution logic.
        """
        try:
            # Fetch just the last 2 minutes to get the most recent bar
            df = self.fetch_latest_bars([symbol], limit=2)
            
            if not df.empty:
                return float(df.iloc[-1]['close'])
            return 0.0
            
        except Exception as e:
            print(f"Error getting price for {symbol}: {e}")
            return 0.0

    def get_clock(self):
        """Helper to get market clock (Open/Closed status)"""
        return self.trading_client.get_clock()