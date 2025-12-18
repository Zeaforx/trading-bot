from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, StopOrderRequest, LimitOrderRequest, TakeProfitRequest, StopLossRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
from config.settings import settings
from notifications.discord_logger import discord_logger

class AlpacaClient:
    def __init__(self):
        # Initialize the modern TradingClient
        self.client = TradingClient(
            settings.ALPACA_API_KEY,
            settings.ALPACA_SECRET_KEY,
            paper=settings.ALPACA_PAPER
        )

    def get_account(self):
        """Get account information"""
        return self.client.get_account()

    def get_portfolio_value(self):
        """Get current total equity"""
        account = self.get_account()
        return float(account.portfolio_value)

    def get_position(self, symbol):
        """Get current position for symbol. Returns None if no position."""
        try:
            # alpaca-py throws an APIError if position doesn't exist
            return self.client.get_open_position(symbol)
        except Exception:
            return None

    def submit_order(self, symbol, qty, side, order_type, limit_price=None, stop_loss_price=None, take_profit_price=None):
        """
        Submit order using modern Request objects.
        Supports Market, Limit, Stop, and Bracket (OTO) orders.
        """
        # 1. Convert string side to Enum
        side_enum = OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL
        
        try:
            order_request = None
            
            # 2. Construct the correct Request Object
            if order_type == 'market':
                order_request = MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=side_enum,
                    time_in_force=TimeInForce.DAY
                )
            
            elif order_type == 'limit':
                if not limit_price:
                    raise ValueError("Limit price required for limt orders")
                
                # Check for OTO (One-Triggers-Other) parameters
                # If we have a stop_loss_price, we use a Bracket Order (or OTO)
                if stop_loss_price or take_profit_price:
                    # Construct nested requests
                    sl_req = StopLossRequest(stop_price=stop_loss_price) if stop_loss_price else None
                    tp_req = TakeProfitRequest(limit_price=take_profit_price) if take_profit_price else None
                    
                    order_request = LimitOrderRequest(
                        symbol=symbol,
                        qty=qty,
                        side=side_enum,
                        time_in_force=TimeInForce.GTC,
                        limit_price=limit_price,
                        order_class=OrderClass.BRACKET if (sl_req and tp_req) else OrderClass.OTO,
                        stop_loss=sl_req,
                        take_profit=tp_req
                    )
                else:
                    # Standard Limit Order
                    order_request = LimitOrderRequest(
                        symbol=symbol,
                        qty=qty,
                        side=side_enum,
                        time_in_force=TimeInForce.GTC,
                        limit_price=limit_price
                    )

            elif order_type == 'stop':
                if not stop_loss_price:
                    raise ValueError("Stop price required for stop orders")
                order_request = StopOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=side_enum,
                    time_in_force=TimeInForce.GTC,
                    stop_price=stop_loss_price
                )

            # 3. Submit
            if order_request:
                order = self.client.submit_order(order_request)
                
                # Log success
                price_log = f"${limit_price}" if limit_price else "MKT"
                discord_logger.log_trade(side, symbol, qty, price_log)
                return order

        except Exception as e:
            discord_logger.log_error(f"Order failed for {symbol}: {str(e)}")
            return None