"""
Import properties from Daft.ie API

This script fetches property listings from the Daft.ie SOAP API and imports them into the database.
Requires a Daft.ie API key (set in .env as DAFT_API_KEY).

Usage:
    python scripts/import_daft_properties.py [--county COUNTY] [--max-price PRICE] [--min-beds BEDS]
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import requests
from xml.etree import ElementTree as ET

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import app, db
from models import Property

# Daft.ie API Configuration
DAFT_API_BASE = "https://api.daft.ie/v3"
DAFT_API_KEY = os.getenv('DAFT_API_KEY')

# SOAP XML namespace
SOAP_NS = {
    'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
    'daft': 'http://api.daft.ie/v3'
}


def build_search_request(county=None, min_price=None, max_price=None, min_beds=None, max_beds=None, 
                         property_type=None, max_results=100):
    """Build SOAP request XML for property search"""
    
    # Build filter XML
    filters = []
    if county:
        filters.append(f"<county>{county}</county>")
    if min_price:
        filters.append(f"<min_price>{min_price}</min_price>")
    if max_price:
        filters.append(f"<max_price>{max_price}</max_price>")
    if min_beds:
        filters.append(f"<min_beds>{min_beds}</min_beds>")
    if max_beds:
        filters.append(f"<max_beds>{max_beds}</max_beds>")
    if property_type:
        filters.append(f"<property_type>{property_type}</property_type>")
    
    filters.append(f"<max_results>{max_results}</max_results>")
    
    filter_xml = ''.join(filters)
    
    # Build complete SOAP envelope
    soap_request = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Header>
        <api_key>{DAFT_API_KEY}</api_key>
    </soap:Header>
    <soap:Body>
        <search_sale xmlns="http://api.daft.ie/v3">
            {filter_xml}
        </search_sale>
    </soap:Body>
</soap:Envelope>"""
    
    return soap_request


def parse_property_from_xml(ad_element):
    """Extract property data from XML ad element"""
    
    def get_text(element, tag, default=''):
        """Safely get text from XML element"""
        child = element.find(tag, SOAP_NS)
        return child.text if child is not None and child.text else default
    
    def get_float(element, tag, default=None):
        """Safely get float from XML element"""
        text = get_text(element, tag)
        try:
            return float(text) if text else default
        except (ValueError, TypeError):
            return default
    
    def get_int(element, tag, default=None):
        """Safely get integer from XML element"""
        text = get_text(element, tag)
        try:
            return int(text) if text else default
        except (ValueError, TypeError):
            return default
    
    # Extract basic property info
    property_data = {
        'external_id': get_text(ad_element, 'daft:ad_id'),
        'source': 'daft.ie',
        'title': get_text(ad_element, 'daft:title'),
        'description': get_text(ad_element, 'daft:description'),
        'price': get_float(ad_element, 'daft:price', 0),
        'address': get_text(ad_element, 'daft:address'),
        'county': get_text(ad_element, 'daft:county'),
        'city': get_text(ad_element, 'daft:city'),
        'eircode': get_text(ad_element, 'daft:eircode'),
        'latitude': get_float(ad_element, 'daft:latitude'),
        'longitude': get_float(ad_element, 'daft:longitude'),
        'bedrooms': get_int(ad_element, 'daft:num_bedrooms'),
        'bathrooms': get_int(ad_element, 'daft:num_bathrooms'),
        'property_type': get_text(ad_element, 'daft:property_type'),
        'size_sqm': get_float(ad_element, 'daft:floor_area'),
        'ber_rating': get_text(ad_element, 'daft:ber_rating'),
        'url': get_text(ad_element, 'daft:url'),
    }
    
    # Extract image URLs
    images_element = ad_element.find('daft:images', SOAP_NS)
    if images_element is not None:
        image_urls = [img.text for img in images_element.findall('daft:image', SOAP_NS) if img.text]
        property_data['image_urls'] = image_urls if image_urls else None
    
    return property_data


def fetch_properties(county=None, min_price=None, max_price=None, min_beds=None, max_beds=None, 
                    property_type=None, max_results=100):
    """Fetch properties from Daft.ie API"""
    
    if not DAFT_API_KEY:
        print("ERROR: DAFT_API_KEY not found in environment variables")
        print("Please add your Daft.ie API key to the .env file:")
        print("DAFT_API_KEY=your-api-key-here")
        return []
    
    print(f"Fetching properties from Daft.ie API...")
    print(f"Filters: county={county}, price={min_price}-{max_price}, beds={min_beds}+")
    
    # Build SOAP request
    soap_request = build_search_request(
        county=county,
        min_price=min_price,
        max_price=max_price,
        min_beds=min_beds,
        max_beds=max_beds,
        property_type=property_type,
        max_results=max_results
    )
    
    # Make API request
    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': 'http://api.daft.ie/v3/search_sale'
    }
    
    try:
        response = requests.post(f"{DAFT_API_BASE}/", data=soap_request, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse XML response
        root = ET.fromstring(response.content)
        
        # Find all ad elements
        ads = root.findall('.//daft:ad', SOAP_NS)
        
        print(f"Found {len(ads)} properties")
        
        # Parse each property
        properties = []
        for ad in ads:
            try:
                property_data = parse_property_from_xml(ad)
                if property_data['external_id']:  # Only add if we have an ID
                    properties.append(property_data)
            except Exception as e:
                print(f"Error parsing property: {e}")
                continue
        
        return properties
        
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return []
    except ET.ParseError as e:
        print(f"XML parsing failed: {e}")
        return []


def import_properties(properties):
    """Import properties into the database"""
    
    if not properties:
        print("No properties to import")
        return
    
    print(f"\nImporting {len(properties)} properties to database...")
    
    with app.app_context():
        added = 0
        updated = 0
        errors = 0
        
        for prop_data in properties:
            try:
                # Check if property already exists
                existing = Property.query.filter_by(
                    external_id=prop_data['external_id'],
                    source='daft.ie'
                ).first()
                
                if existing:
                    # Update existing property
                    for key, value in prop_data.items():
                        setattr(existing, key, value)
                    existing.updated_at = datetime.utcnow()
                    updated += 1
                else:
                    # Create new property
                    new_property = Property(**prop_data)
                    db.session.add(new_property)
                    added += 1
                
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
            print(f"  Errors: {errors}")
        except Exception as e:
            db.session.rollback()
            print(f"\nERROR: Database commit failed: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Import properties from Daft.ie API')
    parser.add_argument('--county', help='Filter by county (e.g., Dublin, Cork)')
    parser.add_argument('--min-price', type=float, help='Minimum price')
    parser.add_argument('--max-price', type=float, help='Maximum price')
    parser.add_argument('--min-beds', type=int, help='Minimum bedrooms')
    parser.add_argument('--max-beds', type=int, help='Maximum bedrooms')
    parser.add_argument('--type', help='Property type (e.g., house, apartment)')
    parser.add_argument('--max-results', type=int, default=100, help='Maximum results (default: 100)')
    
    args = parser.parse_args()
    
    # Fetch properties from API
    properties = fetch_properties(
        county=args.county,
        min_price=args.min_price,
        max_price=args.max_price,
        min_beds=args.min_beds,
        max_beds=args.max_beds,
        property_type=args.type,
        max_results=args.max_results
    )
    
    # Import to database
    if properties:
        import_properties(properties)
    else:
        print("\nNo properties fetched. Check API key and filters.")


if __name__ == '__main__':
    main()
