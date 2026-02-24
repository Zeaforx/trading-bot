import logging
from data.collectors.alpaca_collector import AlpacaCollector
from strategy.low_risk_swing import LowRiskSwingStrategy

logger = logging.getLogger(__name__)


class Backtester:
    def __init__(self):
        self.collector = AlpacaCollector()
        self.strategy = LowRiskSwingStrategy()

    def run(self, symbol, days=365):
        """Run backtest over historical daily bars for a given symbol."""
        logger.info("Fetching %d days of data for %s...", days, symbol)
        data = self.collector.fetch_latest_bars([symbol], limit=days)

        if data.empty:
            logger.warning("No data returned for %s", symbol)
            return None

        # Extract single symbol from multi-index
        if symbol in data.index:
            data = data.loc[symbol]

        # TODO: Loop through data, simulate trades, calculate PnL metrics
        # (equity curve, win rate, max drawdown, Sharpe ratio)
        logger.info("Backtest complete for %s (%d bars).", symbol, len(data))
        return {"symbol": symbol, "bars": len(data)}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = Backtester().run("SPY")
    print(result)