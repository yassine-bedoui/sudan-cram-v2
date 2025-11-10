# scripts/gdelt/fetch_sudan_events.py
"""
Fetch Sudan events from GDELT 2.0 with Goldstein Scale
PROVEN TO WORK: Uses 'SU' country code
DEFAULT: Fetches last 7 days for better trend analysis
"""
import pandas as pd
import requests
import zipfile
from io import BytesIO
from datetime import datetime
import os

def fetch_sudan_from_file(url):
    """Download and filter one GDELT file for Sudan"""
    try:
        response = requests.get(url, timeout=30)
        content = BytesIO(response.content)
        
        with zipfile.ZipFile(content) as z:
            csv_file = z.namelist()[0]
            with z.open(csv_file) as f:
                # Read with column 53 = ActionGeo_CountryCode
                df = pd.read_csv(
                    f,
                    sep='\t',
                    header=None,
                    low_memory=False,
                    on_bad_lines='skip'
                )
        
        # Filter for Sudan (column 53 = 'SU')
        sudan = df[df[53] == 'SU'].copy()
        
        if sudan.empty:
            return pd.DataFrame()
        
        # Extract key columns
        result = pd.DataFrame({
            'date': sudan[1],  # SQLDATE
            'event_code': sudan[26],  # EventCode
            'goldstein': sudan[30],  # GoldsteinScale
            'num_mentions': sudan[31],  # NumMentions
            'avg_tone': sudan[33],  # AvgTone
            'actor1': sudan[6],  # Actor1Name
            'actor2': sudan[16],  # Actor2Name
            'location': sudan[52],  # ActionGeo_Fullname
            'latitude': sudan[55],  # ActionGeo_Lat
            'longitude': sudan[56],  # ActionGeo_Long
            'source_url': sudan[58]  # SOURCEURL
        })
        
        return result
    
    except Exception as e:
        return pd.DataFrame()

def fetch_sudan_events(hours=168):  # 7 days = 168 hours
    """
    Fetch recent Sudan events
    Default: last 7 days (168 hours) for better trend analysis
    """
    
    days = hours // 24
    print(f"\n🇸🇩 FETCHING SUDAN EVENTS (Last {days} days / {hours} hours)\n")
    print("=" * 70)
    
    # Get masterfilelist (takes ~10 seconds, large file)
    print("📡 Downloading GDELT masterfilelist (this may take 10-15 seconds)...")
    masterlist_url = "http://data.gdeltproject.org/gdeltv2/masterfilelist.txt"
    response = requests.get(masterlist_url)
    
    lines = response.text.strip().split('\n')
    export_urls = [line.split()[2] for line in lines if '.export.CSV.zip' in line]
    
    # Reverse to get newest first
    export_urls = list(reversed(export_urls))
    
    # Calculate number of files (4 per hour = 15-minute intervals)
    num_files = min(hours * 4, len(export_urls))
    file_urls = export_urls[:num_files]
    
    print(f"✅ Found {len(export_urls):,} total files in GDELT")
    print(f"📥 Processing {num_files} most recent files ({days} days)...")
    print("   This will take ~5-10 minutes for 7 days of data...")
    print("=" * 70)
    
    all_events = []
    processed = 0
    
    for i, url in enumerate(file_urls, 1):
        filename = url.split('/')[-1][:15]
        
        events = fetch_sudan_from_file(url)
        
        if not events.empty:
            all_events.append(events)
            print(f"[{i:3d}/{num_files}] {filename} ✅ {len(events):2d} events")
        elif i % 20 == 0:  # Show progress every 20 files
            print(f"[{i:3d}/{num_files}] ... ({i/num_files*100:.0f}% complete)")
        
        processed += 1
        
        # Milestone updates
        if processed in [num_files//4, num_files//2, 3*num_files//4]:
            total_so_far = sum(len(e) for e in all_events)
            print(f"\n  📊 Progress: {processed}/{num_files} files | {total_so_far} Sudan events so far...\n")
    
    print("=" * 70)
    
    if not all_events:
        print("\n❌ No Sudan events found")
        print("   Try different date range or check GDELT availability")
        return pd.DataFrame()
    
    # Combine
    combined = pd.concat(all_events, ignore_index=True)
    combined['date'] = pd.to_datetime(combined['date'], format='%Y%m%d')
    
    # Deduplicate
    original_count = len(combined)
    combined = combined.drop_duplicates(subset=['date', 'event_code', 'location'])
    deduped = original_count - len(combined)
    
    # Save
    os.makedirs('data/gdelt', exist_ok=True)
    output_file = f'data/gdelt/sudan_events_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
    combined.to_csv(output_file, index=False)
    
    # Summary
    print(f"\n📊 SUMMARY")
    print("=" * 70)
    print(f"Total events:       {len(combined):,} (removed {deduped} duplicates)")
    print(f"Date range:         {combined['date'].min().date()} → {combined['date'].max().date()}")
    print(f"Days covered:       {(combined['date'].max() - combined['date'].min()).days} days")
    print(f"Avg Goldstein:      {combined['goldstein'].mean():.2f} (negative = conflict)")
    print(f"Median Goldstein:   {combined['goldstein'].median():.2f}")
    print(f"Media mentions:     {combined['num_mentions'].sum():,}")
    print(f"Unique locations:   {combined['location'].nunique()}")
    print(f"💾 Saved to:         {output_file}")
    
    print(f"\n🌍 TOP 10 LOCATIONS (by event count):")
    location_counts = combined['location'].value_counts().head(10)
    for loc, count in location_counts.items():
        avg_gold = combined[combined['location'] == loc]['goldstein'].mean()
        print(f"  {loc[:50]:<50} {count:>3} events (avg Goldstein: {avg_gold:>5.1f})")
    
    print(f"\n🚨 MOST ESCALATORY EVENTS (Goldstein ≤ -5):")
    escalatory = combined[combined['goldstein'] <= -5].sort_values('goldstein').head(10)
    
    if len(escalatory) > 0:
        for i, (_, e) in enumerate(escalatory.iterrows(), 1):
            print(f"  {i}. {e['location']}: Goldstein {e['goldstein']:.1f} (Event {e['event_code']})")
            print(f"     {e['date'].date()}, Mentions: {e['num_mentions']}")
    else:
        print("  No extreme escalatory events (Goldstein ≤ -5) in this period")
    
    # Event type breakdown
    print(f"\n📈 EVENT TYPE BREAKDOWN (CAMEO Codes):")
    event_types = combined.groupby('event_code').agg({
        'goldstein': ['count', 'mean']
    }).sort_values(('goldstein', 'count'), ascending=False).head(5)
    event_types.columns = ['Count', 'Avg Goldstein']
    print(event_types.to_string())
    
    print("\n" + "=" * 70)
    print("✅ GDELT INTEGRATION COMPLETE!")
    print("=" * 70)
    
    return combined

if __name__ == '__main__':
    # Fetch last 7 days (672 files) - optimal for trend analysis
    events = fetch_sudan_events(hours=168)
    
    if not events.empty:
        print("\n📋 NEXT STEPS:")
        print("  1. Run: python scripts/gdelt/analyze_goldstein_trends.py")
        print("  2. Integrate with CRAM backend API")
        print("  3. Build dashboard visualization")
        print("\n  For real-time updates, run this script every 6-12 hours")
