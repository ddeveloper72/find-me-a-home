#!/usr/bin/env python
"""
School data import script
Downloads and imports school data from Department of Education CSV
"""

import sys
import os
import requests
import csv
from io import StringIO

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db
from models import School

# Department of Education CSV URLs
POST_PRIMARY_URL = "https://www.education.ie/en/Publications/Statistics/Data-on-Individual-Schools/Education-UT-post_primaryEducation-IE-DepartmentofEducationAndSkills-Post-PrimarySchoolsLocations2016-2017_080617.csv"

# Note: Primary schools URL - you may need to find the current link at:
# https://www.education.ie/en/find-a-school
# or https://data.gov.ie/organization/department-of-education

def download_csv(url):
    """
    Download CSV file from URL
    """
    print(f"Downloading from: {url}")
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        response.encoding = 'utf-8'  # Ensure proper encoding
        return response.text
    except Exception as e:
        print(f"❌ Error downloading CSV: {e}")
        return None

def import_post_primary_schools(csv_text):
    """
    Import post-primary schools from CSV
    
    Expected columns (may vary):
    - Roll Number
    - Official School Name
    - Address
    - County
    - Eircode
    - Latitude
    - Longitude
    - etc.
    """
    print("\nImporting post-primary schools...")
    
    csv_reader = csv.DictReader(StringIO(csv_text))
    
    # Print available columns for debugging
    if hasattr(csv_reader, 'fieldnames') and csv_reader.fieldnames:
        print(f"CSV Columns: {csv_reader.fieldnames}")
    
    new_count = 0
    updated_count = 0
    error_count = 0
    
    for row in csv_reader:
        try:
            # Map CSV columns to our fields (adjust based on actual CSV structure)
            # Common column names to try
            roll_number = (row.get('Roll Number') or 
                          row.get('ROLL_NUMBER') or 
                          row.get('RollNumber') or
                          row.get('roll_number'))
            
            school_name = (row.get('Official School Name') or 
                          row.get('OFFICIAL_SCHOOL_NAME') or 
                          row.get('School_Name') or
                          row.get('school_name') or
                          row.get('SchoolName'))
            
            # Address components
            address1 = row.get('Address') or row.get('ADDRESS') or ''
            address2 = row.get('Address2') or row.get('ADDRESS2') or ''
            address3 = row.get('Address3') or row.get('ADDRESS3') or ''
            
            # Combine address parts
            address_parts = [p.strip() for p in [address1, address2, address3] if p and p.strip()]
            address = ', '.join(address_parts) if address_parts else None
            
            county = (row.get('County') or 
                     row.get('COUNTY') or 
                     row.get('county'))
            
            eircode = (row.get('Eircode') or 
                      row.get('EIRCODE') or 
                      row.get('eircode') or
                      row.get('Postcode'))
            
            # Geolocation
            latitude_str = (row.get('Latitude') or 
                           row.get('LATITUDE') or 
                           row.get('latitude') or
                           row.get('Y') or
                           row.get('Lat'))
            
            longitude_str = (row.get('Longitude') or 
                            row.get('LONGITUDE') or 
                            row.get('longitude') or
                            row.get('X') or
                            row.get('Lon') or
                            row.get('Long'))
            
            # Convert coordinates to float
            try:
                latitude = float(latitude_str) if latitude_str else None
                longitude = float(longitude_str) if longitude_str else None
            except (ValueError, TypeError):
                latitude = None
                longitude = None
            
            # Skip if missing essential data
            if not roll_number or not school_name:
                error_count += 1
                continue
            
            # Check if school already exists
            existing = School.query.filter_by(
                roll_number=roll_number,
                school_type='post-primary'
            ).first()
            
            if existing:
                # Update existing school
                existing.name = school_name
                existing.address = address
                existing.county = county
                existing.eircode = eircode
                existing.latitude = latitude
                existing.longitude = longitude
                updated_count += 1
            else:
                # Create new school
                school = School(
                    roll_number=roll_number,
                    name=school_name,
                    address=address,
                    county=county,
                    eircode=eircode,
                    school_type='post-primary',
                    latitude=latitude,
                    longitude=longitude
                )
                db.session.add(school)
                new_count += 1
            
            # Commit in batches of 100
            if (new_count + updated_count) % 100 == 0:
                db.session.commit()
                print(f"  Progress: {new_count} new, {updated_count} updated...")
        
        except Exception as e:
            print(f"  ⚠️  Error processing row: {e}")
            error_count += 1
            continue
    
    # Final commit
    try:
        db.session.commit()
        print(f"\n✅ Post-Primary Schools Import Complete:")
        print(f"   New: {new_count}")
        print(f"   Updated: {updated_count}")
        print(f"   Errors: {error_count}")
        return new_count + updated_count
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error committing to database: {e}")
        return 0

def main():
    """
    Main import function
    """
    print("="*80)
    print("SCHOOLS DATA IMPORT")
    print("="*80)
    
    with app.app_context():
        # Import post-primary schools
        csv_text = download_csv(POST_PRIMARY_URL)
        
        if csv_text:
            import_post_primary_schools(csv_text)
        else:
            print("❌ Failed to download schools CSV")
            return False
        
        # Display summary
        print("\n" + "="*80)
        print("DATABASE SUMMARY")
        print("="*80)
        total_schools = School.query.count()
        post_primary = School.query.filter_by(school_type='post-primary').count()
        primary = School.query.filter_by(school_type='primary').count()
        with_coords = School.query.filter(
            School.latitude.isnot(None),
            School.longitude.isnot(None)
        ).count()
        
        print(f"Total Schools: {total_schools}")
        print(f"  Post-Primary: {post_primary}")
        print(f"  Primary: {primary}")
        print(f"  With Coordinates: {with_coords}")
        print("="*80)
        
        return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
