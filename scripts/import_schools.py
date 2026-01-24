#!/usr/bin/env python
"""
School data import script
Downloads and imports school data from Department of Education Excel files (2025/2026)
"""

import sys
import os
import requests
import csv
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db
from models import School

try:
    import openpyxl
except ImportError:
    print("❌ openpyxl not installed. Run: pip install openpyxl")
    sys.exit(1)

# Department of Education Excel URLs (2025/2026)
PRIMARY_SCHOOLS_URL = "https://assets.gov.ie/static/documents/d85298b3/Data_on_Individual_Schools_Mainstream_preliminary_2025-2026.xlsx"
POST_PRIMARY_URL = "https://assets.gov.ie/static/documents/c409b1b1/Data_on_Individual_Schools_PPOD_preliminary_2025-2026.xlsx"

# Local storage directory
DATA_DIR = Path(__file__).parent.parent / 'data'
DATA_DIR.mkdir(exist_ok=True)

LOCAL_PRIMARY_FILE = DATA_DIR / 'primary_schools_2025_2026.xlsx'
LOCAL_POST_PRIMARY_FILE = DATA_DIR / 'post_primary_schools_2025_2026.xlsx'
LOCAL_PRIMARY_CSV = DATA_DIR / 'primary_schools_2025_2026.csv'
LOCAL_POST_PRIMARY_CSV = DATA_DIR / 'post_primary_schools_2025_2026.csv'


def download_excel(url, local_path):
    """
    Download Excel file from URL and save locally
    """
    print(f"Downloading: {url[:70]}...")
    print(f"Saving to: {local_path}")
    
    try:
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        
        # Save to local file
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Downloaded {len(response.content):,} bytes")
        return True
        
    except Exception as e:
        print(f"❌ Error downloading: {e}")
        return False


def excel_to_csv(excel_path, csv_path, sheet_name=0):
    """
    Convert Excel file to CSV for easier processing and version control
    """
    print(f"\nConverting {excel_path.name} to CSV...")
    
    try:
        workbook = openpyxl.load_workbook(excel_path, read_only=True, data_only=True)
        
        # List all sheets
        print(f"  Available sheets: {', '.join([s.title for s in workbook.worksheets])}")
        
        # Get the first sheet or specified sheet
        if isinstance(sheet_name, int):
            sheet = workbook.worksheets[sheet_name]
        else:
            sheet = workbook[sheet_name]
        
        print(f"  Using sheet: {sheet.title}")
        
        # Write to CSV
        row_count = 0
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            for row in sheet.iter_rows(values_only=True):
                # Filter out completely empty rows
                if any(cell is not None and str(cell).strip() for cell in row):
                    writer.writerow(row)
                    row_count += 1
        
        print(f"✅ Saved {row_count:,} rows to {csv_path.name}")
        return True
        
    except Exception as e:
        print(f"❌ Error converting to CSV: {e}")
        import traceback
        traceback.print_exc()
        return False


def import_schools_from_csv(csv_path, school_type, skip_rows=0):
    """
    Import schools from CSV file
    
    Args:
        csv_path: Path to CSV file
        school_type: 'primary' or 'post-primary'
        skip_rows: Number of rows to skip before header row (default: 0)
    """
    print(f"\nImporting {school_type} schools from {csv_path.name}...")
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            # Skip initial rows if needed
            for _ in range(skip_rows):
                next(f)
            
            csv_reader = csv.DictReader(f)
            
            # Print available columns for debugging
            if csv_reader.fieldnames:
                print(f"CSV Columns ({len(csv_reader.fieldnames)}): {', '.join(list(csv_reader.fieldnames)[:10])}...")
            
            new_count = 0
            updated_count = 0
            error_count = 0
            
            for row in csv_reader:
                try:
                    # Map CSV columns to our fields (flexible column name matching)
                    roll_number = (row.get('Roll Number') or 
                                  row.get('ROLL_NUMBER') or 
                                  row.get('RollNumber') or
                                  row.get('roll_number') or
                                  row.get('Roll No') or
                                  row.get('Roll No.'))
                    
                    school_name = (row.get('Official School Name') or 
                                  row.get('OFFICIAL_SCHOOL_NAME') or 
                                  row.get('School_Name') or
                                  row.get('school_name') or
                                  row.get('SchoolName') or
                                  row.get('School Name') or
                                  row.get('Official Name') or  # Primary schools use this
                                  row.get('Name'))
                    
                    # Address components - primary schools use different naming
                    address1 = (row.get('Address') or row.get('ADDRESS') or 
                               row.get('Address1') or row.get('Address 1') or
                               row.get('Address (Line 1)') or '')
                    address2 = (row.get('Address2') or row.get('ADDRESS2') or 
                               row.get('Address 2') or row.get('Address (Line 2)') or '')
                    address3 = (row.get('Address3') or row.get('ADDRESS3') or 
                               row.get('Address 3') or row.get('Address (Line 3)') or '')
                    address4 = row.get('Address 4') or row.get('Address (Line 4)') or ''
                    
                    # Combine address parts
                    address_parts = [p.strip() for p in [address1, address2, address3, address4] if p and p.strip()]
                    address = ', '.join(address_parts) if address_parts else None
                    
                    county = (row.get('County') or 
                             row.get('COUNTY') or 
                             row.get('county') or
                             row.get('Co') or
                             row.get('Co.') or
                             row.get('County Description'))
                    
                    eircode = (row.get('Eircode') or 
                              row.get('EIRCODE') or 
                              row.get('eircode') or
                              row.get('Postcode') or
                              row.get('Eircode/Postcode'))
                    
                    # Geolocation - try multiple column names
                    latitude_str = (row.get('Latitude') or 
                                   row.get('LATITUDE') or 
                                   row.get('latitude') or
                                   row.get('Y') or
                                   row.get('Lat') or
                                   row.get('lat'))
                    
                    longitude_str = (row.get('Longitude') or 
                                    row.get('LONGITUDE') or 
                                    row.get('longitude') or
                                    row.get('X') or
                                    row.get('Lon') or
                                    row.get('Long') or
                                    row.get('lon') or
                                    row.get('long'))
                    
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
                        school_type=school_type
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
                            school_type=school_type,
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
                print(f"\n✅ {school_type.title()} Schools Import Complete:")
                print(f"   New: {new_count}")
                print(f"   Updated: {updated_count}")
                print(f"   Errors: {error_count}")
                return new_count + updated_count
            except Exception as e:
                db.session.rollback()
                print(f"❌ Error committing to database: {e}")
                return 0
                
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        import traceback
        traceback.print_exc()
        return 0


def main():
    """
    Main import function
    """
    print("="*80)
    print("SCHOOLS DATA IMPORT - 2025/2026")
    print("="*80)
    
    with app.app_context():
        # Download Primary Schools Excel
        if not LOCAL_PRIMARY_FILE.exists():
            print("\n📥 PRIMARY SCHOOLS")
            if download_excel(PRIMARY_SCHOOLS_URL, LOCAL_PRIMARY_FILE):
                excel_to_csv(LOCAL_PRIMARY_FILE, LOCAL_PRIMARY_CSV, sheet_name='Mainstream')
        else:
            print(f"\n✓ Primary schools Excel already downloaded: {LOCAL_PRIMARY_FILE.name}")
            if not LOCAL_PRIMARY_CSV.exists():
                excel_to_csv(LOCAL_PRIMARY_FILE, LOCAL_PRIMARY_CSV, sheet_name='Mainstream')
        
        # Download Post-Primary Schools Excel
        if not LOCAL_POST_PRIMARY_FILE.exists():
            print("\n📥 POST-PRIMARY SCHOOLS")
            if download_excel(POST_PRIMARY_URL, LOCAL_POST_PRIMARY_FILE):
                excel_to_csv(LOCAL_POST_PRIMARY_FILE, LOCAL_POST_PRIMARY_CSV, sheet_name='Post-Primary')
        else:
            print(f"\n✓ Post-primary schools Excel already downloaded: {LOCAL_POST_PRIMARY_FILE.name}")
            if not LOCAL_POST_PRIMARY_CSV.exists():
                excel_to_csv(LOCAL_POST_PRIMARY_FILE, LOCAL_POST_PRIMARY_CSV, sheet_name='Post-Primary')
        
        # Import Primary Schools
        if LOCAL_PRIMARY_CSV.exists():
            import_schools_from_csv(LOCAL_PRIMARY_CSV, 'primary', skip_rows=1)
        else:
            print("⚠️  Primary schools CSV not found")
        
        # Import Post-Primary Schools
        if LOCAL_POST_PRIMARY_CSV.exists():
            import_schools_from_csv(LOCAL_POST_PRIMARY_CSV, 'post-primary')
        else:
            print("⚠️  Post-primary schools CSV not found")
        
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
        
        print(f"Total Schools: {total_schools:,}")
        print(f"  Post-Primary: {post_primary:,}")
        print(f"  Primary: {primary:,}")
        print(f"  With Coordinates: {with_coords:,}")
        
        if total_schools > 0:
            print(f"  Geolocation Coverage: {(with_coords/total_schools*100):.1f}%")
        
        print("\n" + "="*80)
        print("LOCAL DATA FILES")
        print("="*80)
        print(f"Excel files stored in: {DATA_DIR}")
        print(f"  {LOCAL_PRIMARY_FILE.name}: {'✓' if LOCAL_PRIMARY_FILE.exists() else '✗'}")
        print(f"  {LOCAL_POST_PRIMARY_FILE.name}: {'✓' if LOCAL_POST_PRIMARY_FILE.exists() else '✗'}")
        print(f"CSV files:")
        print(f"  {LOCAL_PRIMARY_CSV.name}: {'✓' if LOCAL_PRIMARY_CSV.exists() else '✗'}")
        print(f"  {LOCAL_POST_PRIMARY_CSV.name}: {'✓' if LOCAL_POST_PRIMARY_CSV.exists() else '✗'}")
        print("="*80)
        
        return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
