"""
Geocode properties using their Eircode (Irish postal code)

This script uses Google Maps Geocoding API to convert Eircodes to coordinates.
Google has excellent Eircode support for Ireland.
"""

import sys
import os
from pathlib import Path
from time import sleep
import requests
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv(project_root / '.env')

from app import app, db
from models import Property

# Google Maps API key
GOOGLE_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')


def geocode_with_google(eircode):
    """
    Geocode Irish Eircode using Google Maps Geocoding API
    Google has excellent Eircode support for Ireland.
    
    Returns: (latitude, longitude) or (None, None) if not found
    """
    if not eircode or not GOOGLE_API_KEY:
        return None, None
    
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'address': eircode,
        'region': 'ie',  # Bias to Ireland
        'key': GOOGLE_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'OK' and data['results']:
            location = data['results'][0]['geometry']['location']
            lat = location['lat']
            lon = location['lng']
            return lat, lon
        elif data['status'] == 'ZERO_RESULTS':
            return None, None
        else:
            print(f"    Google API error: {data.get('status', 'Unknown')}")
            return None, None
            
    except Exception as e:
        print(f"    Error: {e}")
        return None, None


def geocode_with_nominatim(address, eircode):
    """
    Fallback geocoding using Nominatim (OpenStreetMap)
    
    Returns: (latitude, longitude) or (None, None) if not found
    """
    # Build search query
    query = f"{address}, Ireland" if address else f"{eircode}, Ireland"
    
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': query,
        'format': 'json',
        'limit': 1
    }
    headers = {
        'User-Agent': 'FindMeAHome/1.0 (Irish Property Search App)'
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        results = response.json()
        
        if results and len(results) > 0:
            lat = float(results[0]['lat'])
            lon = float(results[0]['lon'])
            return lat, lon
            
    except Exception as e:
        print(f"    Error: {e}")
    
    return None, None


def geocode_properties():
    """Geocode all properties that have Eircode or address but no coordinates"""
    
    if not GOOGLE_API_KEY:
        print("⚠️  No Google Maps API key found in .env")
        print("   Add GOOGLE_MAPS_API_KEY to .env file for best Eircode support")
        print("   Falling back to Nominatim (OpenStreetMap)\n")
    
    with app.app_context():
        # Find properties with no coordinates
        properties = Property.query.filter(
            Property.latitude.is_(None)
        ).all()
        
        if not properties:
            print("No properties found that need geocoding")
            return
        
        print(f"Found {len(properties)} properties with no coordinates\n")
        
        geocoded = 0
        failed = 0
        
        for i, prop in enumerate(properties, 1):
            eircode_display = f" ({prop.eircode})" if prop.eircode else ""
            print(f"[{i}/{len(properties)}] {prop.address}{eircode_display}...", end=' ')
            
            lat, lon = None, None
            
            # Try Google first if we have API key and Eircode
            if GOOGLE_API_KEY and prop.eircode:
                lat, lon = geocode_with_google(prop.eircode)
            
            # Fallback to Nominatim if Google didn't work
            if not lat:
                lat, lon = geocode_with_nominatim(prop.address, prop.eircode)
            
            if lat and lon:
                prop.latitude = lat
                prop.longitude = lon
                geocoded += 1
                print(f"✓ ({lat:.6f}, {lon:.6f})")
            else:
                failed += 1
                print("✗ Not found")
            
            # Be respectful with API requests
            if i < len(properties):
                sleep(0.5 if GOOGLE_API_KEY else 1.0)
        
        # Commit changes
        db.session.commit()
        
        print(f"\n{'='*70}")
        print("✓ Geocoding complete!")
        print(f"{'='*70}")
        print(f"  Geocoded: {geocoded}")
        print(f"  Failed:   {failed}")
        
        if GOOGLE_API_KEY:
            print(f"\nUsing Google Maps Geocoding API (excellent Eircode support)")
        else:
            print(f"\nUsing Nominatim (OpenStreetMap) - add Google API key for better results")


if __name__ == '__main__':
    geocode_properties()
