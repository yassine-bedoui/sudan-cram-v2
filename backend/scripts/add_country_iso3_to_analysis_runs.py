# scripts/add_country_iso3_to_analysis_runs.py

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv


# 1) Load environment variables from .env (at project root)
load_dotenv()  # this will pick up your DATABASE_URL from .env

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. "
        "Set it in your environment or in .env, e.g. "
        "DATABASE_URL='postgresql://user:pass@host:5432/dbname'"
    )

# Optional: normalize old-style 'postgres://' URLs
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

engine = create_engine(DATABASE_URL, future=True)


def main() -> None:
    print(f"Connecting to database: {DATABASE_URL}")

    with engine.begin() as conn:
        # 1) Add column if it doesn't exist
        print("Adding column country_iso3 to analysis_runs (IF NOT EXISTS)...")
        conn.execute(
            text(
                """
                ALTER TABLE analysis_runs
                ADD COLUMN IF NOT EXISTS country_iso3 VARCHAR(3)
                """
            )
        )

        # 2) Backfill existing rows
        print("Backfilling existing rows with 'SDN' where country_iso3 is NULL or empty...")
        conn.execute(
            text(
                """
                UPDATE analysis_runs
                SET country_iso3 = 'SDN'
                WHERE country_iso3 IS NULL OR country_iso3 = '';
                """
            )
        )

        # 3) Set default and NOT NULL
        print("Setting DEFAULT 'SDN' and NOT NULL on country_iso3...")
        conn.execute(
            text(
                """
                ALTER TABLE analysis_runs
                ALTER COLUMN country_iso3 SET DEFAULT 'SDN';
                """
            )
        )
        conn.execute(
            text(
                """
                ALTER TABLE analysis_runs
                ALTER COLUMN country_iso3 SET NOT NULL;
                """
            )
        )

    print("✅ Migration complete: country_iso3 column is ready on analysis_runs.")


if __name__ == "__main__":
    main()
