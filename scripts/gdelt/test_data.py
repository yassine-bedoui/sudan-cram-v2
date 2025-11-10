# scripts/gdelt/diagnose_sudan_coverage.py
"""
Diagnose Sudan coverage in GDELT to find the right approach
"""
import pandas as pd
import requests
import zipfile
from io import BytesIO
from datetime import datetime, timedelta

def test_single_recent_file():
    """
    Download ONE recent file and inspect all country codes
    """
    print("🔍 DIAGNOSTIC: Testing one recent GDELT file...\n")
    
    # Get masterfilelist
    masterlist_url = "http://data.gdeltproject.org/gdeltv2/masterfilelist.txt"
    response = requests.get(masterlist_url)
    
    # Get URLs
    lines = response.text.strip().split('\n')
    export_urls = [line.split()[2] for line in lines if '.export.CSV.zip' in line]
    
    # REVERSE to get newest
    export_urls = list(reversed(export_urls))
    
    # Test the MOST RECENT file
    test_url = export_urls[0]
    filename = test_url.split('/')[-1]
    
    print(f"📥 Testing file: {filename}")
    print(f"    URL: {test_url}\n")
    
    try:
        # Download
        response = requests.get(test_url, timeout=30)
        content = BytesIO(response.content)
        
        # Unzip
        with zipfile.ZipFile(content) as z:
            csv_file = z.namelist()[0]
            with z.open(csv_file) as f:
                # Read with ALL columns
                df = pd.read_csv(
                    f,
                    sep='\t',
                    header=None,
                    low_memory=False
                )
        
        print(f"✅ File loaded: {len(df)} total events\n")
        
        # GDELT 2.0 column 53 = ActionGeo_CountryCode
        if len(df.columns) > 53:
            country_col = df.iloc[:, 53]  # Column 53 (0-indexed)
            
            print("🌍 Top 20 countries in this file:")
            print(country_col.value_counts().head(20))
            
            # Check for Sudan variants
            print("\n🇸🇩 Checking Sudan variants:")
            sudan_variants = ['SU', 'SD', 'SDN', 'SUDAN']
            for variant in sudan_variants:
                count = (country_col == variant).sum()
                if count > 0:
                    print(f"   ✅ '{variant}': {count} events")
                else:
                    print(f"   ❌ '{variant}': 0 events")
            
            # Show sample Sudan events if any
            sudan_mask = country_col.isin(sudan_variants)
            if sudan_mask.sum() > 0:
                print(f"\n📰 Sample Sudan event:")
                sample = df[sudan_mask].iloc[0]
                print(f"   Date: {sample[1]}")  # Col 1 = SQLDATE
                print(f"   Event Code: {sample[26]}")  # Col 26 = EventCode
                print(f"   Goldstein: {sample[30]}")  # Col 30 = GoldsteinScale
                print(f"   Location: {sample[52]}")  # Col 52 = ActionGeo_Fullname
            
        else:
            print(f"⚠️ File has only {len(df.columns)} columns (expected 60+)")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def scan_historical_coverage(days_back=30):
    """
    Scan last N days to find when Sudan events exist
    """
    print(f"\n\n🔍 SCANNING LAST {days_back} DAYS FOR SUDAN COVERAGE...\n")
    
    masterlist_url = "http://data.gdeltproject.org/gdeltv2/masterfilelist.txt"
    response = requests.get(masterlist_url)
    
    lines = response.text.strip().split('\n')
    export_urls = [line.split()[2] for line in lines if '.export.CSV.zip' in line]
    export_urls = list(reversed(export_urls))
    
    # Sample every 24 files (6 hours)
    sample_urls = export_urls[::24][:days_back*4]  # 4 samples per day
    
    sudan_found = []
    
    for url in sample_urls:
        filename = url.split('/')[-1]
        date_str = filename[:8]
        
        try:
            response = requests.get(url, timeout=20)
            content = BytesIO(response.content)
            
            with zipfile.ZipFile(content) as z:
                csv_file = z.namelist()[0]
                with z.open(csv_file) as f:
                    df = pd.read_csv(f, sep='\t', header=None, low_memory=False, usecols=[53])
            
            sudan_count = (df[53] == 'SU').sum() + (df[53] == 'SD').sum()
            
            if sudan_count > 0:
                print(f"✅ {date_str}: {sudan_count} Sudan events")
                sudan_found.append((date_str, sudan_count))
            else:
                print(f"⚫ {date_str}: No Sudan events")
        
        except Exception as e:
            print(f"⚠️ {date_str}: Error - {str(e)[:50]}")
    
    if sudan_found:
        print(f"\n✅ Found Sudan events in {len(sudan_found)} time periods!")
        print("   Use these dates for historical data collection")
    else:
        print(f"\n❌ No Sudan events found in last {days_back} days")
        print("   This suggests:")
        print("   • Sudan country code might have changed")
        print("   • Limited international media coverage")
        print("   • Need to check ACLED instead")

if __name__ == '__main__':
    print("=" * 60)
    print("GDELT SUDAN COVERAGE DIAGNOSTIC")
    print("=" * 60)
    
    # Test 1: Check one recent file in detail
    test_single_recent_file()
    
    # Test 2: Scan last 7 days
    scan_historical_coverage(days_back=7)
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)
