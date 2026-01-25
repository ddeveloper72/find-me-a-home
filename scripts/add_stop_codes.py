"""
Add stop_code field to bus stops from GTFS data.
The stop_code is the public-facing stop number (e.g., 11090, 102631).
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import TransportStation
import requests
import zipfile
import io
import csv

GTFS_URL = "https://www.transportforireland.ie/transitData/Data/GTFS_All.zip"

def main():
    with app.app_context():
        # Download GTFS data
        print("Downloading GTFS data...")
        response = requests.get(GTFS_URL)
        response.raise_for_status()
        print(f"Downloaded {len(response.content) / (1024*1024):.1f} MB")
        
        zip_file = zipfile.ZipFile(io.BytesIO(response.content))
        
        # Parse stops.txt to get stop_code mapping
        print("\nParsing stops.txt...")
        stop_codes = {}  # external_id (stop_id) -> stop_code
        
        with zip_file.open('stops.txt') as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig'))
            for row in reader:
                stop_id = row['stop_id']
                stop_code = row.get('stop_code', '')
                if stop_code:
                    stop_codes[stop_id] = stop_code
        
        print(f"Found {len(stop_codes):,} stops with stop codes")
        
        # Update bus stops
        print("\nUpdating bus stops with stop codes...")
        bus_stops = TransportStation.query.filter_by(station_type='bus').all()
        
        updated = 0
        no_code = 0
        
        for stop in bus_stops:
            if stop.external_id and stop.external_id in stop_codes:
                stop.station_code = stop_codes[stop.external_id]
                updated += 1
                
                if updated % 1000 == 0:
                    print(f"  Updated {updated:,} stops...")
                    db.session.commit()
            else:
                no_code += 1
        
        db.session.commit()
        
        print()
        print("=== Completed ===")
        print(f"Total bus stops: {len(bus_stops):,}")
        print(f"Updated with stop codes: {updated:,}")
        print(f"No stop code found: {no_code:,}")
        print()
        print("Stop codes saved to 'station_code' field")
        print("Example: Stop code '11090' for passenger-facing stop number")

if __name__ == '__main__':
    main()
