import logging
import time
from data.collectors.alpaca_collector import AlpacaCollector
from strategy.low_risk_swing import LowRiskSwingStrategy
from trading.order_executor import OrderExecutor
from notifications.discord_logger import discord_logger
from config.settings import settings

logger = logging.getLogger(__name__)


class TradingBot:
    def __init__(self):
        self.collector = AlpacaCollector()
        self.strategy = LowRiskSwingStrategy()
        self.executor = OrderExecutor()
        self.symbols = settings.SYMBOLS
        self.trades_today = 0

    def start(self):
        discord_logger.log_system("🚀 Bot Started")
        while True:
            try:
                clock = self.collector.trading_client.get_clock()

                if clock.is_open:
                    self.run_cycle()
                else:
                    logger.info("Market Closed. Opens at %s", clock.next_open)

                time.sleep(settings.STRATEGY_EVAL_INTERVAL * 60)

            except KeyboardInterrupt:
                discord_logger.log_system("🛑 Bot Stopped")
                break
            except Exception as e:
                discord_logger.log_error(f"Critical Bot Error: {e}")
                logger.exception("Critical Bot Error")
                time.sleep(60)

    def run_cycle(self):
        discord_logger.log_stage("Cycle Start", "Beginning analysis...")

        # Reset daily trade counter at each cycle (simplified — ideally reset at market open)
        # TODO: Track actual calendar date to reset counter at market open only
        self.trades_today = 0

        # STAGE 1: Batch Data Fetching
        discord_logger.log_stage(
            "Cycle Update", f"Fetching data for {len(self.symbols)} symbols..."
        )
        batch_data = self.collector.fetch_latest_bars(self.symbols, limit=100)

        if batch_data.empty:
            discord_logger.log_stage("Cycle Warning", "No data returned from API.")
            return

        for symbol in self.symbols:
            try:
                if symbol not in batch_data.index:
                    discord_logger.log_stage("Skipping", "No data for symbol", symbol)
                    continue

                single_symbol_data = batch_data.loc[symbol]

                # STAGE 2: Analysis
                signal, score, reason, atr, debug_data = self.strategy.generate_signal(
                    single_symbol_data
                )

                discord_logger.log_stage(
                    "Analysis", f"Score: {score}/10", symbol, details=debug_data
                )

                # STAGE 3: Decision & Execution
                if signal != "HOLD":
                    # Enforce MAX_TRADES_PER_DAY
                    if self.trades_today >= settings.MAX_TRADES_PER_DAY:
                        discord_logger.log_stage(
                            "Skipped",
                            f"Daily trade limit reached ({settings.MAX_TRADES_PER_DAY})",
                            symbol,
                        )
                        continue

                    # Spread Check
                    quote = self.collector.get_latest_quote(symbol)
                    if quote:
                        ask = quote.ask_price
                        bid = quote.bid_price
                        if ask and bid and ask > 0:
                            mid = (ask + bid) / 2
                            spread_pct = (ask - bid) / mid

                            if spread_pct > settings.MAX_SPREAD_PCT:
                                discord_logger.log_stage(
                                    "Skipped",
                                    f"Spread too high: {spread_pct*100:.2f}% > {settings.MAX_SPREAD_PCT*100:.2f}%",
                                    symbol,
                                )
                                continue
                        else:
                            discord_logger.log_stage(
                                "Warning", "Could not verify spread (bad quote)", symbol
                            )
                            continue  # Skip if we can't verify spread

                    discord_logger.log_stage(
                        "Decision", f"🚨 SIGNAL: {signal}\nReason: {reason}", symbol
                    )

                    current_price = float(single_symbol_data.iloc[-1]["close"])
                    self.executor.execute_signal(symbol, signal, current_price, atr)
                    self.trades_today += 1

            except Exception as e:
                discord_logger.log_error(f"Error processing {symbol}: {str(e)}")
                logger.exception("Error processing %s", symbol)

        discord_logger.log_stage(
            "Cycle End", f"Sleeping for {settings.STRATEGY_EVAL_INTERVAL} mins... 💤"
        )

