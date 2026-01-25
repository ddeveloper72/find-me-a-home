"""Quick script to update MyHome.ie properties with complete data from brochure API"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import app, db
from models import Property
from scripts.import_myhome_brochure import fetch_property_brochure, parse_brochure_to_property
from time import sleep

with app.app_context():
    # Get all MyHome.ie properties
    props = Property.query.filter_by(source='myhome.ie').all()
    print(f'Found {len(props)} MyHome.ie properties to update\n')
    
    updated = 0
    for prop in props:
        print(f'[{prop.id}] {prop.address}...', end=' ')
        
        # Fetch complete data from brochure API
        brochure_data = fetch_property_brochure(prop.external_id, delay=0.5)
        if not brochure_data:
            print('ERROR - Could not fetch')
            continue
        
        # Parse to property data
        prop_data = parse_brochure_to_property(brochure_data)
        if not prop_data:
            print('SKIP - No data')
            continue
        
        # Update fields
        changed = False
        if prop_data.get('latitude') and not prop.latitude:
            prop.latitude = prop_data['latitude']
            prop.longitude = prop_data['longitude']
            changed = True
        
        if prop_data.get('description') and not prop.description:
            prop.description = prop_data['description']
            changed = True
        
        if prop_data.get('bathrooms') and not prop.bathrooms:
            prop.bathrooms = prop_data['bathrooms']
            changed = True
        
        if prop_data.get('size_sqm') and prop.size_sqm == 0:
            prop.size_sqm = prop_data['size_sqm']
            changed = True
        
        if prop_data.get('eircode') and not prop.eircode:
            prop.eircode = prop_data['eircode']
            changed = True
        
        if changed:
            updated += 1
            coords = f"({prop.latitude:.4f}, {prop.longitude:.4f})" if prop.latitude else "(no coords)"
            print(f'UPDATED - {coords}')
        else:
            print('OK - No changes needed')
    
    # Commit changes
    db.session.commit()
    print(f'\n✓ Updated {updated} properties')
