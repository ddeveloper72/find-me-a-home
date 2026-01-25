"""Geocode train stations using their names with Nominatim (free)"""
import sys
from pathlib import Path
from time import sleep
import requests

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import app, db
from models import TransportStation


def geocode_station(name):
    """
    Geocode a train station by name using Nominatim (OpenStreetMap)
    Free and doesn't require API key!
    
    Returns: (latitude, longitude) or (None, None) if not found
    """
    if not name:
        return None, None
    
    # Build query - search for train station in Ireland
    queries = [
        f"{name} railway station, Ireland",
        f"{name} train station, Ireland",
        f"{name} station, Ireland"
    ]
    
    url = "https://nominatim.openstreetmap.org/search"
    headers = {
        'User-Agent': 'FindMeAHome/1.0 (Irish Property Search App)'
    }
    
    for query in queries:
        try:
            params = {
                'q': query,
                'format': 'json',
                'countrycodes': 'ie',
                'limit': 1
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            results = response.json()
            
            if results and len(results) > 0:
                lat = float(results[0]['lat'])
                lon = float(results[0]['lon'])
                return lat, lon
            
            # Small delay between attempts
            sleep(0.5)
            
        except Exception as e:
            print(f"    Error with query '{query}': {e}")
            continue
    
    return None, None


def geocode_all_stations():
    """Geocode all train stations that don't have coordinates"""
    
    with app.app_context():
        # Find stations without coordinates
        stations = TransportStation.query.filter(
            TransportStation.latitude.is_(None)
        ).all()
        
        if not stations:
            print("✓ All train stations already have coordinates")
            return
        
        print(f"Found {len(stations)} train stations without coordinates\n")
        print("Using Nominatim (OpenStreetMap) - FREE geocoding service")
        print("="*70 + "\n")
        
        geocoded = 0
        failed = 0
        
        for i, station in enumerate(stations, 1):
            print(f"[{i}/{len(stations)}] {station.name}...", end=' ')
            
            lat, lon = geocode_station(station.name)
            
            if lat and lon:
                station.latitude = lat
                station.longitude = lon
                geocoded += 1
                print(f"✓ ({lat:.6f}, {lon:.6f})")
            else:
                failed += 1
                print("✗ Not found")
            
            # Be respectful - 1.5 second delay between requests
            if i < len(stations):
                sleep(1.5)
        
        # Commit changes
        db.session.commit()
        
        print(f"\n{'='*70}")
        print("✓ Geocoding complete!")
        print(f"{'='*70}")
        print(f"  Geocoded: {geocoded}")
        print(f"  Failed:   {failed}")
        print(f"\n💰 Cost: €0.00 (Nominatim is free!)")


if __name__ == '__main__':
    geocode_all_stations()
