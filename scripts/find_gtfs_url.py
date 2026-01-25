"""Find NTA GTFS static data download URL"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

NTA_API_KEY = os.getenv('NTA_API_KEY')

# Common GTFS static endpoints to try
urls_to_try = [
    "https://api.nationaltransport.ie/gtfs/v2/gtfs_ireland.zip",
    "https://api.nationaltransport.ie/gtfs/gtfs_ireland.zip",
    "https://www.transportforireland.ie/transitData/Data/GTFS_All.zip",
    "https://api.nationaltransport.ie/gtfs/v1/gtfs_ireland.zip",
]

headers = {
    'Ocp-Apim-Subscription-Key': NTA_API_KEY
}

print("Testing NTA GTFS static data endpoints...")
print("="*70)

for url in urls_to_try:
    print(f"\nTrying: {url}")
    try:
        # Try without auth first
        response = requests.head(url, timeout=10, allow_redirects=True)
        if response.status_code == 200:
            print(f"✓ FOUND (no auth needed)!")
            print(f"  Content-Type: {response.headers.get('Content-Type')}")
            print(f"  Content-Length: {int(response.headers.get('Content-Length', 0)) / 1024 / 1024:.1f} MB")
            continue
        
        # Try with API key
        response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
        if response.status_code == 200:
            print(f"✓ FOUND (requires API key)!")
            print(f"  Content-Type: {response.headers.get('Content-Type')}")
            print(f"  Content-Length: {int(response.headers.get('Content-Length', 0)) / 1024 / 1024:.1f} MB")
        else:
            print(f"✗ Status: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Error: {e}")

print("\n" + "="*70)
print("\nIf none found, please:")
print("1. Visit https://developer.nationaltransport.ie/")
print("2. Look for 'GTFS Static' or 'Download' section")
print("3. Download the GTFS zip file manually")
print("4. Save it to: scripts/gtfs_data.zip")
