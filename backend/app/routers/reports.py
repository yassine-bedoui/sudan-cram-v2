from fastapi import APIRouter, HTTPException
from datetime import datetime
import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
CP_FILE = DATA_DIR / "conflict_proneness_v2.csv"

def load_conflict_proneness_data():
    """Load conflict proneness data from CSV"""
    try:
        return pd.read_csv(CP_FILE)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Data file not found: {CP_FILE}")

@router.post("/generate-brief")
async def generate_brief():
    """Generate daily brief using Conflict Proneness data"""
    try:
        logger.info("Starting brief generation...")

        # Load conflict proneness data
        df = load_conflict_proneness_data()
        logger.info(f"Data loaded: {len(df)} rows")

        # Group by region
        region_summary = df.groupby('region').agg({
            'incidents': 'sum',
            'fatalities': 'sum',
            'conflict_proneness': 'first'
        }).reset_index()

        logger.info(f"Regions summarized: {len(region_summary)}")

        # Build brief data dict
        brief_data = {}
        max_incidents = region_summary['incidents'].max()

        for _, row in region_summary.iterrows():
            region = row['region']
            incidents = int(row['incidents'])
            fatalities = int(row['fatalities'])
            cp_score = float(row['conflict_proneness'])

            # Determine category
            if cp_score >= 7:
                category = 'SEVERE'
            elif cp_score >= 5:
                category = 'HIGH'
            elif cp_score >= 3:
                category = 'MEDIUM'
            else:
                category = 'LOW'

            brief_data[region] = {
                'cp_score': cp_score,
                'incidents': incidents,
                'fatalities': fatalities,
                'category': category
            }

        logger.info(f"Brief data prepared for {len(brief_data)} regions")

        # Simple brief generation (without Groq for now)
        brief_text = f"Sudan Conflict Analysis Report\n"
        brief_text += f"Total Regions: {len(region_summary)}\n"
        brief_text += f"Total Incidents: {int(region_summary['incidents'].sum())}\n"
        brief_text += f"Total Fatalities: {int(region_summary['fatalities'].sum())}\n"
        brief_text += f"High Risk Regions: {(df['proneness_level'].isin(['EXTREME', 'VERY HIGH'])).sum()}"

        logger.info("Brief generation complete")

        return {
            "brief": brief_text,
            "generated_at": datetime.now().isoformat(),
            "regions_analyzed": len(brief_data),
            "total_events": int(region_summary['incidents'].sum()),
            "total_fatalities": int(region_summary['fatalities'].sum())
        }

    except Exception as e:
        logger.error(f"Error in generate_brief: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.get("/reports")
async def get_reports():
    """Get list of past reports"""
    return {
        "reports": [],
        "message": "Click 'Generate New Brief' to create your first report"
    }
