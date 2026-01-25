"""Reverse geocode train stations to get addresses from coordinates"""
import sys
from pathlib import Path
from time import sleep
import requests

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import app, db
from models import TransportStation


def reverse_geocode(latitude, longitude):
    """
    Reverse geocode coordinates to get address using Nominatim (FREE)
    
    Returns: formatted address string or None
    """
    if not latitude or not longitude:
        return None
    
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        'lat': latitude,
        'lon': longitude,
        'format': 'json',
        'addressdetails': 1
    }
    headers = {
        'User-Agent': 'FindMeAHome/1.0 (Irish Property Search App)'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Get formatted address
        display_name = data.get('display_name')
        
        # Or build custom address from components
        address_parts = data.get('address', {})
        road = address_parts.get('road', '')
        suburb = address_parts.get('suburb', '')
        town = address_parts.get('town', '') or address_parts.get('city', '')
        county = address_parts.get('county', '')
        
        # Build cleaner address
        parts = [p for p in [road, suburb, town, county] if p]
        if parts:
            return ', '.join(parts)
        
        return display_name
        
    except Exception as e:
        print(f"    Error: {e}")
        return None


def update_station_addresses():
    """Add addresses to all train stations using reverse geocoding"""
    
    with app.app_context():
        # Find stations with coordinates but no address
        stations = TransportStation.query.filter(
            TransportStation.latitude.isnot(None),
            TransportStation.address.is_(None)
        ).all()
        
        if not stations:
            print("✓ All train stations already have addresses")
            return
        
        print(f"Found {len(stations)} train stations without addresses\n")
        print("Using Nominatim Reverse Geocoding - FREE service")
        print("="*70 + "\n")
        
        updated = 0
        failed = 0
        
        for i, station in enumerate(stations, 1):
            print(f"[{i}/{len(stations)}] {station.name}...", end=' ')
            
            address = reverse_geocode(station.latitude, station.longitude)
            
            if address:
                station.address = address
                updated += 1
                print(f"✓")
                print(f"    {address}")
            else:
                failed += 1
                print("✗ Failed")
            
            # Be respectful - 1 second delay between requests
            if i < len(stations):
                sleep(1)
        
        # Commit changes
        db.session.commit()
        
        print(f"\n{'='*70}")
        print("✓ Reverse geocoding complete!")
        print(f"{'='*70}")
        print(f"  Updated: {updated}")
        print(f"  Failed:  {failed}")
        print(f"\n💰 Cost: €0.00 (Nominatim is free!)")


if __name__ == '__main__':
    update_station_addresses()
