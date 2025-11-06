"""
Sudan CRAM - Bivariate Data Loader
Loads Climate Risk + Conflict Risk (SEPARATE dimensions)
"""
import pandas as pd
import json
from pathlib import Path

class BivariateCRAMLoader:
    def __init__(self, data_dir="data/processed"):
        self.data_dir = Path(data_dir)
        self.climate_df = None
        self.conflict_df = None
        self.combined = None
    
    def load_data(self):
        """Load climate and conflict risk data"""
        # Load climate risk (IGAD CDI)
        self.climate_df = pd.read_csv(
            self.data_dir / 'climate_risk_cdi_v2_real.csv'
        )
        
        # Load conflict risk (political violence)
        self.conflict_df = pd.read_csv(
            self.data_dir / 'political_risk_v2.csv'
        )
        
        # Merge on region name
        self.combined = self.climate_df.merge(
            self.conflict_df[['ADM1_NAME', 'political_risk_score', 'events_6m', 'fatalities_6m']],
            on='ADM1_NAME',
            how='left'
        )
        
        return self.combined
    
    def create_bivariate_category(self, climate_score, conflict_score):
        """Create bivariate category from two scores"""
        # Climate levels
        if climate_score >= 7:
            climate_level = "severe"
        elif climate_score >= 5:
            climate_level = "high"
        elif climate_score >= 3:
            climate_level = "medium"
        else:
            climate_level = "low"
        
        # Conflict levels
        if conflict_score >= 8:
            conflict_level = "extreme"
        elif conflict_score >= 6:
            conflict_level = "very_high"
        elif conflict_score >= 4:
            conflict_level = "high"
        elif conflict_score >= 2:
            conflict_level = "moderate"
        else:
            conflict_level = "low"
        
        return f"{climate_level}_climate_{conflict_level}_conflict"
    
    def get_api_format(self):
        """Convert to API response format"""
        if self.combined is None:
            self.load_data()
        
        regions = []
        for _, row in self.combined.iterrows():
            bivariate = self.create_bivariate_category(
                row['climate_risk_score'],
                row['political_risk_score']
            )
            
            regions.append({
                'region': row['ADM1_NAME'],
                'climate_risk_score': round(row['climate_risk_score'], 2),
                'climate_risk_level': row['cdi_category'],
                'conflict_risk_score': round(row['political_risk_score'], 2),
                'conflict_risk_level': row['risk_category'],
                'bivariate_category': bivariate,
                'events_6m': int(row['events_6m']),
                'fatalities_6m': int(row['fatalities_6m'])
            })
        
        return {'regions': regions}

if __name__ == "__main__":
    loader = BivariateCRAMLoader()
    data = loader.get_api_format()
    print(json.dumps(data, indent=2))
