from data.storage.database import init_db
from bots.runner import TradingBot

if __name__ == "__main__":
    init_db()  # Creates Postgres tables
    TradingBot().start()