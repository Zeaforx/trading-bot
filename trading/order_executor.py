from trading.alpaca_client import AlpacaClient
from config.settings import settings
from data.storage.database import SessionLocal
from data.storage.models import Trade
from datetime import datetime

class OrderExecutor:
    def __init__(self):
        self.client = AlpacaClient()
    
    def execute_signal(self, symbol, signal, price, atr):
        if signal == 'HOLD': return
        
        position = self.client.get_position(symbol)
        
        if signal == 'BUY' and not position:
            qty = self._calc_size(price, atr)
            sl = price - (atr * settings.STOP_LOSS_ATR_MULTIPLIER)
            if self.client.submit_order(symbol, qty, 'buy', sl):
                self._log_db(symbol, 'buy', qty, price, sl)
                
        elif signal == 'SELL' and position:
            qty = abs(int(float(position.qty)))
            if self.client.submit_order(symbol, qty, 'sell'):
                self._close_db(symbol, price)

    def _calc_size(self, price, atr):
        # Simple risk calculation
        account = self.client.api.get_account()
        equity = float(account.portfolio_value)
        risk_amt = equity * 0.02
        shares = int(risk_amt / (atr * 2))
        return shares

    def _log_db(self, symbol, side, qty, price, sl):
        db = SessionLocal()
        db.add(Trade(symbol=symbol, side=side, quantity=qty, entry_price=price, stop_loss=sl))
        db.commit()
        db.close()

    def _close_db(self, symbol, price):
        db = SessionLocal()
        t = db.query(Trade).filter(Trade.symbol==symbol, Trade.status=='open').first()
        if t:
            t.exit_price = price
            t.status = 'closed'
            db.commit()
        db.close()