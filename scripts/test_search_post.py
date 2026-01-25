"""Test MyHome.ie search API with POST method"""
import os
import json
import requests
import uuid
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

MYHOME_API_KEY = os.getenv('MYHOME_API_KEY')

# Try POST with JSON body (like the browser does)
url = "https://api.myhome.ie/search"

# Build search request matching their API structure
search_request = {
    "SearchRequest": {
        "PropertyClassIds": [1],  # Residential for sale
        "RegionId": 2168,  # Ireland
        "IsActive": True
    },
    "Page": 1,
    "PageSize": 50,
    "ApiKey": MYHOME_API_KEY,
    "CorrelationId": str(uuid.uuid4())
}

try:
    print("Sending POST request to /search...")
    response = requests.post(url, json=search_request, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    results = data.get('SearchResults', [])
    
    print(f"\n✓ Found {len(results)} properties\n")
    
    for i, prop in enumerate(results[:15], 1):
        prop_id = prop.get('PropertyId')
        address = prop.get('DisplayAddress', 'N/A')
        price_obj = prop.get('Price', {})
        min_price = price_obj.get('MinPrice', 0) if price_obj else 0
        bedrooms = prop.get('Bedrooms', 'N/A')
        
        print(f"{i:2}. [{prop_id}] €{min_price:,.0f} - {bedrooms}bed - {address}")
    
    if len(results) > 15:
        print(f"\n... and {len(results) - 15} more")
    
    print(f"\nTotal results: {len(results)}")
    
except Exception as e:
    print(f"Error: {e}")
    print(f"Response: {response.text[:500] if 'response' in locals() else 'N/A'}")
