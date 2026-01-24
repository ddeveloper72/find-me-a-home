"""
Import properties from MyHome.ie API

This script fetches property listings from the MyHome.ie undocumented JSON API and imports them 
into the database. Note: This API is not officially documented but appears to be the internal 
API used by MyHome.ie's own website.

Usage:
    python scripts/import_myhome_properties.py [--max-results MAX]
"""

import os
import sys
import argparse
import re
from pathlib import Path
from datetime import datetime
import requests
from time import sleep

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import app, db
from models import Property

# MyHome.ie API Configuration
MYHOME_API_BASE = "https://api.myhome.ie"

# BER rating mapping
BER_RATING_MAP = {
    'A1': 'A1', 'A2': 'A2', 'A3': 'A3',
    'B1': 'B1', 'B2': 'B2', 'B3': 'B3',
    'C1': 'C1', 'C2': 'C2', 'C3': 'C3',
    'D1': 'D1', 'D2': 'D2',
    'E1': 'E1', 'E2': 'E2',
    'F': 'F', 'G': 'G',
    'EXEMPT': None
}


def extract_ber_rating(ber_path):
    """Extract BER rating from image path"""
    if not ber_path:
        return None
    
    # Extract filename from path like "https://.../energyRating/A1.png"
    match = re.search(r'/energyRating/([A-Z0-9]+)\.png', ber_path)
    if match:
        rating = match.group(1)
        return BER_RATING_MAP.get(rating)
    return None


def extract_bedrooms(beds_string):
    """Extract bedroom count from string like '4 beds' or '4'"""
    if not beds_string:
        return None
    
    # Extract number from string
    match = re.search(r'(\d+)', str(beds_string))
    if match:
        return int(match.group(1))
    return None


def extract_size_sqm(size_string):
    """Extract size in square meters from string"""
    if not size_string:
        return None
    
    try:
        # Remove commas and convert to float
        size = float(str(size_string).replace(',', ''))
        return size
    except (ValueError, AttributeError):
        return None


def extract_price(price_string):
    """Extract numeric price from string like '€425,000' or 'POA'"""
    if not price_string or price_string.upper() in ['POA', 'PRICE ON APPLICATION']:
        return 0  # Use 0 for POA properties
    
    # Remove €, commas, and extract first number (for ranges like "€360,000 to €470,000")
    match = re.search(r'€([\d,]+)', price_string)
    if match:
        price_str = match.group(1).replace(',', '')
        try:
            return float(price_str)
        except ValueError:
            return 0
    return 0


def parse_address(display_address):
    """Extract county and city from address string"""
    if not display_address:
        return None, None
    
    # Common Irish counties
    counties = [
        'Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford', 'Clare', 'Kerry',
        'Tipperary', 'Mayo', 'Donegal', 'Wicklow', 'Meath', 'Kildare', 'Wexford',
        'Kilkenny', 'Carlow', 'Laois', 'Offaly', 'Westmeath', 'Longford', 'Louth',
        'Monaghan', 'Cavan', 'Sligo', 'Leitrim', 'Roscommon'
    ]
    
    # Try to extract county
    county = None
    for c in counties:
        if c in display_address:
            county = c
            break
    
    # If county is in "Co. County" format
    if not county:
        match = re.search(r'Co\.\s*(\w+)', display_address, re.IGNORECASE)
        if match:
            county = match.group(1)
    
    # Extract city/town (usually the last part before county)
    parts = display_address.split(',')
    city = None
    if len(parts) >= 2:
        # Try second-to-last part as city
        city = parts[-2].strip() if county else parts[-1].strip()
        # Clean up common prefixes
        city = re.sub(r'^(Co\.|County)\s*', '', city, flags=re.IGNORECASE).strip()
    
    return county, city


def parse_property_from_json(prop_data):
    """Extract property data from JSON response"""
    
    # Extract basic info
    property_id = prop_data.get('PropertyId')
    if not property_id:
        return None
    
    display_address = prop_data.get('DisplayAddress', '')
    county, city = parse_address(display_address)
    
    # Build full URL
    brochure_url = prop_data.get('BrochureUrl', '')
    full_url = f"https://www.myhome.ie{brochure_url}" if brochure_url else None
    
    # Get image URL
    image_url = prop_data.get('SetImageForCache')
    image_urls = [image_url] if image_url and 'heart.png' not in image_url else []
    
    # Extract data
    property_data = {
        'external_id': str(property_id),
        'source': 'myhome.ie',
        'title': prop_data.get('PropertyType', 'Property'),
        'description': None,  # Not available in this endpoint
        'price': extract_price(prop_data.get('PriceAsString')),
        'address': display_address,
        'county': county,
        'city': city,
        'eircode': None,  # Not in this endpoint
        'latitude': None,  # Not in this endpoint
        'longitude': None,  # Not in this endpoint
        'bedrooms': extract_bedrooms(prop_data.get('BedsString')),
        'bathrooms': None,  # Not in this endpoint
        'property_type': prop_data.get('PropertyType', '').lower(),
        'size_sqm': extract_size_sqm(prop_data.get('SizeStringMeters')),
        'ber_rating': extract_ber_rating(prop_data.get('EnergyRatingMediaPath')),
        'image_urls': image_urls if image_urls else None,
        'url': full_url,
    }
    
    return property_data


def fetch_home_properties():
    """Fetch featured and recently added properties from MyHome.ie home endpoint"""
    
    print(f"Fetching properties from MyHome.ie API...")
    
    try:
        response = requests.get(f"{MYHOME_API_BASE}/home", timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract properties from different sections
        all_properties = []
        
        # Get featured properties
        home_data = data.get('Home', {})
        
        # Featured properties (for sale)
        featured_sale = home_data.get('ForSaleFeaturedProperties', [])
        all_properties.extend(featured_sale)
        
        # Featured properties (for rent) 
        featured_rent = home_data.get('ForRentFeaturedProperties', [])
        all_properties.extend(featured_rent)
        
        # Recently added properties (by property class)
        recently_added = home_data.get('RecentlyAddedProperties', {})
        for class_id, props in recently_added.items():
            if isinstance(props, list):
                all_properties.extend(props)
        
        print(f"Found {len(all_properties)} properties from home endpoint")
        
        # Parse each property
        properties = []
        for prop_json in all_properties:
            try:
                # Only import residential properties for sale (PropertyClassId=1)
                if prop_json.get('PropertyClassId') != 1:
                    continue
                    
                property_data = parse_property_from_json(prop_json)
                if property_data:
                    properties.append(property_data)
            except Exception as e:
                print(f"Error parsing property {prop_json.get('PropertyId')}: {e}")
                continue
        
        return properties
        
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return []
    except Exception as e:
        print(f"Error processing response: {e}")
        return []


def import_properties(properties, max_results=None):
    """Import properties into the database"""
    
    if not properties:
        print("No properties to import")
        return
    
    # Limit results if specified
    if max_results:
        properties = properties[:max_results]
    
    print(f"\nImporting {len(properties)} properties to database...")
    
    with app.app_context():
        added = 0
        updated = 0
        skipped = 0
        errors = 0
        
        for prop_data in properties:
            try:
                # Check if property already exists
                existing = Property.query.filter_by(
                    external_id=prop_data['external_id'],
                    source='myhome.ie'
                ).first()
                
                if existing:
                    # Check if price has changed
                    if existing.price != prop_data['price']:
                        # Update existing property
                        for key, value in prop_data.items():
                            setattr(existing, key, value)
                        existing.updated_at = datetime.utcnow()
                        updated += 1
                        print(f"  Updated: {prop_data['address']} (price changed: €{existing.price:,.0f} → €{prop_data['price']:,.0f})")
                    else:
                        skipped += 1
                else:
                    # Create new property
                    new_property = Property(**prop_data)
                    db.session.add(new_property)
                    added += 1
                    print(f"  Added: {prop_data['address']} - €{prop_data['price']:,.0f}")
                
            except Exception as e:
                print(f"Error importing property {prop_data.get('external_id')}: {e}")
                errors += 1
                continue
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n✓ Import complete!")
            print(f"  Added: {added}")
            print(f"  Updated: {updated}")
            print(f"  Skipped: {skipped}")
            print(f"  Errors: {errors}")
            print(f"\nNote: MyHome.ie API endpoint provides limited data (no coordinates, descriptions)")
            print(f"Consider geocoding addresses separately for map functionality")
        except Exception as e:
            db.session.rollback()
            print(f"\nERROR: Database commit failed: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Import properties from MyHome.ie API')
    parser.add_argument('--max-results', type=int, help='Maximum properties to import')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("MyHome.ie Property Importer")
    print("=" * 70)
    print("\nNOTE: This uses an undocumented API endpoint.")
    print("The API structure may change without notice.\n")
    
    # Fetch properties from API
    properties = fetch_home_properties()
    
    # Import to database
    if properties:
        import_properties(properties, max_results=args.max_results)
    else:
        print("\nNo properties fetched. API may have changed or be unavailable.")


if __name__ == '__main__':
    main()
