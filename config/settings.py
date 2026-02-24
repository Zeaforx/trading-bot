import os
import logging
from dotenv import load_dotenv

load_dotenv("local.env")

# Configure logging for the entire application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class Settings:
    # Alpaca API
    ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
    ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
    ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    ALPACA_PAPER = os.getenv("ALPACA_PAPER", "true").lower() == "true"

    # Discord (Dual Channels)
    DISCORD_WEBHOOK_TRADES = os.getenv("DISCORD_WEBHOOK_TRADES")
    DISCORD_WEBHOOK_ALERTS = os.getenv("DISCORD_WEBHOOK_ALERTS")
    DISCORD_WEBHOOK_DEBUG = os.getenv("DISCORD_WEBHOOK_DEBUG")

    # Database (PostgreSQL)
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql://postgres:password@localhost:5432/tradingbot"
    )

    # Trading Parameters
    MAX_POSITION_SIZE = 0.05
    RISK_PER_TRADE = 0.01  # 1% risk per trade
    MAX_TRADES_PER_DAY = 2
    STOP_LOSS_ATR_MULTIPLIER = 2.0
    RISK_REWARD_RATIO = 2.0  # Target 2x risk
    MAX_SPREAD_PCT = 0.001  # 0.1% max spread to trade
    SLIPPAGE_BUFFER_PCT = 0.001  # 0.1% slippage buffer for limit orders

    # Strategy
    SYMBOLS = ["SPY", "QQQ", "AAPL", "MSFT"]
    SMA_SHORT = 20
    SMA_LONG = 50
    RSI_PERIOD = 14
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    ADX_PERIOD = 14
    ADX_THRESHOLD = 25

    # Intervals (in minutes)
    STRATEGY_EVAL_INTERVAL = 1


settings = Settings()

