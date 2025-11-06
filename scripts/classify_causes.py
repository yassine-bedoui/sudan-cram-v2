"""
✅ ACLED Event Classification - Political, Communal, Resource
For Conflict Proneness calculation (part of 4-indicator model)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
ACLED_FILE = PROJECT_ROOT / "data" / "raw" / "Africa_aggregated_data_up_to-2025-10-18.xlsx"
OUTPUT_FILE = DATA_DIR / "acled_with_causes.csv"

END_DATE = datetime(2025, 10, 31)
START_DATE = END_DATE - timedelta(days=365)

CAUSE_MAP = {
    "Armed clash": "political", "Attack": "political",
    "Mob violence": "communal", "Violent demonstration": "communal",
    "Excessive force against protesters": "communal",
    "Looting/property destruction": None, "Peaceful protest": None,
    "Agreement": "exclude", "Arrests": "exclude",
}

RESOURCE_KEYWORDS = ["land", "pasture", "water", "grazing", "livestock", "cattle", "herder", "farmer", "crop"]

def classify_cause(row):
    sub_event = row.get('SUB_EVENT_TYPE', '')
    event_type = row.get('EVENT_TYPE', '')
    disorder_type = str(row.get('DISORDER_TYPE', '')).lower()
    notes = str(row.get('NOTES', '')).lower()
    
    cause = CAUSE_MAP.get(sub_event)
    if cause == "exclude": return None
    if cause: return cause
    
    combined_text = disorder_type + " " + notes
    if any(kw in combined_text for kw in RESOURCE_KEYWORDS): return "resource"
    if event_type == "Protests": return "communal" if any(kw in combined_text for kw in RESOURCE_KEYWORDS) else "communal"
    if event_type == "Violence against civilians": return "political"
    return None

def main():
    print("=" * 70)
    print("✅ CLASSIFY CAUSES")
    print("=" * 70)

    df = pd.read_excel(ACLED_FILE)
    print(f"\n📥 Loaded: {len(df):,} events")

    df_sudan = df[df['COUNTRY'].str.lower() == 'sudan'].copy()
    print(f"🔍 Sudan: {len(df_sudan):,} events")

    df_sudan['event_date'] = pd.to_datetime(df_sudan['WEEK'])
    df_filtered = df_sudan[
        (df_sudan['event_date'] >= START_DATE) &
        (df_sudan['event_date'] <= END_DATE)
    ].copy()
    print(f"📅 Filtered ({START_DATE.date()} to {END_DATE.date()}): {len(df_filtered):,} events")

    df_filtered['cause_class'] = df_filtered.apply(classify_cause, axis=1)

    print("\n📊 Classification:")
    for cause, count in df_filtered['cause_class'].value_counts(dropna=False).items():
        label = cause if pd.notna(cause) else "Not classified"
        print(f"   {label}: {count:,}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df_filtered.to_csv(OUTPUT_FILE, index=False)
    print(f"\n💾 Saved to: {OUTPUT_FILE}")
    print("=" * 70)

if __name__ == "__main__":
    main()
