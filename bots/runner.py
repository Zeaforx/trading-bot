# bots/runner.py

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
        # FIX IS HERE: Load symbols from settings
        self.symbols = settings.SYMBOLS 
    
    def start(self):
        discord_logger.log_system("🚀 Bot Started")
        while True:
            try:
                # Check if market is open
                clock = self.executor.client.api.get_clock()
                if clock.is_open:
                    self.run_cycle()
                else:
                    print(f"Market Closed. Opens at {clock.next_open}")
                
                # Sleep interval
                time.sleep(settings.STRATEGY_EVAL_INTERVAL * 60)
            
            except KeyboardInterrupt:
                discord_logger.log_system("🛑 Bot Stopped")
                break
            except Exception as e:
                discord_logger.log_error(f"Critical Bot Error: {e}")
                time.sleep(60)
    
    def run_cycle(self):
        discord_logger.log_stage("Cycle Start", "Beginning analysis...")

        for symbol in self.symbols:
            try:
                # STAGE 1: Data
                data = self.collector.fetch_latest_bars(symbol, limit=100)
                
                if data.empty:
                    discord_logger.log_stage("Skipping", "No data found.", symbol)
                    continue
                
                # STAGE 2: Analysis
                # We unpack 5 values now (including debug_data)
                signal, score, reason, atr, debug_data = self.strategy.generate_signal(data)
                
                # Log detailed numbers to #bot-brain
                discord_logger.log_stage(
                    "Analysis", 
                    f"Indicators Calculated. Score: {score}", 
                    symbol, 
                    details=debug_data
                )

                # STAGE 3: Decision & Execution
                if signal != 'HOLD':
                    discord_logger.log_signal(symbol, signal, score, reason)
                    
                    current_price = self.collector.get_current_price(symbol)
                    self.executor.execute_signal(symbol, signal, current_price, atr)
                
            except Exception as e:
                discord_logger.log_error(f"Error processing {symbol}: {str(e)}")
        
        discord_logger.log_stage("Cycle End", f"Sleeping for {settings.STRATEGY_EVAL_INTERVAL} mins... 💤")