"""Download and import GTFS data from National Transport Authority"""
import sys
import os
import requests
import zipfile
import csv
from pathlib import Path
from io import BytesIO

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import app, db
from models import TransportStation

# GTFS data URL (static data) - Transport for Ireland
GTFS_URL = "https://www.transportforireland.ie/transitData/Data/GTFS_All.zip"

def download_gtfs():
    """Download GTFS zip file"""
    print("Downloading GTFS data from Transport for Ireland...")
    print(f"URL: {GTFS_URL}\n")
    
    response = requests.get(GTFS_URL, timeout=60)
    response.raise_for_status()
    
    print(f"✓ Downloaded {len(response.content) / 1024 / 1024:.1f} MB\n")
    return BytesIO(response.content)

def import_bus_stops(zip_file):
    """Import bus stops from GTFS stops.txt"""
    
    with app.app_context():
        with zipfile.ZipFile(zip_file) as z:
            # Read stops.txt
            with z.open('stops.txt') as f:
                # Decode and read CSV
                content = f.read().decode('utf-8-sig')
                reader = csv.DictReader(content.splitlines())
                
                print("Importing bus stops...")
                print("="*70)
                
                imported = 0
                skipped = 0
                
                for row in reader:
                    stop_id = row.get('stop_id')
                    stop_name = row.get('stop_name')
                    stop_lat = row.get('stop_lat')
                    stop_lon = row.get('stop_lon')
                    
                    # Skip if missing essential data
                    if not all([stop_id, stop_name, stop_lat, stop_lon]):
                        skipped += 1
                        continue
                    
                    # Check if already exists (by external_id which stores stop_id)
                    existing = TransportStation.query.filter_by(
                        external_id=stop_id
                    ).first()
                    
                    if existing:
                        skipped += 1
                        continue
                    
                    # Create new station
                    station = TransportStation(
                        name=stop_name,
                        station_type='bus',
                        external_id=stop_id,  # Store GTFS stop_id as external_id
                        latitude=float(stop_lat),
                        longitude=float(stop_lon)
                    )
                    
                    db.session.add(station)
                    imported += 1
                    
                    if imported % 100 == 0:
                        print(f"  Imported {imported} bus stops...")
                
                db.session.commit()
                
                print(f"\n{'='*70}")
                print("✓ Import complete!")
                print(f"{'='*70}")
                print(f"  Imported: {imported}")
                print(f"  Skipped:  {skipped}")
                print(f"\nTotal bus stops in database: {TransportStation.query.filter_by(station_type='bus').count()}")

def show_gtfs_info(zip_file):
    """Show information about GTFS files"""
    with zipfile.ZipFile(zip_file) as z:
        print("GTFS Files in archive:")
        print("="*70)
        for name in z.namelist():
            info = z.getinfo(name)
            size_kb = info.file_size / 1024
            print(f"  {name:30s} {size_kb:>10.1f} KB")

if __name__ == '__main__':
    try:
        # Download GTFS data
        gtfs_data = download_gtfs()
        
        # Show info
        show_gtfs_info(gtfs_data)
        gtfs_data.seek(0)  # Reset file pointer
        
        print("\n")
        
        # Import bus stops
        import_bus_stops(gtfs_data)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
