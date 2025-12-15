from datetime import datetime
from trading.alpaca_client import AlpacaClient
from config.settings import settings
from data.storage.database import SessionLocal
from data.storage.models import Trade

class OrderExecutor:
    def __init__(self):
        self.client = AlpacaClient()
    
    def check_risk_management(self, current_prices):
        """Checks if we need to close positions based on Stop Loss"""
        db = SessionLocal()
        open_trades = db.query(Trade).filter(Trade.status == 'open').all()
        executed_actions = []

        for trade in open_trades:
            symbol = trade.symbol
            if symbol not in current_prices:
                continue
                
            price = current_prices[symbol]
            
            # Check Stop Loss
            if price <= float(trade.stop_loss):
                # STRICT TYPING: Convert DB Decimal to float
                qty = float(trade.quantity)
                
                print(f"🛑 STOP LOSS triggered for {symbol} at ${price}")
                self.client.submit_order(symbol, qty, 'sell')
                
                # Update DB
                trade.status = 'closed_sl'
                trade.exit_price = price
                trade.exit_time = datetime.utcnow()
                executed_actions.append(f"Sold {symbol} (Stop Loss)")
            
        if executed_actions:
            db.commit()
        db.close()
        
        return executed_actions
    
    def execute_signal(self, symbol, signal, current_price, atr):
        """Execute Buy/Sell based on strategy signal"""
        if signal == 'HOLD':
            return
        
        # Check existing position
        position = self.client.get_position(symbol)
        
        if signal == 'BUY' and not position:
            # 1. Calculate Size
            portfolio_value = self.client.get_portfolio_value()
            max_risk = portfolio_value * settings.MAX_POSITION_SIZE
            qty = int(max_risk / current_price)
            
            if qty < 1: return

            # 2. Calculate Stop Loss Price
            stop_loss = current_price - (atr * 2.0)

            # 3. Submit Market Buy
            order = self.client.submit_order(symbol, qty, 'buy')
            
            if order:
                # 4. Optional: Submit a server-side Stop Loss order immediately
                # self.client.submit_order(symbol, qty, 'sell', order_type='stop', stop_loss_price=stop_loss)
                
                # 5. Record in Database
                db = SessionLocal()
                trade = Trade(
                    symbol=symbol,
                    side='buy',
                    quantity=qty,
                    entry_price=current_price,
                    stop_loss=stop_loss,
                    status='open'
                )
                db.add(trade)
                db.commit()
                db.close()
        
        elif signal == 'SELL' and position:
            # Alpaca-py returns strings for qty_available, convert to float
            qty = float(position.qty_available)
            if qty > 0:
                self.client.submit_order(symbol, qty, 'sell')
                
                # Close in Database
                db = SessionLocal()
                trade = db.query(Trade).filter(
                    Trade.symbol == symbol, Trade.status == 'open'
                ).first()
                if trade:
                    trade.status = 'closed'
                    trade.exit_price = current_price
                    trade.exit_time = datetime.utcnow()
                    db.commit()
                db.close()