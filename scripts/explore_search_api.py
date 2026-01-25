"""Explore the MyHome.ie search API endpoint"""
import sys
import os
import json
from pathlib import Path
import requests
import uuid
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment
load_dotenv(project_root / '.env')

MYHOME_API_KEY = os.getenv('MYHOME_API_KEY')
MYHOME_API_BASE = 'https://api.myhome.ie'


def search_properties(property_class_id=1, page=1, page_size=50, **filters):
    """
    Search for properties using the /search endpoint
    
    PropertyClassId:
        1 = Residential for Sale
        2 = Residential to Rent
        3 = Commercial
    """
    endpoint = f"{MYHOME_API_BASE}/search"
    
    params = {
        'ApiKey': MYHOME_API_KEY,
        'CorrelationId': str(uuid.uuid4()),
        'PropertyClassId': property_class_id,
        'Page': page,
        'PageSize': page_size
    }
    
    # Add additional filters
    params.update(filters)
    
    try:
        response = requests.get(endpoint, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None


if __name__ == '__main__':
    print("\n" + "="*70)
    print("MyHome.ie Search API Explorer")
    print("="*70)
    
    # Test 1: Residential for sale (default search)
    print("\n[Test 1] Residential properties for sale (page 1, 50 results)")
    print("-" * 70)
    
    data = search_properties(property_class_id=1, page_size=50)
    if data:
        results = data.get('SearchResults', [])
        print(f"✓ Found {len(results)} properties\n")
        
        # Show first 15
        for i, prop in enumerate(results[:15], 1):
            prop_id = prop.get('PropertyId')
            address = prop.get('DisplayAddress', 'N/A')
            price = prop.get('Price', {})
            min_price = price.get('MinPrice', 0)
            bedrooms = prop.get('Bedrooms', 'N/A')
            
            print(f"{i:2}. [{prop_id}] €{min_price:,.0f} - {bedrooms}bed - {address}")
        
        if len(results) > 15:
            print(f"\n... and {len(results) - 15} more properties")
        
        # Check pagination
        total_results = data.get('Request', {}).get('TotalResults', len(results))
        print(f"\nTotal available: {total_results} properties")
        print(f"Page size: 50")
        print(f"Estimated pages: {(total_results // 50) + 1}")
    
    # Test 2: Check available filters
    print("\n" + "="*70)
    print("[Test 2] Available search parameters:")
    print("="*70)
    
    if data:
        request_data = data.get('Request', {}).get('SearchRequest', {})
        print("\nSupported filters:")
        print(f"  - PropertyClassIds: {request_data.get('PropertyClassIds')}")
        print(f"  - RegionId: {request_data.get('RegionId')} (Ireland)")
        print(f"  - MinPrice / MaxPrice")
        print(f"  - MinBeds / MaxBeds")
        print(f"  - PropertyTypeIds (list)")
        print(f"  - LocalityIds (list)")
        print(f"  - EnergyRatings (list)")
        print(f"  - Page / PageSize")
