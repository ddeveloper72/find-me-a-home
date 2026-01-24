"""
Scheduled RSS feed importer with best practices
Downloads feed manually from browser, then imports on schedule
"""
import feedparser
import requests
from datetime import datetime
from models import Property
from extensions import db
from app import app
import os
import re

def extract_property_details(description):
    """Extract property details from RSS description"""
    price_match = re.search(r'&euro;([\d,]+)', description)
    beds_match = re.search(r'(\d+)\s+Bedroom', description)
    baths_match = re.search(r'(\d+)\s+Bathroom', description)
    
    # Property types
    types = {
        'Semi-Detached House': 'house',
        'Detached House': 'house',
        'Terraced House': 'house',
        'End of Terrace House': 'house',
        'Apartment': 'apartment',
        'Duplex': 'apartment',
        'Bungalow': 'house'
    }
    
    prop_type = 'house'
    for type_str, type_val in types.items():
        if type_str in description:
            prop_type = type_val
            break
    
    return {
        'price': float(price_match.group(1).replace(',', '')) if price_match else None,
        'bedrooms': int(beds_match.group(1)) if beds_match else 3,
        'bathrooms': int(baths_match.group(1)) if baths_match else 2,
        'property_type': prop_type
    }

def import_from_feed_file(filename='feed.xml'):
    """Import from saved RSS feed file"""
    if not os.path.exists(filename):
        print(f"❌ File not found: {filename}")
        print("Download the RSS feed from your browser first:")
        print("  1. Open https://rss.property.ie/property-for-sale/")
        print("  2. Save as 'feed.xml'")
        return
    
    print(f"📥 Reading feed from {filename}...")
    feed = feedparser.parse(filename)
    
    if feed.bozo:
        print(f"⚠️  Feed parsing warning: {feed.bozo_exception}")
    
    print(f"Found {len(feed.entries)} properties in feed")
    
    with app.app_context():
        new_count = 0
        updated_count = 0
        skipped_count = 0
        
        for entry in feed.entries:
            try:
                # Extract coordinates
                lat = float(entry.get('geo_lat', 0))
                lon = float(entry.get('geo_long', 0))
                
                if not lat or not lon:
                    skipped_count += 1
                    continue
                
                # Check if exists by unique ID (link)
                existing = Property.query.filter_by(
                    latitude=lat,
                    longitude=lon
                ).first()
                
                # Extract details
                details = extract_property_details(entry.description)
                
                # Parse location from title
                title = entry.title.strip()
                parts = [p.strip() for p in title.split(',')]
                county = None
                city = None
                
                for part in parts:
                    if part.startswith('Co. '):
                        county = part.replace('Co. ', '').strip()
                    elif part and not part.startswith('Co.') and len(parts) > 2:
                        if part == parts[-2]:
                            city = part
                
                # Clean description
                clean_desc = re.sub(r'<[^>]+>', '', entry.description)
                clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()[:500]
                
                property_data = {
                    'title': title,
                    'address': title,
                    'city': city,
                    'county': county,
                    'price': details['price'],
                    'bedrooms': details['bedrooms'],
                    'bathrooms': details['bathrooms'],
                    'property_type': details['property_type'],
                    'size_sqm': 70 + (details['bedrooms'] * 20),
                    'description': clean_desc,
                    'latitude': lat,
                    'longitude': lon
                }
                
                if existing:
                    # Update existing property with new price/details
                    for key, value in property_data.items():
                        if value:
                            setattr(existing, key, value)
                    updated_count += 1
                else:
                    # Create new property
                    new_property = Property(**property_data)
                    db.session.add(new_property)
                    new_count += 1
                
                if (new_count + updated_count) % 10 == 0:
                    db.session.commit()
                    print(f"Progress: {new_count} new, {updated_count} updated...")
                    
            except Exception as e:
                print(f"Error processing entry: {e}")
                continue
        
        db.session.commit()
        
        print(f"\n✅ Import complete!")
        print(f"   New properties: {new_count}")
        print(f"   Updated properties: {updated_count}")
        print(f"   Skipped (no coordinates): {skipped_count}")
        print(f"   Total in database: {Property.query.count()}")
        print(f"   Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    import sys
    
    filename = sys.argv[1] if len(sys.argv) > 1 else 'feed.xml'
    import_from_feed_file(filename)
