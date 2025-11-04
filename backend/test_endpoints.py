import sys
sys.path.insert(0, '.')

from app.utils.data_loader import DataLoader
import traceback

loader = DataLoader()

endpoints = [
    ("conflict_proneness", loader.load_conflict_proneness),
    ("combined_risk", loader.load_combined_risk),
    ("validation_sample", loader.load_validation_sample)
]

for name, func in endpoints:
    try:
        df = func()
        print(f"✅ {name}: {len(df)} rows")
        # Try to convert to dict (this is what the API does)
        data = df.to_dict(orient="records")
        print(f"   ✓ Conversion successful")
    except Exception as e:
        print(f"❌ {name}: {type(e).__name__}")
        print(f"   Error: {str(e)}")
        traceback.print_exc()
    print()
