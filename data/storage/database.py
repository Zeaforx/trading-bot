from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import settings
from .models import Base

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)