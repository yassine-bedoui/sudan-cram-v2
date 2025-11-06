"""
✅ CONFLICT RISK - Simple Incident Count
Uses SAME data source as CP v2 (acled_with_causes.csv)
"""

import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"

ACLED_FILE = DATA_DIR / "acled_with_causes.csv"
OUTPUT_FILE = DATA_DIR / "conflict_risk_simple.csv"

def normalize_to_10(values):
    """Normalize to 0-10 scale"""
    if len(values) == 0 or values.max() == values.min():
        return np.ones_like(values) * 5.0
    return 10.0 * (values - values.min()) / (values.max() - values.min())

def get_level(score):
    """Convert score to risk level"""
    if score >= 8: return "EXTREME"
    elif score >= 6: return "VERY HIGH"
    elif score >= 4: return "HIGH"
    elif score >= 2: return "MODERATE"
    else: return "LOW"

def main():
    print("=" * 70)
    print("✅ CONFLICT RISK - INCIDENT FREQUENCY (same ACLED as CP v2)")
    print("=" * 70)

    print(f"\n📥 Loading ACLED (processed): {ACLED_FILE}")
    df_acled = pd.read_csv(ACLED_FILE)
    print(f"   Total events: {len(df_acled):,}")

    print("\n🔄 Computing Conflict Risk by state...")

    # ✅ FIXED: Iterate over ACLED states (not climate data)
    results = []
    for admin1 in sorted(df_acled['ADMIN1'].unique()):
        state_data = df_acled[df_acled['ADMIN1'] == admin1]
        
        incidents = len(state_data)
        fatalities = int(state_data['FATALITIES'].sum())
        
        print(f"   {admin1:<20} {incidents:>6} incidents, {fatalities:>6} fatalities")

        results.append({
            'region': admin1,
            'incidents': incidents,
            'fatalities': fatalities,
        })

    df_results = pd.DataFrame(results)
    
    print(f"\n   Total states: {len(df_results)}")

    # Normalize to 0-10
    print("\n🔄 Normalizing scores...")
    incidents_norm = normalize_to_10(df_results['incidents'].values.astype(float))
    fatalities_norm = normalize_to_10(df_results['fatalities'].values.astype(float))

    # Weighted combination: 70% incidents, 30% fatalities
    df_results['conflict_risk_score'] = (0.7 * incidents_norm + 0.3 * fatalities_norm).round(2)
    df_results['conflict_risk_level'] = df_results['conflict_risk_score'].apply(get_level)
    df_results = df_results.sort_values('conflict_risk_score', ascending=False)

    print(f"\n📋 TOP 10 by Conflict Risk:")
    print(f"   {'Region':<20} {'Score':>8} {'Level':>12} {'Incidents':>10} {'Fatalities':>10}")
    print("   " + "-" * 65)
    
    for _, row in df_results.head(10).iterrows():
        print(f"   {row['region']:<20} {row['conflict_risk_score']:>8.1f} "
              f"{row['conflict_risk_level']:>12} {row['incidents']:>10} {row['fatalities']:>10}")

    print(f"\n📊 Summary:")
    print(f"   Mean Risk Score: {df_results['conflict_risk_score'].mean():.2f}")
    print(f"   States analyzed: {len(df_results)}")
    print(f"   Total incidents: {df_results['incidents'].sum():,}")
    print(f"   Total fatalities: {df_results['fatalities'].sum():,}")
    
    print(f"\n💾 Saving to: {OUTPUT_FILE}")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    output_cols = ['region', 'conflict_risk_score', 'conflict_risk_level', 'incidents', 'fatalities']
    df_results[output_cols].to_csv(OUTPUT_FILE, index=False)
    print(f"   ✅ Saved {len(df_results)} regions")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
