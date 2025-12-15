import alpaca_trade_api as tradeapi
from datetime import datetime, timedelta
from config.settings import settings


class AlpacaCollector:
    def __init__(self):
        # SDK Initialization
        self.api = tradeapi.REST(
            settings.ALPACA_API_KEY,
            settings.ALPACA_SECRET_KEY,
            settings.ALPACA_BASE_URL,
        )

    def fetch_latest_bars(self, symbols, limit=100):
        # FIX: Set the start time to (Now - 200 minutes)
        # We ask for a bit more than 'limit' (e.g. 200 mins for 100 bars)
        # to account for small gaps in data.
        time_ago = datetime.utcnow() - timedelta(minutes=limit * 2)

        req = StockBarsRequest(
            symbol_or_symbols=symbols,
            timeframe=TimeFrame.Minute,
            limit=limit,
            start=time_ago,  # <--- THIS IS THE KEY CHANGE
        )

        # The API returns data sorted by date (Ascending).
        # Since we moved the 'start' time forward, we now get the LATEST data.
        return self.data_client.get_stock_bars(req).df

    def get_current_price(self, symbol):
        # SDK Call: Get Latest Trade
        try:
            return self.api.get_latest_trade(symbol).price
        except:
            return None
