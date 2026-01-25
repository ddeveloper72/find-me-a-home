"""Extract county information from train station addresses"""
import sys
import re
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import app, db
from models import TransportStation


def extract_county_from_address(address):
    """Extract county name from address string"""
    if not address:
        return None
    
    # Look for "County X" pattern
    match = re.search(r'County\s+([A-Za-z\s]+?)(?:,|$)', address)
    if match:
        return match.group(1).strip()
    
    # Look for "Co. X" pattern
    match = re.search(r'Co\.\s+([A-Za-z\s]+?)(?:,|$)', address)
    if match:
        return match.group(1).strip()
    
    return None


def update_station_counties():
    """Extract and update county from addresses"""
    
    with app.app_context():
        # Find stations with address but no county
        stations = TransportStation.query.filter(
            TransportStation.address.isnot(None),
            TransportStation.county.is_(None)
        ).all()
        
        if not stations:
            print("✓ All stations already have county data")
            return
        
        print(f"Found {len(stations)} stations to update\n")
        
        updated = 0
        
        for station in stations:
            county = extract_county_from_address(station.address)
            
            if county:
                station.county = county
                updated += 1
                print(f"✓ {station.name}: {county}")
            else:
                print(f"✗ {station.name}: Could not extract county from '{station.address}'")
        
        # Commit changes
        db.session.commit()
        
        print(f"\n{'='*70}")
        print("✓ County update complete!")
        print(f"{'='*70}")
        print(f"  Updated: {updated}")
        print(f"  Failed:  {len(stations) - updated}")


if __name__ == '__main__':
    update_station_counties()
