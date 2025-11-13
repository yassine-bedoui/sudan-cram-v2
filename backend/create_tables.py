from app.database import Base, engine
from app.models.gdelt import GDELTEvent
from app.models.risk_score import RiskScore

print("Creating database tables...")

# Create all tables
Base.metadata.create_all(bind=engine)

print("✅ All tables created successfully!")

# Verify tables
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()

print(f"\n📋 Created tables: {', '.join(tables)}")
