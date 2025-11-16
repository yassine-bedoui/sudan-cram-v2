from datetime import datetime

from database import Base, engine
from app.models.gdelt import GDELTEvent
from app.models.acled import ACLEDEvent
from app.models.analysis import AnalysisRun, AnalysisFeedback


def create_all_tables():
    print(f"[{datetime.utcnow().isoformat()}] Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created (or already existed).")


if __name__ == "__main__":
    create_all_tables()
