#!/usr/bin/env python
"""
Data loading script for Find Me a Home application
Fetches initial data from various APIs and populates the database
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db
from services.school_service import fetch_schools_from_gov
from services.transport_service import fetch_irish_rail_stations

def load_schools():
    """Load school data from government sources"""
    print("Loading school data...")
    try:
        count = fetch_schools_from_gov()
        print(f"✓ Successfully loaded {count} schools")
        return True
    except Exception as e:
        print(f"✗ Error loading schools: {e}")
        return False

def load_transport():
    """Load transport station data"""
    print("Loading transport station data...")
    try:
        count = fetch_irish_rail_stations()
        print(f"✓ Successfully loaded {count} train stations")
        return True
    except Exception as e:
        print(f"✗ Error loading transport stations: {e}")
        return False

def load_sample_properties():
    """Load sample property data for testing"""
    print("Loading sample property data...")
    from models import Property
    
    try:
        # Check if we already have properties
        if Property.query.count() > 0:
            print("Properties already exist in database. Skipping...")
            return True
        
        # Sample properties
        sample_properties = [
            {
                'external_id': 'sample-1',
                'source': 'manual',
                'title': 'Modern 3 Bed Semi-Detached House',
                'description': 'Beautiful modern home in a quiet residential area.',
                'price': 425000,
                'address': '123 Main Street, Swords, County Dublin',
                'county': 'Dublin',
                'city': 'Swords',
                'latitude': 53.4597,
                'longitude': -6.2182,
                'bedrooms': 3,
                'bathrooms': 2,
                'property_type': 'house',
                'size_sqm': 120,
                'ber_rating': 'B2',
                'url': 'https://example.com/property/1'
            },
            {
                'external_id': 'sample-2',
                'source': 'manual',
                'title': 'Spacious 2 Bed Apartment in City Centre',
                'description': 'Modern apartment with great amenities.',
                'price': 350000,
                'address': '45 George\'s Street, Dublin 2, County Dublin',
                'county': 'Dublin',
                'city': 'Dublin',
                'latitude': 53.3425,
                'longitude': -6.2658,
                'bedrooms': 2,
                'bathrooms': 1,
                'property_type': 'apartment',
                'size_sqm': 85,
                'ber_rating': 'A3',
                'url': 'https://example.com/property/2'
            },
            {
                'external_id': 'sample-3',
                'source': 'manual',
                'title': '4 Bed Detached House with Garden',
                'description': 'Family home with large garden and parking.',
                'price': 595000,
                'address': '78 Oak Drive, Malahide, County Dublin',
                'county': 'Dublin',
                'city': 'Malahide',
                'latitude': 53.4512,
                'longitude': -6.1543,
                'bedrooms': 4,
                'bathrooms': 3,
                'property_type': 'house',
                'size_sqm': 180,
                'ber_rating': 'B1',
                'url': 'https://example.com/property/3'
            }
        ]
        
        for prop_data in sample_properties:
            prop = Property(**prop_data)
            db.session.add(prop)
        
        db.session.commit()
        print(f"✓ Successfully loaded {len(sample_properties)} sample properties")
        return True
        
    except Exception as e:
        print(f"✗ Error loading sample properties: {e}")
        db.session.rollback()
        return False

def main():
    """Main data loading function"""
    print("=" * 60)
    print("Find Me a Home - Data Loading Script")
    print("=" * 60)
    print()
    
    with app.app_context():
        # Ensure tables exist
        print("Creating database tables if they don't exist...")
        db.create_all()
        print("✓ Database tables ready")
        print()
        
        # Load data
        results = []
        
        results.append(("Schools", load_schools()))
        print()
        
        results.append(("Transport Stations", load_transport()))
        print()
        
        results.append(("Sample Properties", load_sample_properties()))
        print()
        
        # Summary
        print("=" * 60)
        print("Loading Summary:")
        print("-" * 60)
        for name, success in results:
            status = "✓ SUCCESS" if success else "✗ FAILED"
            print(f"{name}: {status}")
        print("=" * 60)
        
        all_success = all(success for _, success in results)
        if all_success:
            print("\n🎉 All data loaded successfully!")
        else:
            print("\n⚠️  Some data loading operations failed. Check errors above.")
        
        return 0 if all_success else 1

if __name__ == '__main__':
    sys.exit(main())
