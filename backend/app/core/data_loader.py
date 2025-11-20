"""
Data Loading and Preparation Module for Sudan CRAM Dashboard

This module handles loading, caching, and preparing data from the 
processed datasets for visualization in the Streamlit dashboard.

Author: Sudan CRAM Team
Date: November 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple, Optional, List
import streamlit as st
from .state_name_normalizer import normalize_dataframe_states


# ============================================================================
# PATH CONFIGURATION
# ============================================================================

# Get project root directory (two levels up from this file)
# dashboard/utils/data_loader.py -> dashboard/ -> Sudan CRAM/
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Define data paths
DATA_DIR = PROJECT_ROOT / 'data' / 'processed'
RAW_DATA_DIR = PROJECT_ROOT / 'data' / 'raw'


# ============================================================================
# HELPER FUNCTIONS FOR COLUMN DETECTION
# ============================================================================

def find_column(df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
    """
    Find the first matching column name from a list of possibilities.
    
    Args:
        df: DataFrame to search
        possible_names: List of possible column names
        
    Returns:
        Column name if found, None otherwise
    """
    for name in possible_names:
        if name in df.columns:
            return name
    return None


# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

@st.cache_data
def load_conflict_proneness() -> pd.DataFrame:
    """
    Load Conflict Proneness v2 scores by state.
    
    Returns:
        DataFrame with columns: ADM1_NAME, conflict_proneness_v2, smoothed_causes_pct, etc.
    """
    try:
        path = DATA_DIR / 'conflict_proneness_v2_with_causes.csv'
        df = pd.read_csv(path)
        
        # Ensure numeric columns
        if 'conflict_proneness_v2' in df.columns:
            df['conflict_proneness_v2'] = pd.to_numeric(df['conflict_proneness_v2'], errors='coerce')
        
        if 'smoothed_causes_pct' in df.columns:
            df['smoothed_causes_pct'] = pd.to_numeric(df['smoothed_causes_pct'], errors='coerce')
        
        # ✅ NORMALIZE STATE NAMES
        df = normalize_dataframe_states(df, state_column='state')
        
        return df
    
    except FileNotFoundError:
        st.error(f"⚠️ Could not find conflict proneness data at: {path}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"⚠️ Error loading conflict proneness data: {str(e)}")
        return pd.DataFrame()


@st.cache_data
def load_acled_events() -> pd.DataFrame:
    """
    Load ACLED event-level data with cause classifications.
    
    Returns:
        DataFrame with event details, dates, locations, and cause classifications.
    """
    try:
        path = DATA_DIR / 'acled_with_causes.csv'
        df = pd.read_csv(path)
        
        # Find and convert date column
        date_col = find_column(df, ['event_date', 'date', 'EVENT_DATE', 'Date', 'event_date_str'])
        if date_col:
            df['event_date'] = pd.to_datetime(df[date_col], errors='coerce')
        
        # Find and ensure numeric fatalities
        fatality_col = find_column(df, ['fatalities', 'FATALITIES', 'Fatalities', 'deaths', 'casualties', 'CASUALTIES'])
        if fatality_col:
            df['fatalities'] = pd.to_numeric(df[fatality_col], errors='coerce').fillna(0)
        else:
            # If no fatality column found, create one with zeros
            df['fatalities'] = 0
        
        # ✅ NORMALIZE STATE NAMES
        df = normalize_dataframe_states(df, state_column='ADMIN1')
        
        return df
    
    except FileNotFoundError:
        st.error(f"⚠️ Could not find ACLED events data at: {path}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"⚠️ Error loading ACLED events data: {str(e)}")
        return pd.DataFrame()


@st.cache_data
def load_causes_by_state() -> pd.DataFrame:
    """
    Load causes distribution aggregated by state.
    
    Returns:
        DataFrame with state-level causes breakdown.
    """
    try:
        path = DATA_DIR / 'causes_by_state.csv'
        df = pd.read_csv(path)
        
        # Ensure numeric columns
        numeric_cols = ['total_events', 'high_risk_events', 'political_events', 
                       'communal_events', 'resource_events', 'raw_causes_pct', 
                       'smoothed_causes_pct']
        
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # ✅ NORMALIZE STATE NAMES
        df = normalize_dataframe_states(df, state_column='state')
        
        return df
    
    except FileNotFoundError:
        st.warning(f"⚠️ Could not find causes by state data at: {path}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"⚠️ Error loading causes by state data: {str(e)}")
        return pd.DataFrame()


# ============================================================================
# SUMMARY STATISTICS
# ============================================================================

@st.cache_data
def get_summary_stats() -> Dict[str, any]:
    """
    Calculate summary statistics for the entire dataset.
    
    Returns:
        Dictionary with key metrics: total_events, total_fatalities, 
        states_affected, date_range, etc.
    """
    df_events = load_acled_events()
    df_cp = load_conflict_proneness()
    
    if df_events.empty:
        return {
            'total_events': 0,
            'total_fatalities': 0,
            'states_affected': 0,
            'date_range': 'N/A',
            'avg_cp_score': 0,
            'high_risk_states': 0
        }
    
    # Find fatalities column
    fatality_col = find_column(df_events, ['fatalities', 'FATALITIES', 'Fatalities', 'deaths', 'casualties'])
    total_fatalities = int(df_events[fatality_col].sum()) if fatality_col else 0
    
    # Find state/admin column
    state_col = find_column(df_events, ['admin1', 'ADM1_NAME', 'state', 'State', 'ADMIN1', 'region', 'Region'])
    states_affected = df_events[state_col].nunique() if state_col else len(df_cp)
    
    # Find date column
    date_col = find_column(df_events, ['event_date', 'date', 'EVENT_DATE', 'Date'])
    if date_col and 'event_date' not in df_events.columns:
        df_events['event_date'] = pd.to_datetime(df_events[date_col], errors='coerce')
    
    # Calculate date range
    if 'event_date' in df_events.columns:
        min_date = df_events['event_date'].min()
        max_date = df_events['event_date'].max()
        date_range = f"{min_date.strftime('%b %Y')} - {max_date.strftime('%b %Y')}"
    else:
        date_range = 'N/A'
    
    stats = {
        'total_events': len(df_events),
        'total_fatalities': total_fatalities,
        'states_affected': states_affected,
        'date_range': date_range,
        'avg_cp_score': round(df_cp['conflict_proneness_v2'].mean(), 2) if not df_cp.empty and 'conflict_proneness_v2' in df_cp.columns else 0,
        'high_risk_states': len(df_cp[df_cp['conflict_proneness_v2'] >= 7]) if not df_cp.empty and 'conflict_proneness_v2' in df_cp.columns else 0
    }
    
    return stats


# ============================================================================
# TIME SERIES DATA
# ============================================================================

@st.cache_data
def get_events_by_month() -> pd.DataFrame:
    """
    Aggregate events by month for time series analysis.
    
    Returns:
        DataFrame with monthly event counts and fatalities.
    """
    df = load_acled_events()
    
    if df.empty:
        return pd.DataFrame(columns=['month', 'events', 'fatalities'])
    
    # Ensure event_date exists
    if 'event_date' not in df.columns:
        date_col = find_column(df, ['event_date', 'date', 'EVENT_DATE', 'Date'])
        if date_col:
            df['event_date'] = pd.to_datetime(df[date_col], errors='coerce')
        else:
            return pd.DataFrame(columns=['month', 'events', 'fatalities'])
    
    # Remove rows with invalid dates
    df = df[df['event_date'].notna()]
    
    if df.empty:
        return pd.DataFrame(columns=['month', 'events', 'fatalities'])
    
    # Group by month
    df['year_month'] = df['event_date'].dt.to_period('M')
    
    # Find event ID column
    event_id_col = find_column(df, ['event_id_cnty', 'event_id', 'id', 'EVENT_ID'])
    
    # Find fatalities column
    fatality_col = find_column(df, ['fatalities', 'FATALITIES', 'Fatalities', 'deaths'])
    
    # Aggregate
    agg_dict = {}
    if event_id_col:
        agg_dict[event_id_col] = 'count'
    else:
        # If no ID column, just count rows
        df['_count'] = 1
        agg_dict['_count'] = 'sum'
    
    if fatality_col:
        agg_dict[fatality_col] = 'sum'
    
    monthly = df.groupby('year_month').agg(agg_dict).reset_index()
    
    # Rename columns
    monthly.columns = ['month', 'events', 'fatalities'] if fatality_col else ['month', 'events']
    if 'fatalities' not in monthly.columns:
        monthly['fatalities'] = 0
    
    monthly['month'] = monthly['month'].dt.to_timestamp()
    
    return monthly


@st.cache_data
def get_events_by_cause() -> pd.DataFrame:
    """
    Aggregate events by cause classification.
    
    Returns:
        DataFrame with event counts by cause type.
    """
    df = load_acled_events()
    
    if df.empty:
        return pd.DataFrame(columns=['cause', 'events'])
    
    # Find cause column
    cause_col = find_column(df, ['classified_cause', 'cause', 'CAUSE', 'Cause', 'cause_type'])
    
    if not cause_col:
        return pd.DataFrame(columns=['cause', 'events'])
    
    cause_counts = df[cause_col].value_counts().reset_index()
    cause_counts.columns = ['cause', 'events']
    
    return cause_counts


# ============================================================================
# FILTERED DATA
# ============================================================================

def filter_events_by_state(state: str) -> pd.DataFrame:
    """
    Filter events for a specific state.
    
    Args:
        state: State name to filter by
        
    Returns:
        Filtered DataFrame
    """
    df = load_acled_events()
    
    if df.empty:
        return pd.DataFrame()
    
    # Find state column
    state_col = find_column(df, ['admin1', 'ADM1_NAME', 'state', 'State', 'ADMIN1'])
    
    if not state_col:
        return pd.DataFrame()
    
    return df[df[state_col] == state].copy()


def filter_events_by_date_range(start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    """
    Filter events within a date range.
    
    Args:
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        
    Returns:
        Filtered DataFrame
    """
    df = load_acled_events()
    
    if df.empty:
        return pd.DataFrame()
    
    # Ensure event_date exists
    if 'event_date' not in df.columns:
        date_col = find_column(df, ['event_date', 'date', 'EVENT_DATE', 'Date'])
        if date_col:
            df['event_date'] = pd.to_datetime(df[date_col], errors='coerce')
        else:
            return pd.DataFrame()
    
    mask = (df['event_date'] >= start_date) & (df['event_date'] <= end_date)
    return df[mask].copy()


def filter_events_by_cause(cause_type: str) -> pd.DataFrame:
    """
    Filter events by cause classification.
    
    Args:
        cause_type: One of 'Political', 'Communal', 'Resource-based'
        
    Returns:
        Filtered DataFrame
    """
    df = load_acled_events()
    
    if df.empty:
        return pd.DataFrame()
    
    # Find cause column
    cause_col = find_column(df, ['classified_cause', 'cause', 'CAUSE', 'Cause'])
    
    if not cause_col:
        return pd.DataFrame()
    
    return df[df[cause_col] == cause_type].copy()


# ============================================================================
# RISK CATEGORIZATION
# ============================================================================

def get_risk_category(cp_score: float) -> str:
    """
    Categorize CP score into risk levels.
    
    Args:
        cp_score: Conflict Proneness score (1-10)
        
    Returns:
        Risk category string
    """
    if pd.isna(cp_score):
        return 'Unknown'
    elif cp_score >= 8:
        return 'Critical'
    elif cp_score >= 6:
        return 'High'
    elif cp_score >= 4:
        return 'Moderate'
    elif cp_score >= 2:
        return 'Low'
    else:
        return 'Very Low'


def get_risk_color(cp_score: float) -> str:
    """
    Get color code for CP score visualization.
    
    Args:
        cp_score: Conflict Proneness score (1-10)
        
    Returns:
        Hex color code
    """
    if pd.isna(cp_score):
        return '#9ca3af'  # Gray (Unknown)
    elif cp_score >= 8:
        return '#dc2626'  # Red (Critical)
    elif cp_score >= 6:
        return '#f59e0b'  # Orange (High)
    elif cp_score >= 4:
        return '#fbbf24'  # Yellow (Moderate)
    elif cp_score >= 2:
        return '#10b981'  # Green (Low)
    else:
        return '#6ee7b7'  # Light Green (Very Low)


def add_risk_category_column(df: pd.DataFrame, cp_col: str = 'conflict_proneness_v2') -> pd.DataFrame:
    """
    Add risk category column to DataFrame.
    
    Args:
        df: DataFrame with CP scores
        cp_col: Name of CP score column
        
    Returns:
        DataFrame with added 'risk_category' column
    """
    if cp_col in df.columns:
        df['risk_category'] = df[cp_col].apply(get_risk_category)
        df['risk_color'] = df[cp_col].apply(get_risk_color)
    return df


# ============================================================================
# DATA VALIDATION
# ============================================================================

def validate_data_availability() -> Dict[str, bool]:
    """
    Check which datasets are available and properly loaded.
    
    Returns:
        Dictionary of dataset availability status.
    """
    status = {
        'conflict_proneness': not load_conflict_proneness().empty,
        'acled_events': not load_acled_events().empty,
        'causes_by_state': not load_causes_by_state().empty
    }
    
    return status


def get_data_info() -> Dict[str, any]:
    """
    Get detailed information about loaded datasets.
    
    Returns:
        Dictionary with dataset details.
    """
    df_cp = load_conflict_proneness()
    df_events = load_acled_events()
    df_causes = load_causes_by_state()
    
    info = {
        'conflict_proneness': {
            'rows': len(df_cp),
            'columns': list(df_cp.columns) if not df_cp.empty else [],
            'available': not df_cp.empty
        },
        'acled_events': {
            'rows': len(df_events),
            'columns': list(df_events.columns) if not df_events.empty else [],
            'available': not df_events.empty
        },
        'causes_by_state': {
            'rows': len(df_causes),
            'columns': list(df_causes.columns) if not df_causes.empty else [],
            'available': not df_causes.empty
        }
    }
    
    return info


# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

def export_to_csv(df: pd.DataFrame, filename: str) -> bytes:
    """
    Convert DataFrame to CSV bytes for download.
    
    Args:
        df: DataFrame to export
        filename: Suggested filename
        
    Returns:
        CSV data as bytes
    """
    return df.to_csv(index=False).encode('utf-8')


# ============================================================================
# INITIALIZATION
# ============================================================================

if __name__ == "__main__":
    # Test data loading
    print("=" * 80)
    print("TESTING DATA LOADER")
    print("=" * 80)
    
    print(f"\nProject Root: {PROJECT_ROOT}")
    print(f"Data Directory: {DATA_DIR}")
    
    print("\n" + "-" * 80)
    print("CONFLICT PRONENESS DATA")
    print("-" * 80)
    cp_df = load_conflict_proneness()
    print(f"Loaded {len(cp_df)} states")
    if not cp_df.empty:
        print(f"Columns: {cp_df.columns.tolist()}")
        print("\nFirst 5 rows:")
        print(cp_df.head())
        print(f"\nCP Score Range: {cp_df['conflict_proneness_v2'].min():.2f} - {cp_df['conflict_proneness_v2'].max():.2f}")
    
    print("\n" + "-" * 80)
    print("ACLED EVENTS DATA")
    print("-" * 80)
    events_df = load_acled_events()
    print(f"Loaded {len(events_df)} events")
    if not events_df.empty:
        print(f"Columns: {events_df.columns.tolist()}")
        print("\nFirst 5 rows:")
        print(events_df.head())
    
    print("\n" + "-" * 80)
    print("CAUSES BY STATE DATA")
    print("-" * 80)
    causes_df = load_causes_by_state()
    print(f"Loaded {len(causes_df)} states")
    if not causes_df.empty:
        print(f"Columns: {causes_df.columns.tolist()}")
        print("\nFirst 5 rows:")
        print(causes_df.head())
    
    print("\n" + "-" * 80)
    print("SUMMARY STATISTICS")
    print("-" * 80)
    stats = get_summary_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print("\n" + "-" * 80)
    print("DATA AVAILABILITY")
    print("-" * 80)
    availability = validate_data_availability()
    for dataset, available in availability.items():
        status = "✅ Available" if available else "❌ Missing"
        print(f"{dataset}: {status}")
    
    print("\n" + "-" * 80)
    print("EVENTS BY MONTH")
    print("-" * 80)
    monthly_df = get_events_by_month()
    print(f"Monthly data points: {len(monthly_df)}")
    if not monthly_df.empty:
        print(monthly_df.head(10))
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)
