"""Test script to inspect ArcGIS service capabilities"""
import requests
import json

# Try different potential endpoints
endpoints = [
    "https://services-eu1.arcgis.com/HkXiH6hCLlYq7qYC/arcgis/rest/services/Schools_Map/FeatureServer/0",
    "https://services-eu1.arcgis.com/HkXiH6hCLlYq7qYC/ArcGIS/rest/services/Schools_Map/FeatureServer/0",
    "https://www.education.ie/en/Publications/Statistics/Data-Hub/arcgis/rest/services/Schools_Map/FeatureServer/0",
]

for base_url in endpoints:
    print("\n" + "="*80)
    print(f"TESTING: {base_url}")
    print("="*80)
    
    try:
        # Try to get service info
        response = requests.get(base_url, params={'f': 'json'}, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'error' in data:
                print(f"❌ Error: {data['error']}")
            else:
                print(f"✅ Service found!")
                print(f"   Name: {data.get('name', 'N/A')}")
                print(f"   Type: {data.get('type', 'N/A')}")
                
                # Try query
                query_url = base_url + "/query"
                params = {
                    'where': '1=1',
                    'returnGeometry': 'false',
                    'outFields': '*',
                    'f': 'json',
                    'resultRecordCount': 1
                }
                
                query_response = requests.get(query_url, params=params, timeout=10)
                query_data = query_response.json()
                
                if 'features' in query_data:
                    print(f"   ✅ Query works! Got {len(query_data['features'])} records")
                    if query_data['features']:
                        print(f"   Sample fields: {list(query_data['features'][0].get('attributes', {}).keys())[:5]}")
                elif 'error' in query_data:
                    print(f"   ❌ Query failed: {query_data['error']}")
        else:
            print(f"❌ HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")

# Also try data.gov.ie
print("\n" + "="*80)
print("CHECKING data.gov.ie for schools dataset")
print("="*80)
print("Searching for alternative data sources...")
print("Note: data.gov.ie may have CSV/JSON downloads instead of API")
