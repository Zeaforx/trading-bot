import time
from data.collectors.alpaca_collector import AlpacaCollector
from strategy.low_risk_swing import LowRiskSwingStrategy
from trading.order_executor import OrderExecutor
from notifications.discord_logger import discord_logger
from config.settings import settings


class TradingBot:
    def __init__(self):
        self.collector = AlpacaCollector()
        self.strategy = LowRiskSwingStrategy()
        self.executor = OrderExecutor()
        self.symbols = settings.SYMBOLS

    def start(self):
        discord_logger.log_system("🚀 Bot Started")
        while True:
            try:
                # FIX 1: Use the new SDK Clock (via the collector's client)
                # The 'api' attribute does not exist in alpaca-py
                clock = self.collector.trading_client.get_clock()

                if clock.is_open:
                    self.run_cycle()
                else:
                    # 'next_open' is a datetime object in the new SDK
                    print(f"Market Closed. Opens at {clock.next_open}")

                time.sleep(settings.STRATEGY_EVAL_INTERVAL * 60)

            except KeyboardInterrupt:
                discord_logger.log_system("🛑 Bot Stopped")
                break
            except Exception as e:
                discord_logger.log_error(f"Critical Bot Error: {e}")
                time.sleep(60)

    def run_cycle(self):
        discord_logger.log_stage("Cycle Start", "Beginning analysis...")

        # STAGE 1: Batch Data Fetching (Optimization)
        # Fetch data for ALL symbols in one request to reduce API latency and impact
        discord_logger.log_stage(
            "Cycle Update", f"Fetching data for {len(self.symbols)} symbols..."
        )
        batch_data = self.collector.fetch_latest_bars(self.symbols, limit=100)

        if batch_data.empty:
            discord_logger.log_stage("Cycle Warning", "No data returned from API.")
            return

        for symbol in self.symbols:
            try:
                # FIX 2: Handle Multi-Index safely
                if symbol not in batch_data.index:
                    discord_logger.log_stage("Skipping", "No data for symbol", symbol)
                    continue

                single_symbol_data = batch_data.loc[symbol]

                # STAGE 2: Analysis
                signal, score, reason, atr, debug_data = self.strategy.generate_signal(
                    single_symbol_data
                )

                # Log detailed numbers
                discord_logger.log_stage(
                    "Analysis", f"Score: {score}/10", symbol, details=debug_data
                )

                # STAGE 3: Decision & Execution
                if signal != "HOLD":
                    # OPTIMIZATION: Spread Check (Cost Reduction)
                    quote = self.collector.get_latest_quote(symbol)
                    if quote:
                        ask = quote.ask_price
                        bid = quote.bid_price
                        # Handle case where bid/ask are 0 or None
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
                            # Fallback if quote is bad: log warning but maybe proceed or skip?
                            # Safest to skip if we can't verify spread.
                            discord_logger.log_stage(
                                "Warning", "Could not verify spread (bad quote)", symbol
                            )
                            pass  # Or continue to skip

                    # FIX 3: Use log_stage for decision (consistent with new logger)
                    discord_logger.log_stage(
                        "Decision", f"🚨 SIGNAL: {signal}\nReason: {reason}", symbol
                    )

                    # OPTIMIZATION: Use the close price from our batch data instead of a new API call
                    current_price = float(single_symbol_data.iloc[-1]["close"])
                    self.executor.execute_signal(symbol, signal, current_price, atr)

            except Exception as e:
                discord_logger.log_error(f"Error processing {symbol}: {str(e)}")

        discord_logger.log_stage(
            "Cycle End", f"Sleeping for {settings.STRATEGY_EVAL_INTERVAL} mins... 💤"
        )
