#!/usr/bin/env python
"""
Geocode schools using multiple providers with Eircode-first strategy.

Provider order (default):
1. GeoDirectory API (https://www.geoaddress-checked.ie/) using Eircode
2. Google Geocoding API using Eircode
3. Nominatim (OpenStreetMap) using address/county or school name/county
"""

import sys
import os
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db
from models import School

try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError
except ImportError:
    print("❌ geopy not installed. Run: pip install geopy")
    sys.exit(1)

# Load environment variables from project root
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / '.env')

GEODIRECTORY_TOKEN = os.getenv('GEOADDRESS_CHECKED_API_TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# Rate limiting: Nominatim policy requires 1 request per second
# See: https://operations.osmfoundation.org/policies/nominatim/
REQUESTS_PER_SECOND = 1
DELAY_BETWEEN_REQUESTS = 1.0 / REQUESTS_PER_SECOND
BATCH_COMMIT_SIZE = 10  # Commit every N successful geocodes

# Initialize geocoder
geocoder = Nominatim(user_agent="FindMeAHome/1.0 (Educational Project - Ireland)")


def _normalize_eircode(eircode):
    """Normalize eircode input for API calls."""
    if not eircode:
        return None
    return ''.join(str(eircode).strip().upper().split())


def _extract_lat_lon(payload):
    """Extract latitude/longitude from variable API response structures."""
    if not payload:
        return None, None

    # Common direct fields
    lat = payload.get('latitude') or payload.get('lat') or payload.get('y')
    lon = payload.get('longitude') or payload.get('lng') or payload.get('lon') or payload.get('x')

    if lat is not None and lon is not None:
        try:
            return float(lat), float(lon)
        except (TypeError, ValueError):
            pass

    # Optional nested location fields (varies by token permissions)
    location = payload.get('location')
    if isinstance(location, dict):
        lat = location.get('latitude') or location.get('lat')
        lon = location.get('longitude') or location.get('lng') or location.get('lon')
        if lat is not None and lon is not None:
            try:
                return float(lat), float(lon)
            except (TypeError, ValueError):
                pass

    if isinstance(location, (list, tuple)) and len(location) == 2:
        try:
            first = float(location[0])
            second = float(location[1])
            # Handle potential [lon, lat] ordering.
            if abs(first) <= 90 and abs(second) <= 180:
                return first, second
            return second, first
        except (TypeError, ValueError):
            pass

    return None, None


def _geodirectory_post(endpoint, payload):
    """Make authenticated POST request to GeoDirectory API."""
    if not GEODIRECTORY_TOKEN:
        return None

    url = f"https://www.geoaddress-checked.ie/api/v3/{endpoint}"
    headers = {
        'Authorization': f'Bearer {GEODIRECTORY_TOKEN}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()
        # 401/429/other errors are handled by returning None and letting fallback run.
        return None
    except requests.RequestException:
        return None


def geocode_with_geodirectory(eircode):
    """
    Geocode using GeoDirectory API search-eircode endpoint.

    Returns:
        tuple: (lat, lon) or (None, None)
    """
    normalized = _normalize_eircode(eircode)
    if not normalized:
        return None, None

    # 1) Lookup by eircode
    data = _geodirectory_post('search-eircode', {'q': normalized})
    if not data:
        return None, None

    results = data.get('results')
    if isinstance(results, list):
        result = results[0] if results else None
    elif isinstance(results, dict):
        result = results
    else:
        result = None

    if not result:
        return None, None

    lat, lon = _extract_lat_lon(result)
    if lat is not None and lon is not None:
        return lat, lon

    # 2) Fallback to identification detail lookup for coordinates
    identification = result.get('identification')
    if not identification:
        return None, None

    detail_data = _geodirectory_post('search-identification', {'identification': str(identification)})
    if not detail_data:
        return None, None

    detail_results = detail_data.get('results')
    detail = detail_results[0] if isinstance(detail_results, list) and detail_results else detail_results
    if isinstance(detail, dict):
        return _extract_lat_lon(detail)

    return None, None


def geocode_with_google(eircode):
    """Geocode Irish eircode using Google Maps Geocoding API."""
    if not eircode or not GOOGLE_API_KEY:
        return None, None

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        'address': eircode,
        'region': 'ie',
        'key': GOOGLE_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data.get('status') == 'OK' and data.get('results'):
            location = data['results'][0]['geometry']['location']
            return location['lat'], location['lng']
    except requests.RequestException:
        return None, None

    return None, None


def geocode_school(school, provider_mode='auto'):
    """
    Geocode a school using its address, Eircode, and county
    
    Args:
        school: School object with address, eircode, county
        
    Returns:
        tuple: (latitude, longitude) or (None, None) if not found
    """
    # Strategy 1: GeoDirectory by eircode (if enabled)
    if provider_mode in ('auto', 'geodirectory'):
        if school.eircode and GEODIRECTORY_TOKEN:
            lat, lon = geocode_with_geodirectory(school.eircode)
            if lat and lon:
                return lat, lon, 'geodirectory'
        if provider_mode == 'geodirectory':
            return None, None, None

    # Strategy 2: Google by eircode (if enabled)
    if provider_mode in ('auto', 'google'):
        if school.eircode and GOOGLE_API_KEY:
            lat, lon = geocode_with_google(school.eircode)
            if lat and lon:
                return lat, lon, 'google'
        if provider_mode == 'google':
            return None, None, None

    # Strategy 3: Try full address + Eircode via Nominatim
    if school.address and school.eircode:
        query = f"{school.address}, {school.eircode}, Ireland"
        
        try:
            location = geocoder.geocode(query, exactly_one=True, timeout=10, country_codes='ie')
            if location:
                return location.latitude, location.longitude, 'nominatim'
        except (GeocoderTimedOut, GeocoderServiceError):
            pass
    
    # Strategy 4: Try address + county
    if school.address and school.county:
        query = f"{school.address}, {school.county}, Ireland"
        
        try:
            location = geocoder.geocode(query, exactly_one=True, timeout=10, country_codes='ie')
            if location:
                return location.latitude, location.longitude, 'nominatim'
        except (GeocoderTimedOut, GeocoderServiceError):
            pass
    
    # Strategy 5: Try school name + county
    if school.name and school.county:
        query = f"{school.name}, {school.county}, Ireland"
        
        try:
            location = geocoder.geocode(query, exactly_one=True, timeout=10, country_codes='ie')
            if location:
                return location.latitude, location.longitude, 'nominatim'
        except (GeocoderTimedOut, GeocoderServiceError):
            pass
    
            return None, None, None


def geocode_schools(max_schools=None, provider_mode='auto'):
    """
    Geocode all schools that don't have coordinates yet
    
    Args:
        max_schools: Maximum number of schools to geocode (for testing)
    """
    print("="*80)
    print("SCHOOL GEOCODING - Multi-provider")
    print("="*80)
    if provider_mode == 'auto':
        print("Provider mode: auto (GeoDirectory -> Google -> Nominatim)")
    else:
        print(f"Provider mode: {provider_mode}")
    print(f"Rate limit: {REQUESTS_PER_SECOND} request/second (Nominatim policy)")
    print(f"Batch commits: every {BATCH_COMMIT_SIZE} successful geocodes")
    print(f"GeoDirectory token configured: {'yes' if GEODIRECTORY_TOKEN else 'no'}")
    print(f"Google API key configured: {'yes' if GOOGLE_API_KEY else 'no'}")
    print()
    
    with app.app_context():
        # Find schools without coordinates
        schools_to_geocode = School.query.filter(
            School.latitude.is_(None)
        ).all()
        
        print(f"Schools needing geocoding: {len(schools_to_geocode):,}")
        
        # Check how many have Eircodes
        with_eircode = sum(1 for s in schools_to_geocode if s.eircode)
        print(f"  With Eircode: {with_eircode:,}")
        print(f"  Without Eircode: {len(schools_to_geocode) - with_eircode:,}")
        print()
        
        if max_schools:
            schools_to_geocode = schools_to_geocode[:max_schools]
            print(f"⚠️  Limited to {max_schools} schools for testing")
            print()
        
        # Geocode schools
        success_count = 0
        fail_count = 0
        by_provider = {'geodirectory': 0, 'google': 0, 'nominatim': 0}
        start_time = datetime.now()
        
        print("Starting geocoding...")
        print(f"Started at: {start_time.strftime('%H:%M:%S')}")
        print("-"*80)
        
        for i, school in enumerate(schools_to_geocode, 1):
            # Display school info
            eircode_display = school.eircode if school.eircode else 'No Eircode'
            print(f"[{i}/{len(schools_to_geocode)}] {school.name[:40]:<40} | {eircode_display:<10}", end=' ')
            
            # Geocode
            lat, lon, provider = geocode_school(school, provider_mode=provider_mode)
            
            if lat and lon:
                school.latitude = lat
                school.longitude = lon
                success_count += 1
                if provider in by_provider:
                    by_provider[provider] += 1
                print(f" ✅ {lat:.6f}, {lon:.6f} [{provider}]")
                
                # Commit in batches
                if success_count % BATCH_COMMIT_SIZE == 0:
                    db.session.commit()
                    elapsed = (datetime.now() - start_time).total_seconds()
                    rate = success_count / elapsed if elapsed > 0 else 0
                    remaining = len(schools_to_geocode) - i
                    eta_seconds = remaining / rate if rate > 0 else 0
                    print(f"  💾 Batch commit ({success_count} total, {rate:.2f}/sec, ETA: {eta_seconds/60:.0f}min)")
            else:
                fail_count += 1
                print(" ❌")
            
            # Rate limiting - sleep between requests
            if i < len(schools_to_geocode):
                time.sleep(DELAY_BETWEEN_REQUESTS)
        
        # Final commit
        db.session.commit()
        
        # Summary
        print("-"*80)
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        
        print()
        print("="*80)
        print("GEOCODING SUMMARY")
        print("="*80)
        print(f"Total processed: {len(schools_to_geocode):,}")
        print(f"  ✅ Success: {success_count:,}")
        print(f"  ❌ Failed: {fail_count:,}")
        print(f"  Success rate: {(success_count/len(schools_to_geocode)*100):.1f}%" if schools_to_geocode else "N/A")
        print(f"  Source breakdown: GeoDirectory={by_provider['geodirectory']}, Google={by_provider['google']}, Nominatim={by_provider['nominatim']}")
        print()
        print(f"Time elapsed: {elapsed:.0f} seconds ({elapsed/60:.1f} minutes)")
        print(f"Average rate: {(success_count/elapsed):.2f} geocodes/second" if elapsed > 0 else "N/A")
        print()
        
        # Database summary
        total_schools = School.query.count()
        with_coords = School.query.filter(
            School.latitude.isnot(None),
            School.longitude.isnot(None)
        ).count()
        
        print("DATABASE STATUS")
        print("-"*80)
        print(f"Total schools: {total_schools:,}")
        print(f"With coordinates: {with_coords:,}")
        print(f"Coverage: {(with_coords/total_schools*100):.1f}%")
        print("="*80)
        
        return success_count, fail_count


def main():
    """
    Main function with command-line options
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Geocode schools using Nominatim with Eircode')
    parser.add_argument('--test', type=int, metavar='N', 
                       help='Test mode: only geocode N schools')
    parser.add_argument(
        '--provider',
        choices=['auto', 'geodirectory', 'google', 'nominatim'],
        default='auto',
        help='Geocoding provider mode (default: auto)'
    )
    
    args = parser.parse_args()
    
    success, fail = geocode_schools(max_schools=args.test, provider_mode=args.provider)
    
    return 0 if success > 0 else 1


if __name__ == '__main__':
    sys.exit(main())
