#!/usr/bin/env python
"""
Geocode schools using Nominatim (OpenStreetMap) with Eircode
Adds latitude/longitude coordinates to schools using their addresses and Eircodes
"""

import sys
import os
import time
from datetime import datetime

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

# Rate limiting: Nominatim policy requires 1 request per second
# See: https://operations.osmfoundation.org/policies/nominatim/
REQUESTS_PER_SECOND = 1
DELAY_BETWEEN_REQUESTS = 1.0 / REQUESTS_PER_SECOND
BATCH_COMMIT_SIZE = 10  # Commit every N successful geocodes

# Initialize geocoder
geocoder = Nominatim(user_agent="FindMeAHome/1.0 (Educational Project - Ireland)")


def geocode_school(school):
    """
    Geocode a school using its address, Eircode, and county
    
    Args:
        school: School object with address, eircode, county
        
    Returns:
        tuple: (latitude, longitude) or (None, None) if not found
    """
    # Strategy 1: Try full address + Eircode (most specific)
    if school.address and school.eircode:
        query = f"{school.address}, {school.eircode}, Ireland"
        
        try:
            location = geocoder.geocode(query, exactly_one=True, timeout=10, country_codes='ie')
            if location:
                return location.latitude, location.longitude
        except (GeocoderTimedOut, GeocoderServiceError):
            pass
    
    # Strategy 2: Try address + county (no Eircode, as Nominatim doesn't geocode Eircodes well)
    if school.address and school.county:
        query = f"{school.address}, {school.county}, Ireland"
        
        try:
            location = geocoder.geocode(query, exactly_one=True, timeout=10, country_codes='ie')
            if location:
                return location.latitude, location.longitude
        except (GeocoderTimedOut, GeocoderServiceError):
            pass
    
    # Strategy 3: Try school name + county (for well-known schools)
    if school.name and school.county:
        query = f"{school.name}, {school.county}, Ireland"
        
        try:
            location = geocoder.geocode(query, exactly_one=True, timeout=10, country_codes='ie')
            if location:
                return location.latitude, location.longitude
        except (GeocoderTimedOut, GeocoderServiceError):
            pass
    
    return None, None


def geocode_schools(max_schools=None):
    """
    Geocode all schools that don't have coordinates yet
    
    Args:
        max_schools: Maximum number of schools to geocode (for testing)
    """
    print("="*80)
    print("SCHOOL GEOCODING - Nominatim (OpenStreetMap)")
    print("="*80)
    print(f"Rate limit: {REQUESTS_PER_SECOND} request/second (Nominatim policy)")
    print(f"Batch commits: every {BATCH_COMMIT_SIZE} successful geocodes")
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
        start_time = datetime.now()
        
        print("Starting geocoding...")
        print(f"Started at: {start_time.strftime('%H:%M:%S')}")
        print("-"*80)
        
        for i, school in enumerate(schools_to_geocode, 1):
            # Display school info
            eircode_display = school.eircode if school.eircode else 'No Eircode'
            print(f"[{i}/{len(schools_to_geocode)}] {school.name[:40]:<40} | {eircode_display:<10}", end=' ')
            
            # Geocode
            lat, lon = geocode_school(school)
            
            if lat and lon:
                school.latitude = lat
                school.longitude = lon
                success_count += 1
                print(f" ✅ {lat:.6f}, {lon:.6f}")
                
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
    
    args = parser.parse_args()
    
    success, fail = geocode_schools(max_schools=args.test)
    
    return 0 if success > 0 else 1


if __name__ == '__main__':
    sys.exit(main())
