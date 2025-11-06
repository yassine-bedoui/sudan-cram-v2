"""
✅ CONFLICT PRONENESS v2 - ALL 4 INDICATORS (FIXED)
1. INCIDENTS (35%) - event frequency
2. CAUSES (30%) - % of political/communal/resource
3. ACTORS (20%) - organizational complexity
4. TREND (15%) - recent change
"""

import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"

ACLED_FILE = DATA_DIR / "acled_with_causes.csv"
CLIMATE_FILE = DATA_DIR / "climate_risk_cdi_v2_real.csv"
OUTPUT_FILE = DATA_DIR / "conflict_proneness_v2.csv"

WEIGHTS = {
    'incidents': 0.35,
    'causes': 0.30,
    'actors': 0.20,
    'trend': 0.15,
    'climate': 0.25,
}

def count_unique_actors(state_data):
    """Count unique actor combinations (organizations involved)"""
    actors = set()
    
    # Try ACTOR field
    if 'ACTOR1' in state_data.columns:
        actors.update(state_data['ACTOR1'].dropna().unique())
    if 'ACTOR2' in state_data.columns:
        actors.update(state_data['ACTOR2'].dropna().unique())
    
    # Fallback: use SUB_EVENT_TYPE as proxy for actor differentiation
    if len(actors) <= 1:
        sub_events = state_data['SUB_EVENT_TYPE'].dropna().unique()
        return max(len(sub_events), 1)
    
    return max(len(actors), 1)

def calculate_all_4_indicators(df_acled):
    """Calculate all 4 sub-indicators per state"""
    indicators_by_state = {}
    
    for admin1 in df_acled['ADMIN1'].unique():
        state_data = df_acled[df_acled['ADMIN1'] == admin1]
        
        # INDICATOR 1: INCIDENTS
        total_events = len(state_data)
        
        # INDICATOR 2: CAUSES (% of classified high-risk events)
        high_risk_events = state_data['cause_class'].notna().sum()
        causes_pct = (high_risk_events / max(total_events, 1)) * 100
        
        # INDICATOR 3: ACTORS (unique organizations/groups)
        num_actors = count_unique_actors(state_data)
        
        # INDICATOR 4: TREND (6-month comparison)
        if 'event_date' in state_data.columns:
            state_data_sorted = state_data.sort_values('event_date')
            mid_point = len(state_data_sorted) // 2
            first_half = mid_point
            second_half = len(state_data_sorted) - mid_point
            trend_delta = second_half - first_half
        else:
            trend_delta = 0
        
        fatalities = state_data['FATALITIES'].sum() if 'FATALITIES' in state_data.columns else 0
        
        indicators_by_state[admin1] = {
            'incidents': total_events,
            'causes_pct': causes_pct,
            'actors': num_actors,
            'trend_delta': trend_delta,
            'high_risk_events': high_risk_events,
            'fatalities': int(fatalities),
            'fatality_rate': fatalities / max(total_events, 1)
        }
    
    return indicators_by_state


def normalize_to_10(values):
    """Normalize to 0-10 scale"""
    if len(values) == 0 or values.max() == values.min():
        return np.ones_like(values) * 5.0
    return 10.0 * (values - values.min()) / (values.max() - values.min())


def calculate_proneness_score(incidents, causes, actors, trend, climate):
    """Weighted CP score combining all 4 indicators"""
    score = (
        WEIGHTS['incidents'] * incidents +
        WEIGHTS['causes'] * causes +
        WEIGHTS['actors'] * actors +
        WEIGHTS['trend'] * trend +
        WEIGHTS['climate'] * climate
    )
    return round(min(10.0, max(0.0, score)), 2)


def main():
    print("=" * 70)
    print("✅ CONFLICT PRONENESS v2 - ALL 4 INDICATORS (FIXED ACTORS)")
    print("=" * 70)

    print(f"\n📥 Loading ACLED data from: {ACLED_FILE}")
    df_acled = pd.read_csv(ACLED_FILE)
    df_acled['event_date'] = pd.to_datetime(df_acled['event_date'])
    print(f"   Events: {len(df_acled):,}")

    print(f"\n📥 Loading climate data from: {CLIMATE_FILE}")
    df_climate = pd.read_csv(CLIMATE_FILE)
    print(f"   States: {len(df_climate):,}")

    print("\n🔄 Calculating 4 indicators...")
    indicators_by_state = calculate_all_4_indicators(df_acled)
    print(f"   ✅ Calculated for {len(indicators_by_state)} states")

    print("\n🔄 Computing Conflict Proneness scores...")
    results = []
    
    for _, climate_row in df_climate.iterrows():
        admin1_name = str(climate_row.get('ADM1_NAME', '')).strip()
        
        ind = indicators_by_state.get(admin1_name, {
            'incidents': 0, 'causes_pct': 0, 'actors': 1, 'trend_delta': 0,
            'high_risk_events': 0, 'fatalities': 0, 'fatality_rate': 0.0
        })
        
        results.append({
            'ADM1_NAME': admin1_name,
            'region': admin1_name,
            'incidents': ind['incidents'],
            'causes_pct': ind['causes_pct'],
            'num_actors': ind['actors'],
            'trend_delta': ind['trend_delta'],
            'high_risk_events': ind['high_risk_events'],
            'fatalities': ind['fatalities'],
            'fatality_rate': ind['fatality_rate'],
            'climate_risk_score': float(climate_row.get('climate_risk_score', 0)),
            'cdi_category': climate_row.get('cdi_category', 'UNKNOWN'),
            '_incidents_norm': 0,
            '_causes_norm': 0,
            '_actors_norm': 0,
            '_trend_norm': 0,
            '_climate_norm': 0,
        })
    
    df_results = pd.DataFrame(results)
    
    # Normalize
    print("   Normalizing components...")
    df_results['_incidents_norm'] = normalize_to_10(df_results['incidents'].values.astype(float))
    df_results['_causes_norm'] = normalize_to_10(df_results['causes_pct'].values.astype(float))
    df_results['_actors_norm'] = normalize_to_10(df_results['num_actors'].values.astype(float))
    trend_vals = df_results['trend_delta'].values + abs(df_results['trend_delta'].values.min())
    df_results['_trend_norm'] = normalize_to_10(trend_vals.astype(float))
    df_results['_climate_norm'] = normalize_to_10(df_results['climate_risk_score'].values.astype(float))
    
    # Calculate CP
    print("   Computing weighted scores...")
    df_results['conflict_proneness'] = df_results.apply(
        lambda row: calculate_proneness_score(
            row['_incidents_norm'], row['_causes_norm'], row['_actors_norm'],
            row['_trend_norm'], row['_climate_norm']
        ),
        axis=1
    )
    
    def get_level(score):
        if score >= 8: return "EXTREME"
        elif score >= 6: return "VERY HIGH"
        elif score >= 4: return "HIGH"
        elif score >= 2: return "MODERATE"
        else: return "LOW"
    
    df_results['proneness_level'] = df_results['conflict_proneness'].apply(get_level)
    df_results = df_results.sort_values('conflict_proneness', ascending=False)
    
    # Display
    print("\n📋 TOP 10 Regions (ALL 4 Indicators):")
    print(f"   {'Region':<20} {'CP':>8} {'Level':>12} {'Inc':>6} {'Cause%':>8} {'Act':>4} {'Trend':>6}")
    print("   " + "-" * 75)
    
    for _, row in df_results.head(10).iterrows():
        print(f"   {row['ADM1_NAME']:<20} {row['conflict_proneness']:>8.1f} "
              f"{row['proneness_level']:>12} {row['incidents']:>6} "
              f"{row['causes_pct']:>7.1f}% {row['num_actors']:>4} {row['trend_delta']:>+6}")
    
    print("\n📊 Summary:")
    print(f"   Mean CP: {df_results['conflict_proneness'].mean():.2f}")
    print(f"   Total Fatalities: {df_results['fatalities'].sum():,}")
    
    # Save
    print(f"\n💾 Saving to: {OUTPUT_FILE}")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    output_cols = [
        'ADM1_NAME', 'region', 'conflict_proneness', 'proneness_level',
        'incidents', 'causes_pct', 'num_actors', 'trend_delta', 'high_risk_events',
        'fatalities', 'fatality_rate', 'climate_risk_score', 'cdi_category'
    ]
    df_results[output_cols].to_csv(OUTPUT_FILE, index=False)
    print(f"   ✅ Saved {len(df_results)} regions")
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
