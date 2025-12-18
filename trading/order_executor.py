from datetime import datetime
from trading.alpaca_client import AlpacaClient
from config.settings import settings
from data.storage.database import SessionLocal
from data.storage.models import Trade


class OrderExecutor:
    def __init__(self):
        self.client = AlpacaClient()

    def check_risk_management(self, current_prices):
        """
        DEPRECATED: Now using Server-Side OTO Stops.
        Kept as a fallback or for logging if needed, but primary risk is handled by the order itself.
        """
        pass

    def execute_signal(self, symbol, signal, current_price, atr):
        """Execute Buy/Sell based on strategy signal using Limit OTO Orders"""
        if signal == "HOLD":
            return

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
                # OPTIMIZATION: Use fractional shares (round to 4 decimals for safety)
                qty = round(risk_amount / sl_dist, 4)
            else:
                qty = 0

            # Cap size at MAX_POSITION_SIZE (e.g. 5% of portfolio)
            max_qty = (portfolio_value * settings.MAX_POSITION_SIZE) / current_price
            qty = min(qty, max_qty)

            if qty < 0.0001:
                print(
                    f"⚠️ Calculated quantity 0 for {symbol} (Risk: ${risk_amount:.2f}, SL Dist: {sl_dist:.2f})"
                )
                return

            # --- 2. Calculate Prices ---
            # OPTIMIZATION: Marketable Limit Order (Current + 0.1% buffer)
            # This ensures we cross the spread and get filled in fast moves, but don't pay infinite slippage.
            limit_entry_price = current_price * 1.001

            stop_loss_price = limit_entry_price - sl_dist

            # Optional: Dynamic Take Profit (2:1 Ratio)
            take_profit_price = limit_entry_price + (
                sl_dist * settings.RISK_REWARD_RATIO
            )

            # --- 3. Submit Limit OTO Order ---
            print(
                f"🚀 Submitting BUY {symbol} Qty:{qty} Limit:${limit_entry_price:.2f} SL:${stop_loss_price:.2f}"
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
                db = SessionLocal()
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
                db.close()

        elif signal == "SELL" and position:
            # Alpaca-py returns strings for qty_available, convert to float
            qty = float(position.qty_available)
            if qty > 0:
                # Exit with Limit Order at current price (or slightly lower to chase)
                # For safety, ensure we cross the spread.
                limit_exit = current_price * 0.999

                self.client.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side="sell",
                    order_type="limit",
                    limit_price=limit_exit,
                )

                # Close in Database
                db = SessionLocal()
                trade = (
                    db.query(Trade)
                    .filter(Trade.symbol == symbol, Trade.status == "open")
                    .first()
                )
                if trade:
                    trade.status = "closed"
                    trade.exit_price = current_price
                    trade.exit_time = datetime.utcnow()
                    db.commit()
                db.close()
