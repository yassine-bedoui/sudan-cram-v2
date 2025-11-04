"""
Data Loader for Sudan CRAM v2
Handles loading all data files from data/processed directory
"""
import pandas as pd
from pathlib import Path
import json
from typing import Dict, Any
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataLoader:
    """Central data loader for all Sudan CRAM datasets"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent
        self.data_dir = self.base_dir / "data" / "processed"
        logger.info(f"Data directory: {self.data_dir}")
        
    def _load_csv(self, filename: str) -> pd.DataFrame:
        """Helper method to load CSV files with error handling"""
        file_path = self.data_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Loaded {filename}: {len(df)} records")
            return df
        except Exception as e:
            logger.error(f"Error loading {filename}: {str(e)}")
            raise
    
    def _load_json(self, filename: str) -> Dict[str, Any]:
        """Helper method to load JSON files with error handling"""
        file_path = self.data_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded {filename}")
            return data
        except Exception as e:
            logger.error(f"Error loading {filename}: {str(e)}")
            raise
    
    # ===== PRIMARY DATA SOURCES =====
    
    def load_conflict_data(self) -> pd.DataFrame:
        """Load ACLED conflict events with causes (383KB)"""
        return self._load_csv("acled_with_causes.csv")
    
    def load_causes_by_state(self) -> pd.DataFrame:
        """Load conflict causes aggregated by state"""
        return self._load_csv("causes_by_state.csv")
    
    def load_conflict_proneness(self) -> pd.DataFrame:
        """Load conflict proneness scores v2 with causes"""
        return self._load_csv("conflict_proneness_v2_with_causes.csv")
    
    # ===== RISK ASSESSMENT DATA =====
    
    def load_risk_scores(self) -> pd.DataFrame:
        """Load comprehensive risk assessment scores (12KB)"""
        return self._load_csv("risk_scores.csv")
    
    def load_combined_risk(self) -> pd.DataFrame:
        """Load combined risk indicators v2"""
        return self._load_csv("combined_risk_v2.csv")
    
    def load_combined_risk_igad(self) -> pd.DataFrame:
        """Load combined risk indicators v2 with IGAD data"""
        return self._load_csv("combined_risk_v2_igad.csv")
    
    def load_political_risk(self) -> pd.DataFrame:
        """Load political risk analysis"""
        return self._load_csv("political_risk_v2.csv")
    
    def load_climate_risk(self) -> pd.DataFrame:
        """Load climate risk data (CDI v2 real)"""
        return self._load_csv("climate_risk_cdi_v2_real.csv")
    
    def load_climate_risk_v2(self) -> pd.DataFrame:
        """Load climate risk data (CDI v2 alternative)"""
        return self._load_csv("climate_risk_cdi_v2.csv")
    
    # ===== LEGACY/VERSIONED DATA =====
    
    def load_conflict_proneness_v1(self) -> pd.DataFrame:
        """Load conflict proneness scores v1 (legacy)"""
        return self._load_csv("conflict_proneness_v1.csv")
    
    # ===== CLIMATE/WEATHER DATA =====
    
    def load_chirps_data(self) -> pd.DataFrame:
        """Load CHIRPS Sudan admin1 monthly rainfall data"""
        return self._load_csv("chirps_sudan_admin1_monthly.csv")
    
    # ===== ALERTS & CONFIGURATION =====
    
    def load_alerts(self) -> Dict[str, Any]:
        """Load alert configuration and data (JSON)"""
        return self._load_json("alerts.json")
    
    # ===== VALIDATION DATA =====
    
    def load_validation_sample(self) -> pd.DataFrame:
        """Load data validation sample"""
        return self._load_csv("validation_sample.csv")
    
    def load_validation_report(self) -> str:
        """Load validation report (text)"""
        file_path = self.data_dir / "validation_report.txt"
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r') as f:
            return f.read()
    
    # ===== UTILITY METHODS =====
    
    def get_data_directory(self) -> Path:
        """Return the data directory path"""
        return self.data_dir
    
    def list_available_files(self) -> list:
        """List all available data files"""
        files = list(self.data_dir.glob("*"))
        return [f.name for f in files if f.is_file()]
    
    def get_file_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all data files"""
        info = {}
        for file in self.data_dir.glob("*"):
            if file.is_file():
                size_mb = file.stat().st_size / (1024 * 1024)
                info[file.name] = {
                    "size_mb": round(size_mb, 2),
                    "size_bytes": file.stat().st_size,
                    "extension": file.suffix
                }
        return info

