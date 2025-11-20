"""
State Name Normalization Utility
Ensures consistent spelling across all visualizations
"""

# State name mappings - normalize all variations to official spelling
STATE_NAME_MAPPINGS = {
    # Al Jazirah variations
    'Aj Jazirah': 'Al Jazirah',
    'Al-Jazirah': 'Al Jazirah',
    'Gezira': 'Al Jazirah',
    'Al Gezira': 'Al Jazirah',

    # Add other known variations if needed
    'River Nile': 'River Nile',
    'Northern': 'Northern',
    # Add lowercase variants for robustness
    'aj jazirah': 'Al Jazirah',
    'al-jazirah': 'Al Jazirah',
    'gezira': 'Al Jazirah',
    'al gezira': 'Al Jazirah',
}

# Official state names (18 states)
OFFICIAL_STATE_NAMES = [
    'Al Jazirah',
    'Blue Nile',
    'Central Darfur',
    'East Darfur',
    'Gedaref',
    'Kassala',
    'Khartoum',
    'North Darfur',
    'North Kordofan',
    'Northern',
    'Red Sea',
    'River Nile',
    'Sennar',
    'South Darfur',
    'South Kordofan',
    'West Darfur',
    'West Kordofan',
    'White Nile'
]

def normalize_state_name(state_name):
    """
    Normalize state name to official spelling

    Args:
        state_name (str): Input state name (any variation)

    Returns:
        str: Normalized state name
    """
    if not state_name or not isinstance(state_name, str):
        return state_name

    # Strip whitespace and lowercase for matching
    state_name_clean = state_name.strip()
    state_name_lower = state_name_clean.lower()

    # Check if already normalized (case-insensitive)
    for official in OFFICIAL_STATE_NAMES:
        if official.lower() == state_name_lower:
            return official

    # Apply mapping (case-insensitive)
    normalized = STATE_NAME_MAPPINGS.get(state_name_clean)
    if not normalized:
        normalized = STATE_NAME_MAPPINGS.get(state_name_lower)

    return normalized or state_name_clean

def normalize_dataframe_states(df, state_column):
    """
    Normalize all state names in a dataframe

    Args:
        df (pd.DataFrame): Input dataframe
        state_column (str): Name of column containing state names

    Returns:
        pd.DataFrame: Dataframe with normalized state names
    """
    import pandas as pd
    df = df.copy()

    if state_column in df.columns:
        df[state_column] = df[state_column].apply(normalize_state_name)

    return df
