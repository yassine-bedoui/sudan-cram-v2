# backend/database.py
import os
from pathlib import Path

from dotenv import load_dotenv, dotenv_values
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError

# Resolve backend directory and .env
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

print(f"📄 Loading .env from: {ENV_PATH}")
print(f"🌱 BEFORE load_dotenv, os.environ['DATABASE_URL'] = {os.getenv('DATABASE_URL')}")

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
    values = dotenv_values(ENV_PATH)
    print(f"📦 dotenv_values: {values}")

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"🔍 AFTER load_dotenv, Effective DATABASE_URL: {DATABASE_URL}")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

# Engine with health checks to avoid stale connections
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # important: test connections before use
    pool_recycle=1800,    # optional: recycle connections every 30 mins
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Yield a DB session and close it safely, even if the server dropped the connection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        try:
            db.close()
        except OperationalError as e:
            # If the server already closed the connection, we just log and ignore.
            print(f"⚠️ Error closing DB session (ignored): {e}")
