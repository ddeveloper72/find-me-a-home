"""
Reverse geocode bus stops to get addresses and extract counties.
Uses Nominatim (free) with progress tracking and resume capability.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import TransportStation
import requests
import time
from datetime import datetime, timedelta
import re

def reverse_geocode(lat, lon):
    """Reverse geocode coordinates using Nominatim"""
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        'lat': lat,
        'lon': lon,
        'format': 'json',
        'addressdetails': 1
    }
    headers = {
        'User-Agent': 'FindMeAHome-PropertySearch/1.0'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'display_name' in data:
            return data['display_name']
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None

def extract_county(address):
    """Extract county from address string"""
    if not address:
        return None
    
    # Look for "County X" pattern
    county_match = re.search(r'County\s+([A-Za-z\s]+?)(?:,|$)', address)
    if county_match:
        return county_match.group(1).strip()
    
    # Look for common Irish counties
    irish_counties = [
        'Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford', 'Drogheda',
        'Kildare', 'Wicklow', 'Meath', 'Louth', 'Kerry', 'Clare', 'Tipperary',
        'Donegal', 'Mayo', 'Sligo', 'Wexford', 'Kilkenny', 'Carlow', 'Laois',
        'Offaly', 'Westmeath', 'Longford', 'Roscommon', 'Leitrim', 'Cavan',
        'Monaghan'
    ]
    
    for county in irish_counties:
        if county in address:
            return county
    
    return None

def format_time(seconds):
    """Format seconds into readable time"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds/60)}m {int(seconds%60)}s"
    else:
        hours = int(seconds/3600)
        minutes = int((seconds % 3600)/60)
        return f"{hours}h {minutes}m"

def main():
    with app.app_context():
        # Get all bus stops without addresses
        bus_stops = TransportStation.query.filter(
            TransportStation.station_type == 'bus',
            TransportStation.address.is_(None)
        ).all()
        
        total = len(bus_stops)
        
        if total == 0:
            print("All bus stops already have addresses!")
            return
        
        print(f"=== Bus Stop Reverse Geocoding ===")
        print(f"Total bus stops to process: {total:,}")
        print(f"Estimated time: {format_time(total * 1.1)}")  # 1 sec per request + buffer
        print(f"Data will be saved to: findmehome.db (TransportStation table)")
        print(f"Progress is saved after EACH stop - safe to interrupt anytime")
        print(f"\nNote: Route numbers already stored in 'external_id' field from GTFS")
        print(f"      (Actual route names would need separate GTFS routes.txt import)")
        print()
        
        start_time = datetime.now()
        processed = 0
        success_count = 0
        error_count = 0
        county_count = 0
        
        for stop in bus_stops:
            processed += 1
            
            # Progress indicator
            percent = (processed / total) * 100
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if processed > 1:
                avg_time_per_stop = elapsed / processed
                remaining = total - processed
                eta_seconds = remaining * avg_time_per_stop
                eta_str = format_time(eta_seconds)
            else:
                eta_str = "calculating..."
            
            print(f"[{processed:,}/{total:,}] ({percent:.1f}%) - {stop.name[:50]}", end='')
            
            # Reverse geocode
            address = reverse_geocode(stop.latitude, stop.longitude)
            
            if address:
                stop.address = address
                county = extract_county(address)
                
                if county:
                    stop.county = county
                    county_count += 1
                    print(f" ✓ ({county}) - ETA: {eta_str}")
                else:
                    print(f" ✓ (no county) - ETA: {eta_str}")
                
                success_count += 1
            else:
                print(f" ✗ Failed - ETA: {eta_str}")
                error_count += 1
            
            # Save progress after EACH stop (failsafe)
            try:
                db.session.commit()
            except Exception as e:
                print(f"  Database error: {e}")
                db.session.rollback()
            
            # Respectful delay (Nominatim requirement)
            time.sleep(1)
        
        # Final summary
        elapsed_total = (datetime.now() - start_time).total_seconds()
        print()
        print("=== Completed ===")
        print(f"Total processed: {processed:,}")
        print(f"Successful: {success_count:,}")
        print(f"With county data: {county_count:,}")
        print(f"Failed: {error_count:,}")
        print(f"Total time: {format_time(elapsed_total)}")
        print()
        print("Data saved to: findmehome.db")
        print("You can now filter bus stops by county!")

if __name__ == '__main__':
    main()
