from data.collectors.alpaca_collector import AlpacaCollector
from strategy.low_risk_swing import LowRiskSwingStrategy

class Backtester:
    def __init__(self):
        self.collector = AlpacaCollector()
        self.strategy = LowRiskSwingStrategy()

    def run(self, symbol):
        # SDK Call: Get 1 Year of Data
        print(f"Fetching data for {symbol}...")
        data = self.collector.api.get_bars(
            symbol, "1Day", limit=365
        ).df
        
        # ... logic to loop through data and calculate PnL ...
        # (Same logic as previous guide)
        print("Backtest complete.")

if __name__ == "__main__":
    Backtester().run("SPY")