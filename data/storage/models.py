from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Numeric
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()


def _utc_now():
    return datetime.now(timezone.utc)

class PriceData(Base):
    __tablename__ = 'price_data'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String, index=True)
    timestamp = Column(DateTime, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)

class Trade(Base):
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String)
    side = Column(String)  # 'buy' or 'sell'
    quantity = Column(Float)
    entry_price = Column(Numeric(10, 2)) 
    exit_price = Column(Numeric(10, 2), nullable=True)
    pnl = Column(Numeric(10, 2), nullable=True)
    stop_loss = Column(Float)
    take_profit = Column(Float, nullable=True)
    entry_time = Column(DateTime, default=_utc_now)
    exit_time = Column(DateTime, nullable=True)
    status = Column(String, default='open')  # 'open', 'closed'

class Signal(Base):
    __tablename__ = 'signals'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String)
    signal_type = Column(String)  # 'BUY', 'SELL', 'HOLD'
    timestamp = Column(DateTime, default=_utc_now)
    indicators = Column(String)  # JSON string of indicator values
    executed = Column(Boolean, default=False)