"""Test MyHome.ie search API with authenticated session"""
import os
import json
import requests
import uuid
from dotenv import load_dotenv

load_dotenv()

MYHOME_API_KEY = os.getenv('MYHOME_API_KEY')
MYHOME_SESSION_COOKIE = os.getenv('MYHOME_SESSION_COOKIE')

print("="*70)
print("Testing MyHome.ie Search API with Session Cookie")
print("="*70)
print(f"API Key: {MYHOME_API_KEY[:20]}...")
print(f"Session Cookie: {MYHOME_SESSION_COOKIE[:20] if MYHOME_SESSION_COOKIE else 'None'}...")
print()

# Test 1: /home endpoint to verify authentication
print("[Test 1] Checking authentication with /home endpoint...")
url = "https://api.myhome.ie/home"
params = {
    'ApiKey': MYHOME_API_KEY,
    'CorrelationId': str(uuid.uuid4())
}
cookies = {
    'ss-pid': MYHOME_SESSION_COOKIE,
    'ai_session': 'idbeXcQs9wHPPSPn1NM0XT|1769348922619|1769349004485',
    'ai_user': 'KLHOBZY5vuMM2Kh/+8aX8M|2026-01-15T21:43:05.360Z'
} if MYHOME_SESSION_COOKIE else {}

try:
    response = requests.get(url, params=params, cookies=cookies, timeout=30)
    data = response.json()
    user_id = data.get('UserId', 0)
    email = data.get('Email', '')
    
    if user_id:
        print(f"✓ Authenticated as UserId: {user_id}")
        print(f"  Email: {email}")
    else:
        print("✗ Not authenticated")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: Search with authentication
print("\n[Test 2] Searching with authenticated session...")
url = "https://api.myhome.ie/search"

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
    response = requests.post(url, json=search_request, cookies=cookies, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    results = data.get('SearchResults', [])
    
    print(f"✓ Found {len(results)} properties")
    
    if results:
        print("\nFirst 15 properties:")
        print("-" * 70)
        for i, prop in enumerate(results[:15], 1):
            prop_id = prop.get('PropertyId')
            address = prop.get('DisplayAddress', 'N/A')
            price_obj = prop.get('Price', {})
            min_price = price_obj.get('MinPrice', 0) if price_obj else 0
            bedrooms = prop.get('Bedrooms', 'N/A')
            
            print(f"{i:2}. [{prop_id}] €{min_price:,.0f} - {bedrooms}bed - {address}")
        
        if len(results) > 15:
            print(f"\n... and {len(results) - 15} more")
    else:
        print("\nNo results returned - session may not grant search access")
    
except Exception as e:
    print(f"✗ Error: {e}")
    if 'response' in locals():
        print(f"Status: {response.status_code}")

print("\n" + "="*70)
