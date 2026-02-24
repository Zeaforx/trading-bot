#!/bin/bash
# Test strategy
python -c "from bots.backtester import Backtester; bt = Backtester(); print(bt.run('SPY'))"

# Test with paper trading first
# Make sure ALPACA_BASE_URL in .env is set to paper trading endpoint
# python main.py