from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.groq_brief import generate_daily_brief
from app.routers.analytics import load_data
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/generate-brief")
async def generate_brief():
    """Generate AI-powered daily brief using CRAM data"""
    try:
        logger.info("Starting brief generation...")
        
        # Load data
        df = load_data()
        logger.info(f"Data loaded: {len(df)} rows")
        
        # Group by ADMIN1 (uppercase) and sum EVENTS and FATALITIES
        region_summary = df.groupby('ADMIN1').agg({
            'EVENTS': 'sum',
            'FATALITIES': 'sum'
        }).reset_index()
        
        logger.info(f"Regions summarized: {len(region_summary)}")
        
        # Build CRAM data dict
        cram_data = {}
        max_events = region_summary['EVENTS'].max()
        
        for _, row in region_summary.iterrows():
            region = row['ADMIN1']
            events = int(row['EVENTS'])
            fatalities = int(row['FATALITIES'])
            
            # Calculate risk score (0-10 scale)
            risk_score = round((events / max_events) * 10, 1) if max_events > 0 else 0
            
            # Determine category
            if risk_score >= 8:
                category = 'SEVERE'
            elif risk_score >= 6:
                category = 'HIGH'
            elif risk_score >= 3:
                category = 'MEDIUM'
            else:
                category = 'LOW'
            
            trend = 'stable'  # Placeholder
            
            cram_data[region] = {
                'risk_score': risk_score,
                'events': events,
                'fatalities': fatalities,
                'category': category,
                'trend': trend
            }
        
        logger.info(f"CRAM data prepared for {len(cram_data)} regions")
        logger.info(f"Sample region data: {list(cram_data.items())[0]}")
        
        # Generate AI brief
        brief = generate_daily_brief(cram_data)
        logger.info("Brief generation complete")
        
        return {
            "brief": brief,
            "generated_at": datetime.now().isoformat(),
            "regions_analyzed": len(cram_data),
            "total_events": int(region_summary['EVENTS'].sum()),
            "total_fatalities": int(region_summary['FATALITIES'].sum())
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
