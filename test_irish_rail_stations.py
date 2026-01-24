"""Test Irish Rail API to get all stations with coordinates"""
import requests
import xml.etree.ElementTree as ET

print("="*80)
print("TESTING IRISH RAIL - Get All Stations with Coordinates")
print("="*80)

url = "http://api.irishrail.ie/realtime/realtime.asmx/getAllStationsXML"

try:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    
    print(f"\n✅ API Response received ({len(response.content)} bytes)")
    print(f"Content Type: {response.headers.get('content-type')}")
    
    # Parse XML
    root = ET.fromstring(response.content)
    
    # Find all station objects
    stations = []
    
    # Handle XML namespace
    namespace = {'ir': 'http://api.irishrail.ie/realtime/'}
    
    # Try with namespace first
    for station in root.findall('.//ir:objStation', namespace):
        station_data = {}
        for child in station:
            # Remove namespace from tag
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            station_data[tag] = child.text
        stations.append(station_data)
    
    # If that didn't work, try without namespace
    if not stations:
        for station in root.findall('.//{http://api.irishrail.ie/realtime/}objStation'):
            station_data = {}
            for child in station:
                tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                station_data[tag] = child.text
            stations.append(station_data)
    
    print(f"\n✅ Found {len(stations)} stations")
    
    if stations:
        print("\n" + "="*80)
        print("SAMPLE STATIONS (First 10)")
        print("="*80)
        
        for i, station in enumerate(stations[:10], 1):
            name = station.get('StationDesc', 'Unknown')
            code = station.get('StationCode', 'N/A')
            lat = station.get('StationLatitude', 'N/A')
            lon = station.get('StationLongitude', 'N/A')
            
            print(f"\n{i}. {name}")
            print(f"   Code: {code}")
            print(f"   Coordinates: {lat}, {lon}")
        
        print("\n" + "="*80)
        print("STATISTICS")
        print("="*80)
        
        # Count how many have coordinates
        with_coords = sum(1 for s in stations if s.get('StationLatitude') and s.get('StationLongitude'))
        print(f"Total Stations: {len(stations)}")
        print(f"With Coordinates: {with_coords}")
        print(f"Missing Coordinates: {len(stations) - with_coords}")
        
        # Show a few different station types
        dublin_stations = [s for s in stations if 'Dublin' in s.get('StationDesc', '')]
        print(f"\nDublin Stations: {len(dublin_stations)}")
        
        cork_stations = [s for s in stations if 'Cork' in s.get('StationDesc', '')]
        print(f"Cork Stations: {len(cork_stations)}")
        
        print("\n✅ SUCCESS! Irish Rail API is working perfectly!")
        print("   We can use this to load all train stations into the database.")
        
    else:
        print("\n⚠️  WARNING: No stations found in XML response")
        print("   First 500 chars of response:")
        print(response.text[:500])

except ET.ParseError as e:
    print(f"\n❌ XML Parse Error: {e}")
    print(f"   First 500 chars of response:")
    print(response.text[:500] if 'response' in locals() else "No response")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
