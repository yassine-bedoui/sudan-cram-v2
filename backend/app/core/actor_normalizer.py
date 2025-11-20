"""
Actor Name Normalization Utility
Ensures consistent and standardized naming of actors (armed groups, political entities)
across all conflict event annotations.
"""

# Mapping of common actor name variants to canonical names
ACTOR_MAPPINGS = {
    'SPLA': 'Sudan People’s Liberation Army',
    'JEM': 'Justice and Equality Movement',
    'RSF': 'Rapid Support Forces',
    'SPLM-N': 'Sudan People’s Liberation Movement-North',
    'SPLM': 'Sudan People’s Liberation Movement',
    'SAF': 'Sudanese Armed Forces',
    'NCP': 'National Congress Party',
    # Add more known mappings based on your domain knowledge
}

def normalize_actor(name: str) -> str:
    """
    Normalize actor name to a canonical form.

    Args:
        name (str): Raw actor name (may contain abbreviations or variants)

    Returns:
        str: Normalized actor name or original if no mapping found
    """
    if not name or not isinstance(name, str):
        return name

    candidate = name.strip().upper()
    normalized = ACTOR_MAPPINGS.get(candidate) or ACTOR_MAPPINGS.get(name.strip()) or name.strip()

    return normalized
