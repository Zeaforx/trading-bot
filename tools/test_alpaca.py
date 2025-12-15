import alpaca_trade_api as tradeapi
from config.settings import settings

def test_connection():
    print("Testing Alpaca SDK Connection...")
    
    # Initialize SDK
    api = tradeapi.REST(
        settings.ALPACA_API_KEY,
        settings.ALPACA_SECRET_KEY,
        settings.ALPACA_BASE_URL
    )

    try:
        # 1. Check Account
        account = api.get_account()
        print(f"✅ Account Status: {account.status}")
        print(f"💰 Buying Power: ${account.buying_power}")

        # 2. Check Market Clock
        clock = api.get_clock()
        print(f"⏰ Market Open: {clock.is_open}")

        # 3. Check Data Access
        spy_bar = api.get_bars("SPY", tradeapi.TimeFrame.Day, limit=1)
        print(f"📊 Data Test (SPY): ${spy_bar[0].c}")

        return True
    except Exception as e:
        print(f"❌ SDK Error: {e}")
        return False

if __name__ == "__main__":
    test_connection()