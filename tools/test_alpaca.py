"""Quick connectivity test using the modern alpaca-py SDK."""
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from config.settings import settings


def test_connection():
    print("Testing Alpaca SDK Connection...")

    trading_client = TradingClient(
        settings.ALPACA_API_KEY,
        settings.ALPACA_SECRET_KEY,
        paper=settings.ALPACA_PAPER,
    )
    data_client = StockHistoricalDataClient(
        settings.ALPACA_API_KEY,
        settings.ALPACA_SECRET_KEY,
    )

    try:
        # 1. Check Account
        account = trading_client.get_account()
        print(f"✅ Account Status: {account.status}")
        print(f"💰 Buying Power: ${account.buying_power}")

        # 2. Check Market Clock
        clock = trading_client.get_clock()
        print(f"⏰ Market Open: {clock.is_open}")

        # 3. Check Data Access
        request = StockBarsRequest(
            symbol_or_symbols="SPY",
            timeframe=TimeFrame.Day,
            limit=1,
        )
        bars = data_client.get_stock_bars(request).df
        if not bars.empty:
            print(f"📊 Data Test (SPY): ${bars.iloc[-1]['close']:.2f}")

        return True
    except Exception as e:
        print(f"❌ SDK Error: {e}")
        return False


if __name__ == "__main__":
    test_connection()