#!/usr/bin/env python
"""
Property import script using Property.ie RSS feeds
Fetches property listings from RSS and imports to database
"""

import sys
import os
import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from html.parser import HTMLParser

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db
from models import Property

# Property.ie RSS Feeds
RSS_FEEDS = {
    'for-sale': 'https://rss.property.ie/property-for-sale/',
    'dublin': 'https://rss.property.ie/property-for-sale/dublin/',
    'cork': 'https://rss.property.ie/property-for-sale/cork/',
    'galway': 'https://rss.property.ie/property-for-sale/galway/',
    'limerick': 'https://rss.property.ie/property-for-sale/limerick/',
    'waterford': 'https://rss.property.ie/property-for-sale/waterford/',
}

# Namespace for geo tags
NAMESPACES = {
    'geo': 'http://www.w3.org/2003/01/geo/wgs84_pos#'
}


class PropertyHTMLParser(HTMLParser):
    """Parse HTML description to extract property details"""
    
    def __init__(self):
        super().__init__()
        self.data = {}
        self.current_tag = None
        self.buffer = []
    
    def handle_data(self, data):
        text = data.strip()
        if text:
            self.buffer.append(text)
    
    def get_text(self):
        """Get all collected text"""
        return ' '.join(self.buffer)


def parse_property_description(html_desc):
    """
    Extract property details from HTML description
    
    Returns dict with: price, bedrooms, bathrooms, property_type, agent, description
    """
    parser = PropertyHTMLParser()
    parser.feed(html_desc)
    text = parser.get_text()
    
    details = {
        'price': None,
        'bedrooms': None,
        'bathrooms': None,
        'property_type': None,
        'agent': None,
        'description': None
    }
    
    # Extract price (e.g., "€425,000")
    price_match = re.search(r'€([\d,]+)', text)
    if price_match:
        price_str = price_match.group(1).replace(',', '')
        try:
            details['price'] = float(price_str)
        except ValueError:
            pass
    
    # Extract bedrooms (e.g., "3 Bedrooms")
    bed_match = re.search(r'(\d+)\s+Bedroom', text, re.IGNORECASE)
    if bed_match:
        try:
            details['bedrooms'] = int(bed_match.group(1))
        except ValueError:
            pass
    
    # Extract bathrooms (e.g., "2 Bathrooms")
    bath_match = re.search(r'(\d+)\s+Bathroom', text, re.IGNORECASE)
    if bath_match:
        try:
            details['bathrooms'] = int(bath_match.group(1))
        except ValueError:
            pass
    
    # Extract property type (House, Apartment, Bungalow, etc.)
    type_patterns = [
        r'(Detached House|Semi-Detached House|Terraced House|End of Terrace House)',
        r'(Apartment|Duplex|Penthouse)',
        r'(Bungalow)',
        r'(House For Sale|House)',
    ]
    for pattern in type_patterns:
        type_match = re.search(pattern, text, re.IGNORECASE)
        if type_match:
            details['property_type'] = type_match.group(1)
            break
    
    # Extract agent (e.g., "Agent: Sherry FitzGerald")
    agent_match = re.search(r'Agent:\s*([^<\n]+)', text)
    if agent_match:
        details['agent'] = agent_match.group(1).strip()
    
    # Extract description (text after agent before "View full ad")
    desc_match = re.search(r'Agent:.*?<br\s*/?>(.+?)(?:View full ad|$)', html_desc, re.DOTALL)
    if desc_match:
        desc_text = re.sub(r'<[^>]+>', '', desc_match.group(1))
        desc_text = re.sub(r'\s+', ' ', desc_text).strip()
        if len(desc_text) > 50:  # Only use if substantial
            details['description'] = desc_text[:500]  # Limit length
    
    return details


def extract_address_components(title, link):
    """
    Extract address, county, city from property title and link
    
    Example title: "15 Oak Park Avenue, Oak Park, Naas, Co. Kildare"
    """
    # Remove CDATA if present
    title = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', title)
    title = title.strip()
    
    components = {
        'address': None,
        'county': None,
        'city': None,
    }
    
    # Split by comma
    parts = [p.strip() for p in title.split(',')]
    
    if parts:
        # First part is usually street address
        components['address'] = parts[0]
        
        # Look for county (starts with "Co." or "County")
        for part in parts:
            if part.startswith('Co.') or part.startswith('County'):
                components['county'] = part.replace('Co.', '').replace('County', '').strip()
                break
        
        # City/town is usually the last or second-to-last part (before county)
        if len(parts) >= 2:
            # Check if last part is county
            if parts[-1].startswith('Co.') or parts[-1].startswith('County'):
                if len(parts) >= 3:
                    components['city'] = parts[-2]
            else:
                components['city'] = parts[-1]
    
    return components


def fetch_rss_feed(url):
    """Fetch and parse RSS feed"""
    try:
        print(f"Fetching: {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        
        # Parse XML
        root = ET.fromstring(response.content)
        
        # Find all items
        items = root.findall('.//item')
        print(f"  Found {len(items)} properties")
        
        return items
    
    except Exception as e:
        print(f"  ❌ Error fetching feed: {e}")
        return []


def parse_property_item(item):
    """Parse single property RSS item"""
    try:
        # Extract basic fields
        title = item.find('title').text if item.find('title') is not None else ''
        link = item.find('link').text if item.find('link') is not None else ''
        description_html = item.find('description').text if item.find('description') is not None else ''
        pub_date_str = item.find('pubDate').text if item.find('pubDate') is not None else ''
        
        # Extract geolocation
        lat_elem = item.find('geo:lat', NAMESPACES)
        lon_elem = item.find('geo:long', NAMESPACES)
        
        latitude = float(lat_elem.text) if lat_elem is not None and lat_elem.text else None
        longitude = float(lon_elem.text) if lon_elem is not None and lon_elem.text else None
        
        # Parse description HTML for details
        details = parse_property_description(description_html)
        
        # Extract address components
        address_parts = extract_address_components(title, link)
        
        # Create external ID from link
        external_id = link.split('/')[-2] if '/' in link else None
        
        # Build property dict
        property_data = {
            'external_id': external_id,
            'source': 'property.ie',
            'title': title,
            'description': details['description'],
            'price': details['price'],
            'address': address_parts['address'],
            'county': address_parts['county'],
            'city': address_parts['city'],
            'latitude': latitude,
            'longitude': longitude,
            'bedrooms': details['bedrooms'],
            'bathrooms': details['bathrooms'],
            'property_type': details['property_type'],
            'url': link,
        }
        
        return property_data
    
    except Exception as e:
        print(f"  ⚠️  Error parsing item: {e}")
        return None


def import_properties(feed_name='for-sale', max_properties=None):
    """
    Import properties from RSS feed
    
    Args:
        feed_name: Name of feed from RSS_FEEDS dict
        max_properties: Maximum number to import (for testing)
    """
    print("="*80)
    print(f"PROPERTY IMPORT - Property.ie RSS ({feed_name})")
    print("="*80)
    
    if feed_name not in RSS_FEEDS:
        print(f"❌ Unknown feed: {feed_name}")
        print(f"Available feeds: {', '.join(RSS_FEEDS.keys())}")
        return
    
    feed_url = RSS_FEEDS[feed_name]
    
    with app.app_context():
        # Fetch RSS feed
        items = fetch_rss_feed(feed_url)
        
        if not items:
            print("No properties found in feed")
            return
        
        if max_properties:
            items = items[:max_properties]
            print(f"⚠️  Limited to {max_properties} properties for testing")
        
        print(f"\nProcessing {len(items)} properties...")
        print("-"*80)
        
        new_count = 0
        updated_count = 0
        error_count = 0
        
        for i, item in enumerate(items, 1):
            property_data = parse_property_item(item)
            
            if not property_data:
                error_count += 1
                continue
            
            # Check if property exists
            existing = None
            if property_data['external_id']:
                existing = Property.query.filter_by(
                    external_id=property_data['external_id'],
                    source='property.ie'
                ).first()
            
            try:
                if existing:
                    # Update existing
                    for key, value in property_data.items():
                        if value is not None:  # Only update non-None values
                            setattr(existing, key, value)
                    updated_count += 1
                    status = "✓ Updated"
                else:
                    # Create new
                    prop = Property(**property_data)
                    db.session.add(prop)
                    new_count += 1
                    status = "✓ New"
                
                # Print progress
                price_str = f"€{property_data['price']:,.0f}" if property_data['price'] else "N/A"
                print(f"[{i}/{len(items)}] {status:10} | {price_str:12} | {property_data['title'][:60]}")
                
                # Commit in batches
                if (new_count + updated_count) % 20 == 0:
                    db.session.commit()
                    print(f"  💾 Batch commit ({new_count} new, {updated_count} updated)")
            
            except Exception as e:
                print(f"  ❌ Error saving: {e}")
                error_count += 1
                db.session.rollback()
        
        # Final commit
        try:
            db.session.commit()
            print("-"*80)
            print("\n✅ Import Complete:")
            print(f"   New: {new_count}")
            print(f"   Updated: {updated_count}")
            print(f"   Errors: {error_count}")
            
            # Database summary
            total_props = Property.query.count()
            with_coords = Property.query.filter(
                Property.latitude.isnot(None),
                Property.longitude.isnot(None)
            ).count()
            
            print(f"\nDatabase: {total_props:,} total properties")
            print(f"  With coordinates: {with_coords:,} ({with_coords/total_props*100:.1f}%)")
            print("="*80)
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error committing: {e}")


def main():
    """Main function with command-line options"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Import properties from Property.ie RSS feeds')
    parser.add_argument('--feed', default='for-sale', choices=RSS_FEEDS.keys(),
                       help='RSS feed to import from')
    parser.add_argument('--test', type=int, metavar='N',
                       help='Test mode: only import N properties')
    
    args = parser.parse_args()
    
    import_properties(feed_name=args.feed, max_properties=args.test)


if __name__ == '__main__':
    main()
