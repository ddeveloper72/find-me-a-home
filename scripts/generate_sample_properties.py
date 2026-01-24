#!/usr/bin/env python
"""
Generate sample property data for development/testing
Creates realistic Irish property listings with geocoded locations
"""

import sys
import os
import random
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db
from models import Property, School, TransportStation

# Irish property data templates
PROPERTY_TYPES = [
    'Detached House',
    'Semi-Detached House', 
    'Terraced House',
    'Apartment',
    'Bungalow',
    'Duplex',
]

# Dublin areas with typical price ranges (in thousands)
DUBLIN_AREAS = {
    'Dublin 2': (400, 950),
    'Dublin 4': (450, 1200),
    'Dublin 6': (400, 900),
    'Dublin 8': (300, 650),
    'Blackrock': (500, 1100),
    'Dalkey': (600, 1500),
    'Malahide': (400, 850),
    'Howth': (450, 950),
    'Clontarf': (400, 850),
    'Rathgar': (500, 1000),
    'Rathmines': (350, 750),
    'Ballsbridge': (550, 1300),
    'Sandymount': (450, 900),
    'Donnybrook': (500, 1200),
    'Swords': (300, 550),
    'Lucan': (280, 500),
    'Tallaght': (250, 450),
}

CORK_AREAS = {
    'Cork City Centre': (250, 600),
    'Douglas': (300, 650),
    'Ballincollig': (250, 500),
    'Blackrock (Cork)': (280, 550),
    'Bishopstown': (250, 500),
}

GALWAY_AREAS = {
    'Galway City Centre': (250, 600),
    'Salthill': (300, 650),
    'Renmore': (250, 500),
    'Newcastle': (280, 550),
}

OTHER_AREAS = {
    'Limerick City': (200, 450),
    'Waterford City': (180, 400),
    'Kilkenny': (200, 450),
    'Drogheda': (220, 450),
    'Dundalk': (180, 400),
    'Sligo': (160, 380),
    'Tralee': (180, 400),
    'Athlone': (160, 350),
    'Ennis': (180, 400),
    'Navan': (200, 450),
    'Maynooth': (280, 550),
    'Celbridge': (280, 550),
    'Naas': (250, 500),
    'Portlaoise': (180, 400),
}

STREET_NAMES = [
    'Main Street', 'Church Road', 'Station Road', 'Park Avenue', 'Green Road',
    'Mill Lane', 'Oak Drive', 'Elm Grove', 'Maple Terrace', 'Willow Park',
    'Riverside Drive', 'Castle Street', 'Abbey Road', 'Market Square', 'Bridge Street',
    'High Street', 'Millbrook', 'Ashwood', 'Beechwood', 'Fairview',
]

ESTATE_NAMES = [
    'The Oaks', 'The Meadows', 'The Grove', 'The Park', 'The Green',
    'Riverside', 'Brookfield', 'Fairways', 'Parklands', 'Woodlands',
    'The Heights', 'The Gardens', 'The Court', 'The Chase', 'The Grange',
]

DESCRIPTION_TEMPLATES = [
    "Well presented {bedrooms} bedroom {property_type} in sought-after {area}. Bright and spacious accommodation throughout. Convenient to all local amenities including shops, schools and transport links.",
    
    "Charming {bedrooms} bed {property_type} situated in the heart of {area}. This lovely home features {features} and is within walking distance of excellent schools and transport.",
    
    "Superb {bedrooms} bedroom {property_type} in prime {area} location. Beautifully maintained with {features}. Viewing highly recommended.",
    
    "Stunning {property_type} with {bedrooms} bedrooms located in popular {area}. The property boasts {features} and benefits from close proximity to all amenities.",
    
    "Impressive {bedrooms} bed {property_type} in excellent {area} location. Features include {features}. Ideal family home close to schools and transport.",
]

FEATURES = [
    ['modern fitted kitchen', 'spacious living room', 'private garden'],
    ['open plan living', 'master ensuite', 'off-street parking'],
    ['contemporary kitchen', 'hardwood floors', 'south-facing garden'],
    ['fitted wardrobes', 'guest WC', 'large rear garden'],
    ['modern bathrooms', 'double glazing', 'landscaped garden'],
    ['bright reception rooms', 'utility room', 'patio area'],
]

BER_RATINGS = ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3', 'D1', 'D2', 'E1']


def get_all_areas():
    """Combine all area dictionaries"""
    all_areas = {}
    all_areas.update(DUBLIN_AREAS)
    all_areas.update(CORK_AREAS)
    all_areas.update(GALWAY_AREAS)
    all_areas.update(OTHER_AREAS)
    return all_areas


def determine_county(area):
    """Determine county from area name"""
    if 'Dublin' in area or area in DUBLIN_AREAS:
        return 'Dublin'
    elif area in CORK_AREAS or 'Cork' in area:
        return 'Cork'
    elif area in GALWAY_AREAS or 'Galway' in area:
        return 'Galway'
    elif 'Limerick' in area:
        return 'Limerick'
    elif 'Waterford' in area:
        return 'Waterford'
    elif 'Kilkenny' in area:
        return 'Kilkenny'
    elif area in ['Drogheda', 'Dundalk']:
        return 'Louth'
    elif area == 'Sligo':
        return 'Sligo'
    elif area == 'Tralee':
        return 'Kerry'
    elif area == 'Athlone':
        return 'Westmeath'
    elif area == 'Ennis':
        return 'Clare'
    elif area == 'Navan':
        return 'Meath'
    elif area in ['Maynooth', 'Celbridge', 'Naas']:
        return 'Kildare'
    elif area == 'Portlaoise':
        return 'Laois'
    else:
        return 'Dublin'


def generate_address(area):
    """Generate realistic Irish address"""
    use_estate = random.random() < 0.6  # 60% in estates
    
    if use_estate:
        number = random.randint(1, 250)
        estate = random.choice(ESTATE_NAMES)
        address = f"{number} {estate}, {area}"
    else:
        number = random.randint(1, 150)
        street = random.choice(STREET_NAMES)
        address = f"{number} {street}, {area}"
    
    return address


def generate_description(bedrooms, property_type, area):
    """Generate property description"""
    template = random.choice(DESCRIPTION_TEMPLATES)
    features = ', '.join(random.choice(FEATURES))
    
    return template.format(
        bedrooms=bedrooms,
        property_type=property_type.lower(),
        area=area,
        features=features
    )


def get_location_near(reference_lat, reference_lon, max_distance_km=5):
    """
    Generate coordinates near a reference point
    
    Args:
        reference_lat: Reference latitude
        reference_lon: Reference longitude
        max_distance_km: Maximum distance from reference (km)
    
    Returns:
        tuple: (latitude, longitude)
    """
    # Rough conversion: 1 degree lat/lon ≈ 111 km
    km_per_degree = 111.0
    
    # Random offset in km
    offset_km = random.uniform(0, max_distance_km)
    angle = random.uniform(0, 360)
    
    import math
    offset_lat = offset_km * math.cos(math.radians(angle)) / km_per_degree
    offset_lon = offset_km * math.sin(math.radians(angle)) / (km_per_degree * math.cos(math.radians(reference_lat)))
    
    return (
        reference_lat + offset_lat,
        reference_lon + offset_lon
    )


def generate_property(area, price_range):
    """Generate single property"""
    # Determine property type and size
    property_type = random.choice(PROPERTY_TYPES)
    
    # Bedrooms based on property type
    if property_type == 'Apartment':
        bedrooms = random.choices([1, 2, 3], weights=[3, 5, 2])[0]
    elif property_type == 'Bungalow':
        bedrooms = random.choices([2, 3, 4], weights=[2, 5, 3])[0]
    else:
        bedrooms = random.choices([2, 3, 4, 5], weights=[1, 4, 4, 1])[0]
    
    # Bathrooms
    if bedrooms <= 2:
        bathrooms = 1
    elif bedrooms == 3:
        bathrooms = random.choice([1, 2])
    else:
        bathrooms = random.choice([2, 3])
    
    # Price (influenced by bedrooms)
    base_price = random.uniform(price_range[0], price_range[1]) * 1000
    bedroom_multiplier = 1 + ((bedrooms - 2) * 0.15)
    price = base_price * bedroom_multiplier
    
    # Round to nearest 5k
    price = round(price / 5000) * 5000
    
    # Size in sqm
    if property_type == 'Apartment':
        size_sqm = random.randint(50, 120)
    elif property_type == 'Bungalow':
        size_sqm = random.randint(90, 180)
    else:
        size_sqm = random.randint(80, 200)
    
    # Generate address
    address = generate_address(area)
    county = determine_county(area)
    
    # Generate description
    description = generate_description(bedrooms, property_type, area)
    
    # BER rating
    ber_rating = random.choice(BER_RATINGS)
    
    # Generate property URL
    prop_id = f"sample_{random.randint(100000, 999999)}"
    url = f"https://www.property.ie/sample/{prop_id}/"
    
    return {
        'external_id': prop_id,
        'source': 'sample_data',
        'title': f"{address}",
        'description': description,
        'price': price,
        'address': address,
        'county': county,
        'city': area,
        'bedrooms': bedrooms,
        'bathrooms': bathrooms,
        'property_type': property_type,
        'size_sqm': size_sqm,
        'ber_rating': ber_rating,
        'url': url,
    }


def add_geocoding(properties, app_context):
    """Add latitude/longitude using nearby schools/stations"""
    with app_context:
        # Get some reference locations from schools and stations
        schools = School.query.filter(
            School.latitude.isnot(None),
            School.longitude.isnot(None)
        ).limit(500).all()
        
        stations = TransportStation.query.filter(
            TransportStation.latitude.isnot(None),
            TransportStation.longitude.isnot(None)
        ).all()
        
        reference_points = []
        
        # Add school locations
        for school in schools:
            reference_points.append({
                'lat': school.latitude,
                'lon': school.longitude,
                'county': school.county,
            })
        
        # Add station locations
        for station in stations:
            reference_points.append({
                'lat': station.latitude,
                'lon': station.longitude,
                'county': None,
            })
        
        print(f"Using {len(reference_points)} reference points for geocoding")
        
        # Assign coordinates to properties
        for prop in properties:
            # Find reference points in same county or nearby
            county_refs = [r for r in reference_points if r['county'] == prop['county']]
            
            if county_refs:
                ref = random.choice(county_refs)
            elif reference_points:
                ref = random.choice(reference_points)
            else:
                # Fallback to Dublin center
                ref = {'lat': 53.349805, 'lon': -6.26031}
            
            # Generate nearby coordinates (within 5km)
            lat, lon = get_location_near(ref['lat'], ref['lon'], max_distance_km=5)
            
            prop['latitude'] = lat
            prop['longitude'] = lon


def generate_sample_properties(count=100):
    """
    Generate sample properties
    
    Args:
        count: Number of properties to generate
    """
    print("="*80)
    print(f"SAMPLE PROPERTY GENERATOR")
    print("="*80)
    print(f"Generating {count} sample properties...")
    print()
    
    all_areas = get_all_areas()
    properties = []
    
    # Generate properties
    for i in range(count):
        area = random.choice(list(all_areas.keys()))
        price_range = all_areas[area]
        
        prop_data = generate_property(area, price_range)
        properties.append(prop_data)
    
    print(f"✅ Generated {len(properties)} properties")
    
    # Add geocoding
    print("\nAdding geolocation data...")
    add_geocoding(properties, app.app_context())
    
    # Save to database
    print("\nSaving to database...")
    with app.app_context():
        new_count = 0
        
        for prop_data in properties:
            # Check if exists
            existing = Property.query.filter_by(
                external_id=prop_data['external_id']
            ).first()
            
            if not existing:
                prop = Property(**prop_data)
                db.session.add(prop)
                new_count += 1
        
        db.session.commit()
        
        print(f"✅ Saved {new_count} new properties")
        
        # Summary
        total_props = Property.query.count()
        with_coords = Property.query.filter(
            Property.latitude.isnot(None),
            Property.longitude.isnot(None)
        ).count()
        
        # Price stats
        avg_price = db.session.query(db.func.avg(Property.price)).scalar()
        min_price = db.session.query(db.func.min(Property.price)).scalar()
        max_price = db.session.query(db.func.max(Property.price)).scalar()
        
        print()
        print("="*80)
        print("DATABASE SUMMARY")
        print("="*80)
        print(f"Total properties: {total_props:,}")
        print(f"With coordinates: {with_coords:,} ({with_coords/total_props*100:.1f}%)")
        print()
        print(f"Price range: €{min_price:,.0f} - €{max_price:,.0f}")
        print(f"Average price: €{avg_price:,.0f}")
        print("="*80)


def main():
    """Main function with command-line options"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate sample property data')
    parser.add_argument('--count', type=int, default=100,
                       help='Number of properties to generate (default: 100)')
    
    args = parser.parse_args()
    
    generate_sample_properties(count=args.count)


if __name__ == '__main__':
    main()
