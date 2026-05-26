from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import config

connect_args = {"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {}
pool_pre_ping = not config.DATABASE_URL.startswith("sqlite")
engine = create_engine(config.DATABASE_URL, connect_args=connect_args, pool_pre_ping=pool_pre_ping)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()