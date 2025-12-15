import alpaca_trade_api as tradeapi
from config.settings import settings
from notifications.discord_logger import discord_logger

class AlpacaClient:
    def __init__(self):
        self.api = tradeapi.REST(
            settings.ALPACA_API_KEY,
            settings.ALPACA_SECRET_KEY,
            settings.ALPACA_BASE_URL
        )
    
    def get_position(self, symbol):
        try:
            return self.api.get_position(symbol)
        except:
            return None
    
    def submit_order(self, symbol, qty, side, stop_loss=None):
        try:
            # SDK Call: Submit Order
            order = self.api.submit_order(
                symbol=symbol, qty=qty, side=side, 
                type='market', time_in_force='gtc'
            )
            
            # SDK Call: Submit Stop Loss (Bracket-like behavior)
            if stop_loss and side == 'buy':
                self.api.submit_order(
                    symbol=symbol, qty=qty, side='sell', 
                    type='stop', stop_price=stop_loss, time_in_force='gtc'
                )
            
            price = float(order.filled_avg_price or order.limit_price or 0)
            discord_logger.log_trade(side, symbol, qty, price)
            return order
        except Exception as e:
            discord_logger.log_error(f"Order Failed: {e}")
            return None