import os
from dotenv import load_dotenv

load_dotenv('local.env')

class Settings:
    # Alpaca API
    ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
    ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
    ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    ALPACA_PAPER = True
    
    # Discord (Dual Channels)
    DISCORD_WEBHOOK_TRADES = os.getenv("DISCORD_WEBHOOK_TRADES")
    DISCORD_WEBHOOK_ALERTS = os.getenv("DISCORD_WEBHOOK_ALERTS")
    DISCORD_WEBHOOK_DEBUG = os.getenv("DISCORD_WEBHOOK_DEBUG") 
    
    # Database (PostgreSQL)
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/tradingbot")
    
    # Trading Parameters
    MAX_POSITION_SIZE = 0.05
    MAX_TRADES_PER_DAY = 2
    STOP_LOSS_ATR_MULTIPLIER = 2.0
    
    # Strategy
    SYMBOLS = ["SPY", "QQQ", "AAPL", "MSFT"]
    SMA_SHORT = 20
    SMA_LONG = 50
    RSI_PERIOD = 14
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    
    # Intervals (in minutes)
    STRATEGY_EVAL_INTERVAL = 3

settings = Settings()