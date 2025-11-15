import pandas as pd
from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql://sudan_cram_user:0iUMUWn4LLMvzyYxMu1ZB7Ry8n8nPSH7@dpg-d453f2euk2gs73fs5lgg-a.oregon-postgres.render.com/sudan_cram_db"
)

# ---------- NEW: clear target tables first ----------
with engine.begin() as conn:
    # Order matters if you have FKs; here they look independent
    conn.execute(text("TRUNCATE TABLE gdelt_events RESTART IDENTITY CASCADE;"))
    conn.execute(text("TRUNCATE TABLE acled_events RESTART IDENTITY CASCADE;"))
# ----------------------------------------------------


# --------- GDELT ----------
df_gdelt = pd.read_csv("data/gdelt/sudan_events_20251110_1005.csv")

df_gdelt = df_gdelt.rename(columns={
    "date": "event_date",
    "goldstein": "goldstein_scale",
    "actor1": "actor1_name",
    "actor2": "actor2_name",
    "location": "region",
})

# Add required event_id with deterministic IDs
df_gdelt["event_id"] = ["gdelt-" + str(i) for i in df_gdelt.index]

expected_gdelt_cols = [
    "event_id",
    "event_date",
    "event_code",
    "goldstein_scale",
    "num_mentions",
    "avg_tone",
    "actor1_name",
    "actor2_name",
    "region",
    "latitude",
    "longitude",
]

df_gdelt = df_gdelt[expected_gdelt_cols]

df_gdelt["latitude"] = pd.to_numeric(df_gdelt["latitude"], errors="coerce")
df_gdelt["longitude"] = pd.to_numeric(df_gdelt["longitude"], errors="coerce")

df_gdelt.to_sql("gdelt_events", engine, if_exists="append", index=False)


# --------- ACLED ----------
df_acled = pd.read_csv("data/processed/acled_with_causes.csv")

df_acled = df_acled.rename(columns={
    "event_date": "event_date",
    "REGION": "region",
    "EVENT_TYPE": "event_type",
    "FATALITIES": "fatalities",
    "CENTROID_LATITUDE": "latitude",
    "CENTROID_LONGITUDE": "longitude",
})

df_acled["event_id"] = ["acled-" + str(i) for i in df_acled.index]

expected_acled_cols = [
    "event_id",
    "event_date",
    "region",
    "event_type",
    "fatalities",
    "latitude",
    "longitude",
]

df_acled = df_acled[expected_acled_cols]

df_acled["latitude"] = pd.to_numeric(df_acled["latitude"], errors="coerce")
df_acled["longitude"] = pd.to_numeric(df_acled["longitude"], errors="coerce")

df_acled.to_sql("acled_events", engine, if_exists="append", index=False)
