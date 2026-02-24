import logging
from datetime import datetime, timezone
from trading.alpaca_client import AlpacaClient
from config.settings import settings
from data.storage.database import SessionLocal
from data.storage.models import Trade

logger = logging.getLogger(__name__)


class OrderExecutor:
    def __init__(self):
        self.client = AlpacaClient()

    def execute_signal(self, symbol, signal, current_price, atr):
        """Execute Buy/Sell based on strategy signal using Limit OTO Orders"""
        if signal == "HOLD":
            return False

        # Check existing position
        position = self.client.get_position(symbol)

        if signal == "BUY" and not position:
            # --- 1. Volatility-Adjusted Sizing (Kelly / Risk%) ---
            portfolio_value = self.client.get_portfolio_value()

            # Risk Amount = Account * Risk% (e.g., $100k * 1% = $1000 risk)
            risk_amount = portfolio_value * settings.RISK_PER_TRADE

            # Stop Loss Distance = 2 * ATR
            sl_dist = atr * settings.STOP_LOSS_ATR_MULTIPLIER

            # Shares = Risk Amount / Risk Per Share
            if sl_dist > 0:
                qty = round(risk_amount / sl_dist, 4)
            else:
                qty = 0

            # Cap size at MAX_POSITION_SIZE (e.g. 5% of portfolio)
            max_qty = (portfolio_value * settings.MAX_POSITION_SIZE) / current_price
            qty = min(qty, max_qty)

            if qty < 0.0001:
                logger.warning(
                    "Calculated quantity 0 for %s (Risk: $%.2f, SL Dist: %.2f)",
                    symbol, risk_amount, sl_dist,
                )
                return False

            # --- 2. Calculate Prices ---
            # Marketable Limit Order (Current + slippage buffer)
            limit_entry_price = current_price * (1 + settings.SLIPPAGE_BUFFER_PCT)

            stop_loss_price = limit_entry_price - sl_dist

            # Dynamic Take Profit (risk:reward ratio)
            take_profit_price = limit_entry_price + (
                sl_dist * settings.RISK_REWARD_RATIO
            )

            # --- 3. Submit Limit OTO Order ---
            logger.info(
                "Submitting BUY %s Qty:%s Limit:$%.2f SL:$%.2f",
                symbol, qty, limit_entry_price, stop_loss_price,
            )

            order = self.client.submit_order(
                symbol=symbol,
                qty=qty,
                side="buy",
                order_type="limit",
                limit_price=limit_entry_price,
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price,
            )

            if order:
                # 4. Record in Database
                with SessionLocal() as db:
                    trade = Trade(
                        symbol=symbol,
                        side="buy",
                        quantity=qty,
                        entry_price=limit_entry_price,
                        stop_loss=stop_loss_price,
                        status="open",
                    )
                    db.add(trade)
                    db.commit()
                return True
        elif signal == "SELL" and position:
            # Alpaca-py returns strings for qty_available, convert to float
            qty = float(position.qty_available)
            if qty > 0:
                # Exit with Limit Order (slightly below current to cross spread)
                limit_exit = current_price * (1 - settings.SLIPPAGE_BUFFER_PCT)

                order = self.client.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side="sell",
                    order_type="limit",
                    limit_price=limit_exit,
                )

                if order:
                    # Close in Database only if order submitted successfully
                    with SessionLocal() as db:
                        trade = (
                            db.query(Trade)
                            .filter(Trade.symbol == symbol, Trade.status == "open")
                            .first()
                        )
                        if trade:
                            trade.status = "closed"
                            trade.exit_price = current_price
                            trade.exit_time = datetime.now(timezone.utc)
                            db.commit()
                return True
        return False
