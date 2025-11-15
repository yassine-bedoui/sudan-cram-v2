from pathlib import Path
from dotenv import load_dotenv, dotenv_values
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

BASE_DIR = Path(__file__).resolve().parent      # .../backend
ENV_PATH = BASE_DIR / ".env"                    # .../backend/.env

print("📄 Loading .env from:", ENV_PATH)

# Show what DATABASE_URL is *before* we load .env
print("🌱 BEFORE load_dotenv, os.environ['DATABASE_URL'] =",
      os.environ.get("DATABASE_URL"))

# Force-load .env and override anything already set
load_dotenv(dotenv_path=ENV_PATH, override=True)

# Show what dotenv actually read from the file
print("📦 dotenv_values:", dotenv_values(ENV_PATH))

# Now read DATABASE_URL from the environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost/sudan_cram"
)

print("🔍 AFTER load_dotenv, Effective DATABASE_URL:", DATABASE_URL)

# Fix old-style postgres:// URLs if needed
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
