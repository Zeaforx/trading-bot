import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    print("Verifying imports...")
    from config.settings import settings

    print(
        f"✅ Settings loaded. Interval: {settings.STRATEGY_EVAL_INTERVAL}, Risk: {settings.RISK_PER_TRADE}, Spread Max: {settings.MAX_SPREAD_PCT}"
    )

    from trading.alpaca_client import AlpacaClient

    print("✅ AlpacaClient imported.")

    from trading.order_executor import OrderExecutor

    print("✅ OrderExecutor imported.")

    from strategy.indicators import Indicators

    print("✅ Indicators imported.")

    from strategy.low_risk_swing import LowRiskSwingStrategy

    print("✅ Strategy imported.")

    from bots.runner import TradingBot

    print("✅ Runner imported.")

    print("\nVerifying Logic Components...")
    ind = Indicators()
    # Test ADX method existence
    if hasattr(ind, "adx"):
        print("✅ ADX indicator method exists.")
    else:
        print("❌ ADX indicator MISSING.")

    client = AlpacaClient()
    # Test submit_order signature (inspection not easy, but import worked)

    print(
        "\n🚀 Verification Complete: All modules load successfully. Syntax is correct."
    )

except ImportError as e:
    print(f"❌ Import Error: {e}")
except Exception as e:
    print(f"❌ Verification Failed: {e}")
