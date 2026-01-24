"""
Import properties from Property.ie RSS feed
Can work with saved XML file or attempt direct download
"""
import xml.etree.ElementTree as ET
import re
from datetime import datetime
from models import Property
from extensions import db
from app import app

def extract_price(description):
    """Extract price from description"""
    match = re.search(r'&euro;([\d,]+)', description)
    if match:
        return float(match.group(1).replace(',', ''))
    return None

def extract_bedrooms(description):
    """Extract bedrooms from description"""
    match = re.search(r'(\d+)\s+Bedroom', description)
    if match:
        return int(match.group(1))
    return None

def extract_bathrooms(description):
    """Extract bathrooms from description"""
    match = re.search(r'(\d+)\s+Bathroom', description)
    if match:
        return int(match.group(1))
    return None

def extract_property_type(description):
    """Extract property type from description"""
    types = {
        'Semi-Detached House': 'house',
        'Detached House': 'house',
        'Terraced House': 'house',
        'End of Terrace House': 'house',
        'Apartment': 'apartment',
        'Duplex': 'apartment',
        'Bungalow': 'house'
    }
    
    for type_str, type_val in types.items():
        if type_str in description:
            return type_val
    return 'house'  # Default

def extract_city_county(title):
    """Extract city and county from title"""
    # Title format: "Address, City, Co. County"
    parts = [p.strip() for p in title.split(',')]
    
    county = None
    city = None
    
    # Look for "Co. County" pattern
    for part in parts:
        if part.startswith('Co. '):
            county = part.replace('Co. ', '').strip()
        elif part and not part.startswith('Co.') and len(parts) > 2:
            # Second to last part is usually the city/area
            if part == parts[-2]:
                city = part
    
    return city, county

def parse_rss_feed(xml_content):
    """Parse RSS feed XML and extract property data"""
    # Define namespace
    namespaces = {
        'geo': 'http://www.w3.org/2003/01/geo/wgs84_pos#'
    }
    
    root = ET.fromstring(xml_content)
    items = root.findall('.//item')
    
    properties = []
    
    for item in items:
        try:
            # Extract basic fields
            title_elem = item.find('title')
            title = title_elem.text.strip() if title_elem is not None else None
            
            link_elem = item.find('link')
            link = link_elem.text.strip() if link_elem is not None else None
            
            desc_elem = item.find('description')
            description = desc_elem.text if desc_elem is not None else ''
            
            # Extract geocoordinates
            lat_elem = item.find('geo:lat', namespaces)
            lon_elem = item.find('geo:long', namespaces)
            
            if lat_elem is None or lon_elem is None:
                print(f"Skipping property without coordinates: {title}")
                continue
                
            latitude = float(lat_elem.text)
            longitude = float(lon_elem.text)
            
            # Extract property details from description
            price = extract_price(description)
            bedrooms = extract_bedrooms(description)
            bathrooms = extract_bathrooms(description)
            property_type = extract_property_type(description)
            
            # Extract location
            city, county = extract_city_county(title)
            
            # Clean description (remove HTML)
            clean_desc = re.sub(r'<[^>]+>', '', description)
            clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
            # Get first 500 chars
            clean_desc = clean_desc[:500] + '...' if len(clean_desc) > 500 else clean_desc
            
            # Estimate size (typical Irish homes: 90-150 sqm)
            size_sqm = None
            if bedrooms:
                size_sqm = 70 + (bedrooms * 20)  # Rough estimate
            
            property_data = {
                'title': title,
                'address': title,  # Use title as address
                'city': city,
                'county': county,
                'price': price,
                'bedrooms': bedrooms or 3,  # Default if not found
                'bathrooms': bathrooms or 2,
                'property_type': property_type,
                'size_sqm': size_sqm or 100,
                'description': clean_desc,
                'latitude': latitude,
                'longitude': longitude,
                'listing_url': link
            }
            
            properties.append(property_data)
            
        except Exception as e:
            print(f"Error parsing property: {e}")
            continue
    
    return properties

def import_from_file(filename):
    """Import properties from saved RSS XML file"""
    print(f"Reading RSS feed from {filename}...")
    
    with open(filename, 'r', encoding='utf-8') as f:
        xml_content = f.read()
    
    print("Parsing RSS feed...")
    properties = parse_rss_feed(xml_content)
    
    print(f"Found {len(properties)} properties")
    
    # Import to database
    with app.app_context():
        imported = 0
        skipped = 0
        
        for prop_data in properties:
            # Check if property already exists (by URL)
            existing = Property.query.filter_by(listing_url=prop_data['listing_url']).first()
            
            if existing:
                skipped += 1
                continue
            
            # Create new property
            prop = Property(**prop_data)
            db.session.add(prop)
            imported += 1
            
            if imported % 10 == 0:
                print(f"Imported {imported} properties...")
        
        db.session.commit()
        print(f"\n✓ Import complete!")
        print(f"  Imported: {imported}")
        print(f"  Skipped (duplicates): {skipped}")
        print(f"  Total in database: {Property.query.count()}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python import_rss_feed.py <rss_file.xml>")
        print("\nTo use:")
        print("1. Open https://rss.property.ie/property-for-sale/ in your browser")
        print("2. Save the page as 'feed.xml'")
        print("3. Run: python import_rss_feed.py feed.xml")
        sys.exit(1)
    
    import_from_file(sys.argv[1])
