"""
AI Brief Generator - CRAM Data Only
Generates conflict analysis summaries using Groq AI
"""
import os
import logging
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Available Groq models in priority order
AVAILABLE_MODELS = [
    "gemma2-9b-it",
    "mixtral-8x7b-32768",
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
]

def get_available_model(client: Groq) -> str:
    """Find first available Groq model"""
    logger.info("Checking available Groq models...")
    
    for model in AVAILABLE_MODELS:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            logger.info(f"✅ Using model: {model}")
            return model
        except Exception as e:
            logger.warning(f"❌ Model {model} unavailable: {str(e)[:50]}")
            continue
    
    logger.warning("Using fallback model")
    return "gemma2-9b-it"

def generate_daily_brief(cram_data: dict) -> str:
    """
    Generate AI brief from CRAM conflict data
    
    Args:
        cram_data: Dict with regional risk scores, events, fatalities
    
    Returns:
        Markdown formatted brief
    """
    load_dotenv()
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Build prompt for AI
    prompt = f"""You are a Sudan conflict analyst. Today is {today}.

CONFLICT RISK DATA (CRAM Analysis):
{format_cram_data(cram_data)}

Generate a professional conflict analysis brief with these sections:

## Executive Summary
2-3 key findings highlighting highest risk areas

## Regional Risk Assessment
Organize by risk level (SEVERE → HIGH → MEDIUM → LOW)
For each region, mention event count, fatalities, and trends

## Humanitarian Implications
Based on conflict intensity and fatality data, what are the humanitarian concerns?

## Key Recommendations
3-5 actionable steps for field operations and response teams

Keep it factual, concise, and actionable. Focus on what decision-makers need to know."""
    
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return f"# Sudan Daily Brief – {today}\n\n❌ Error: GROQ_API_KEY not configured in .env"
        
        client = Groq(api_key=api_key)
        model = get_available_model(client)
        
        # Generate brief
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.3
        )
        
        brief = response.choices[0].message.content
        header = f"# Sudan Daily Brief – {today}\n\n*Generated using Groq AI ({model})*\n\n---\n\n"
        
        logger.info(f"✅ Brief generated with {model}")
        return header + brief
    
    except Exception as e:
        logger.error(f"Error: {e}")
        return f"# Sudan Daily Brief – {today}\n\n❌ Error: {str(e)}"

def format_cram_data(cram_data: dict) -> str:
    """Format CRAM data for AI prompt"""
    if not cram_data:
        return "No data available"
    
    formatted = ""
    for region, data in cram_data.items():
        risk = data.get('risk_score', 0)
        events = data.get('events', 0)
        fatalities = data.get('fatalities', 0)
        category = data.get('category', 'UNKNOWN')
        trend = data.get('trend', 'stable')
        
        formatted += f"\n- **{region}** [{category}]: Risk {risk}/10 | {events} events | {fatalities} fatalities | Trend: {trend}"
    
    return formatted
