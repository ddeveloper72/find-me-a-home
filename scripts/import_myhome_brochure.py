"""
Import properties from MyHome.ie Brochure API

This script fetches property IDs from the MyHome.ie /home endpoint, then queries the
/brochure/{id} endpoint to get complete property details including coordinates, descriptions,
and all metadata.

The API key used is publicly exposed in browser requests (not a private credential).

Usage:
    python scripts/import_myhome_brochure.py [--max-results MAX] [--delay SECONDS]
"""

import os
import sys
import argparse
import re
from pathlib import Path
from datetime import datetime
import requests
from time import sleep
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import app, db
from models import Property

# MyHome.ie API Configuration
MYHOME_API_BASE = "https://api.myhome.ie"
# Get API key from environment, fallback to public key
MYHOME_API_KEY = os.getenv('MYHOME_API_KEY', '4284149e-13da-4f12-aed7-0d644a0b7adb')
# Optional session cookie for personalized data (favorites, user properties, etc.)
MYHOME_SESSION_COOKIE = os.getenv('MYHOME_SESSION_COOKIE')

# BER rating order (for validation)
BER_RATINGS = ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3', 'D1', 'D2', 'E1', 'E2', 'F', 'G']


def get_property_ids_from_home():
    """Fetch property IDs from the /home endpoint"""
    endpoint = f"{MYHOME_API_BASE}/home"
    
    print(f"Fetching property IDs from {endpoint}...")
    
    # Add session cookie if available (for personalized data)
    headers = {}
    cookies = {}
    if MYHOME_SESSION_COOKIE:
        cookies['session'] = MYHOME_SESSION_COOKIE
        print("Using session cookie for personalized data...")
    
    try:
        response = requests.get(endpoint, headers=headers, cookies=cookies, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Check if user is authenticated
        user_id = data.get('UserId')
        if user_id and user_id != 0:
            user_email = data.get('Email', 'unknown')
            print(f"✓ Authenticated as user {user_id} ({user_email})")
        
        # Extract properties from different sections
        home_data = data.get('Home', {})
        property_ids = set()
        
        # Collect from all property arrays
        property_arrays = [
            home_data.get('ForSaleFeaturedProperties', []),
            home_data.get('ForSaleTrendingProperties', []),
            home_data.get('TrendingProperties', []),
            home_data.get('FeaturedProperties', [])
        ]
        
        for prop_array in property_arrays:
            if prop_array and isinstance(prop_array, list):
                for prop in prop_array:
                    if isinstance(prop, dict):
                        prop_id = prop.get('PropertyId')
                        # Only residential for sale (PropertyClassId=1)
                        if prop_id and prop.get('PropertyClassId') == 1:
                            property_ids.add(prop_id)
        
        # RecentlyAddedProperties is a dict with class IDs as keys
        recently_added = home_data.get('RecentlyAddedProperties', {})
        if isinstance(recently_added, dict):
            # Class 1 is residential for sale
            class_1_props = recently_added.get('1', [])
            if isinstance(class_1_props, list):
                for prop in class_1_props:
                    if isinstance(prop, dict):
                        prop_id = prop.get('PropertyId')
                        if prop_id:
                            property_ids.add(prop_id)
        
        # Check for user-specific properties if logged in
        user_properties = home_data.get('UserProperties', [])
        if user_properties and isinstance(user_properties, list):
            print(f"Found {len(user_properties)} user properties (favorites/saved)")
            for prop in user_properties:
                if isinstance(prop, dict):
                    prop_id = prop.get('PropertyId')
                    if prop_id and prop.get('PropertyClassId') == 1:
                        property_ids.add(prop_id)
        
        # Check favorites from top level
        favourites = data.get('Favourites', [])
        if favourites and isinstance(favourites, list):
            print(f"Found {len(favourites)} favorites")
            for prop in favourites:
                if isinstance(prop, dict):
                    prop_id = prop.get('PropertyId')
                    if prop_id and prop.get('PropertyClassId') == 1:
                        property_ids.add(prop_id)
        
        property_ids = list(property_ids)
        print(f"Found {len(property_ids)} property IDs")
        return property_ids
        
    except requests.RequestException as e:
        print(f"Error fetching property IDs: {e}")
        return []


def fetch_property_brochure(property_id, delay=1.0):
    """Fetch complete property details from /brochure endpoint"""
    endpoint = f"{MYHOME_API_BASE}/brochure/{property_id}"
    params = {
        'ApiKey': MYHOME_API_KEY,
        'CorrelationId': str(uuid.uuid4()),
        'format': 'json'
    }
    
    # Add session cookie if available
    cookies = {}
    if MYHOME_SESSION_COOKIE:
        cookies['session'] = MYHOME_SESSION_COOKIE
    
    try:
        response = requests.get(endpoint, params=params, cookies=cookies, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Respectful delay between requests
        sleep(delay)
        
        return data.get('Brochure', {})
        
    except requests.RequestException as e:
        print(f"  Error fetching property {property_id}: {e}")
        return None


def parse_price(price_obj):
    """Extract price from price object"""
    if not price_obj:
        return None
    
    # Price object has MinPrice and MaxPrice
    min_price = price_obj.get('MinPrice')
    max_price = price_obj.get('MaxPrice')
    
    # Use average if range, otherwise use MinPrice
    if min_price and max_price and min_price != max_price:
        return (min_price + max_price) / 2
    return min_price if min_price else None


def clean_html(html_text):
    """Remove HTML tags from text"""
    if not html_text:
        return None
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', html_text)
    # Collapse whitespace
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean if clean else None


def parse_brochure_to_property(brochure_data):
    """Convert brochure API response to Property model data"""
    
    if not isinstance(brochure_data, dict):
        return None
    
    prop = brochure_data.get('Property', {})
    if not isinstance(prop, dict):
        return None
    
    property_id = prop.get('PropertyId')
    if not property_id:
        return None
    
    # Only import residential for sale (PropertyClassId=1)
    if prop.get('PropertyClassId') != 1:
        return None
    
    # Extract address info
    display_address = prop.get('DisplayAddress', '')
    brochure_map = prop.get('BrochureMap', {})
    if not isinstance(brochure_map, dict):
        brochure_map = {}
    
    # Extract coordinates
    latitude = brochure_map.get('Latitude')
    longitude = brochure_map.get('Longitude')
    
    # Extract price
    price = parse_price(prop.get('Price'))
    if not price:
        # Skip properties with no price (e.g., POA)
        return None
    
    # Extract BER rating
    ber_rating = prop.get('BerRating')
    if ber_rating and ber_rating not in BER_RATINGS:
        ber_rating = None
    
    # Extract description - can be in Features (array or dict) or BrochureContent
    description = None
    features = brochure_data.get('Features')
    if isinstance(features, dict):
        description = clean_html(features.get('Description'))
    elif isinstance(features, list) and len(features) > 0:
        description = clean_html(features[0].get('Description'))
    
    # Try BrochureContent as fallback
    if not description:
        brochure_content = prop.get('BrochureContent', {})
        if isinstance(brochure_content, dict):
            description = clean_html(brochure_content.get('Description'))
    
    # Get main photo
    main_photo = prop.get('MainPhoto')
    
    # Extract property type
    property_type = prop.get('PropertyType') or 'House'
    
    # Bedrooms and bathrooms
    bedrooms = prop.get('Bedrooms') or 0
    bathrooms = prop.get('Bathrooms') or 0
    
    # Size in square meters
    size_str = prop.get('SizeStringMeters')
    size_sqm = None
    if size_str:
        # Convert to string if needed
        size_str = str(size_str)
        # Extract number from string like "122" or "122 m²"
        match = re.search(r'(\d+)', size_str)
        if match:
            try:
                size_sqm = int(match.group(1))
            except (ValueError, AttributeError):
                pass
    
    # Extract county and city
    county = brochure_map.get('County') or extract_county_from_address(display_address)
    city = brochure_map.get('LocalityName')
    
    # Eircode (postal code)
    eircode = prop.get('Eircode')
    
    return {
        'external_id': str(property_id),
        'source': 'myhome.ie',
        'title': display_address,
        'address': display_address,
        'city': city,
        'county': county,
        'eircode': eircode,
        'latitude': latitude,
        'longitude': longitude,
        'price': price,
        'bedrooms': bedrooms,
        'bathrooms': bathrooms,
        'property_type': property_type,
        'size_sqm': size_sqm,
        'ber_rating': ber_rating,
        'description': description,
        'image_url': main_photo,
        'url': f"https://www.myhome.ie/residential/brochure/{property_id}",
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }


def extract_county_from_address(address):
    """Extract county from address string as fallback"""
    if not address:
        return None
    
    # Common Irish counties
    counties = [
        'Dublin', 'Cork', 'Galway', 'Limerick', 'Waterford', 'Clare', 'Kerry',
        'Tipperary', 'Mayo', 'Donegal', 'Wicklow', 'Meath', 'Kildare', 'Wexford',
        'Kilkenny', 'Carlow', 'Laois', 'Offaly', 'Westmeath', 'Longford', 'Louth',
        'Monaghan', 'Cavan', 'Sligo', 'Leitrim', 'Roscommon'
    ]
    
    for county in counties:
        if county in address:
            return county
    
    # Try "Co. County" format
    match = re.search(r'Co\.\s*(\w+)', address, re.IGNORECASE)
    if match:
        return match.group(1)
    
    return None


def import_properties(property_ids, max_results=None, delay=1.0):
    """Import properties from brochure API into database"""
    
    if not property_ids:
        print("No property IDs to import")
        return
    
    # Limit results if specified
    if max_results:
        property_ids = property_ids[:max_results]
    
    print(f"\nFetching detailed data for {len(property_ids)} properties...")
    print("This may take a while (respectful delay between requests)\n")
    
    with app.app_context():
        added = 0
        updated = 0
        skipped = 0
        errors = 0
        
        for i, prop_id in enumerate(property_ids, 1):
            try:
                print(f"[{i}/{len(property_ids)}] Fetching property {prop_id}...", end=' ')
                
                # Fetch brochure data
                brochure_data = fetch_property_brochure(prop_id, delay=delay)
                if not brochure_data:
                    print("ERROR - Failed to fetch")
                    errors += 1
                    continue
                
                # Parse to Property model
                prop_data = parse_brochure_to_property(brochure_data)
                if not prop_data:
                    print("SKIPPED - Not residential for sale or no price")
                    skipped += 1
                    continue
                
                # Check if property already exists
                existing = Property.query.filter_by(
                    external_id=prop_data['external_id'],
                    source='myhome.ie'
                ).first()
                
                if existing:
                    # Check if price or key details changed
                    if (existing.price != prop_data['price'] or 
                        existing.description != prop_data['description']):
                        # Update existing property
                        for key, value in prop_data.items():
                            setattr(existing, key, value)
                        existing.updated_at = datetime.utcnow()
                        updated += 1
                        print(f"UPDATED - {prop_data['address'][:50]}")
                    else:
                        skipped += 1
                        print(f"EXISTS - {prop_data['address'][:50]}")
                else:
                    # Create new property
                    new_property = Property(**prop_data)
                    db.session.add(new_property)
                    added += 1
                    coords = f"({prop_data['latitude']:.4f}, {prop_data['longitude']:.4f})" if prop_data['latitude'] else "(no coords)"
                    print(f"ADDED - {prop_data['address'][:40]} - €{prop_data['price']:,.0f} - {coords}")
                
            except Exception as e:
                print(f"ERROR - {e}")
                errors += 1
                continue
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n{'='*70}")
            print("✓ Import complete!")
            print(f"{'='*70}")
            print(f"  Added:   {added}")
            print(f"  Updated: {updated}")
            print(f"  Skipped: {skipped}")
            print(f"  Errors:  {errors}")
            print(f"\nNote: Using public API key from browser requests")
            print(f"Rate limiting: {delay}s delay between requests")
        except Exception as e:
            db.session.rollback()
            print(f"\nERROR: Database commit failed: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Import properties from MyHome.ie Brochure API'
    )
    parser.add_argument(
        '--max-results', 
        type=int, 
        help='Maximum properties to import'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='Delay between API requests in seconds (default: 1.0)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("MyHome.ie Brochure API Property Importer")
    print("=" * 70)
    print("\nThis script:")
    print("1. Fetches property IDs from /home endpoint")
    print("2. Queries /brochure/{id} for complete details")
    print("3. Imports with coordinates, descriptions, and metadata")
    print(f"\nDelay between requests: {args.delay}s")
    print()
    
    # Get property IDs from /home endpoint
    property_ids = get_property_ids_from_home()
    
    # Import detailed data
    if property_ids:
        import_properties(property_ids, max_results=args.max_results, delay=args.delay)
    else:
        print("\nNo properties found. API may be unavailable.")


if __name__ == '__main__':
    main()
