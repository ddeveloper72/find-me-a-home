#!/usr/bin/env python
"""
API Connectivity Test Script
Tests connections to all external data sources
"""

import requests
import xml.etree.ElementTree as ET

def test_irish_rail_api():
    """Test Irish Rail API"""
    print("\n" + "="*60)
    print("Testing Irish Rail API...")
    print("="*60)
    
    url = "http://api.irishrail.ie/realtime/realtime.asmx/getAllStationsXML"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Parse XML
        root = ET.fromstring(response.content)
        stations = list(root.findall('.//objStation'))
        
        print(f"✅ SUCCESS: Connected to Irish Rail API")
        print(f"   Found {len(stations)} train stations")
        
        if stations:
            # Show first station as example
            first = stations[0]
            name = first.find('StationDesc').text if first.find('StationDesc') is not None else 'Unknown'
            code = first.find('StationCode').text if first.find('StationCode') is not None else 'Unknown'
            print(f"   Example: {name} ({code})")
        
        return True, len(stations)
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False, 0

def test_schools_arcgis_api():
    """Test Department of Education ArcGIS API"""
    print("\n" + "="*60)
    print("Testing Department of Education ArcGIS API...")
    print("="*60)
    
    # Try the main service first to see if it's available
    base_url = "https://services-eu1.arcgis.com/HkXiH6hCLlYq7qYC/arcgis/rest/services/Schools_Map/FeatureServer/0"
    
    try:
        # First check if the service is available
        response = requests.get(base_url + "?f=json", timeout=30)
        response.raise_for_status()
        service_info = response.json()
        
        print(f"✅ Service is available: {service_info.get('name', 'Schools Map')}")
        
        # Now try to query it
        query_url = base_url + "/query"
        params = {
            'where': '1=1',
            'outFields': 'OBJECTID,Official_School_Name,Roll_Number,County',
            'f': 'json',
            'returnGeometry': 'false',
            'resultRecordCount': 5
        }
        
        response = requests.get(query_url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'features' in data and data['features']:
            features = data['features']
            print(f"✅ SUCCESS: Retrieved school data from ArcGIS")
            print(f"   Retrieved {len(features)} school records (test sample)")
            
            # Show first school as example
            if features:
                attrs = features[0].get('attributes', {})
                name = attrs.get('Official_School_Name', 'Unknown')
                roll = attrs.get('Roll_Number', 'Unknown')
                county = attrs.get('County', 'Unknown')
                print(f"   Example: {name}")
                print(f"   Roll Number: {roll}, County: {county}")
            
            return True, len(features)
        elif 'error' in data:
            print(f"❌ FAILED: API returned error")
            print(f"   Error: {data['error']}")
            return False, 0
        else:
            print(f"⚠️  WARNING: Connected but no data returned")
            print(f"   Response keys: {list(data.keys())}")
            return False, 0
            
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, 0

def test_gtfs_realtime_api():
    """Test GTFS-R API for bus/LUAS data"""
    print("\n" + "="*60)
    print("Testing GTFS-R API (Bus/LUAS)...")
    print("="*60)
    
    url = "https://api.nationaltransport.ie/gtfsr/v2/gtfsr"
    
    print("ℹ️  Note: This API requires an authentication key from data.gov.ie")
    
    try:
        # Try without auth (will likely fail, but let's see)
        response = requests.get(url, timeout=10)
        
        if response.status_code == 401:
            print("⚠️  EXPECTED: API requires authentication")
            print("   You need to register at https://data.gov.ie/ to get an API key")
            print("   This is optional and not needed for basic functionality")
            return None, 0
        
        response.raise_for_status()
        print(f"✅ SUCCESS: Connected to GTFS-R API")
        return True, 0
        
    except requests.exceptions.HTTPError as e:
        if '401' in str(e):
            print("⚠️  EXPECTED: API requires authentication")
            print("   You need to register at https://data.gov.ie/ to get an API key")
            print("   This is optional and not needed for basic functionality")
            return None, 0
        else:
            print(f"❌ FAILED: {str(e)}")
            return False, 0
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False, 0

def test_sample_irish_rail_station():
    """Test getting real-time data for a specific station"""
    print("\n" + "="*60)
    print("Testing Irish Rail Real-time Data (Dublin Connolly)...")
    print("="*60)
    
    url = "http://api.irishrail.ie/realtime/realtime.asmx/getStationDataByCodeXML"
    params = {'StationCode': 'CNLLY'}  # Dublin Connolly
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        trains = list(root.findall('.//objStationData'))
        
        print(f"✅ SUCCESS: Retrieved real-time train data")
        print(f"   Found {len(trains)} trains at Dublin Connolly")
        
        if trains and len(trains) > 0:
            # Show first train
            train = trains[0]
            origin = train.find('Origin').text if train.find('Origin') is not None else 'Unknown'
            dest = train.find('Destination').text if train.find('Destination') is not None else 'Unknown'
            exp_arrival = train.find('Exparrival').text if train.find('Exparrival') is not None else 'Unknown'
            print(f"   Example train: {origin} → {dest}")
            print(f"   Expected: {exp_arrival}")
        elif len(trains) == 0:
            print("   (No trains currently scheduled - this is normal)")
        
        return True, len(trains)
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        return False, 0

def main():
    """Run all API tests"""
    print("\n" + "="*60)
    print("🔍 API CONNECTIVITY TEST")
    print("Testing all external data sources...")
    print("="*60)
    
    results = []
    
    # Test Irish Rail API
    success, count = test_irish_rail_api()
    results.append(("Irish Rail API", success, count))
    
    # Test real-time data
    success, count = test_sample_irish_rail_station()
    results.append(("Irish Rail Real-time", success, count))
    
    # Test Schools API
    success, count = test_schools_arcgis_api()
    results.append(("Education ArcGIS API", success, count))
    
    # Test GTFS-R
    success, count = test_gtfs_realtime_api()
    results.append(("GTFS-R API (Bus/LUAS)", success, count))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    for name, success, count in results:
        if success is True:
            status = "✅ WORKING"
        elif success is None:
            status = "⚠️  AUTH REQUIRED"
        else:
            status = "❌ FAILED"
        
        print(f"{status:20} | {name}")
    
    print("="*60)
    
    # Recommendations
    working = sum(1 for _, s, _ in results if s is True)
    
    print("\n💡 RECOMMENDATIONS:")
    if working >= 2:
        print("✅ You have working API connections!")
        print("   - You can load train station data")
        if any(name == "Education ArcGIS API" and success for name, success, _ in results):
            print("   - You can load school data")
        print("\n   Run: python scripts\\load_data.py")
        print("   This will populate your database with real data!")
    else:
        print("⚠️  Limited API connectivity detected")
        print("   - You can still use sample data for development")
        print("   - Check your internet connection")
        print("   - Some APIs may have rate limits or be temporarily down")
    
    print("\n🔑 OPTIONAL:")
    print("   - GTFS-R API key: Register at https://data.gov.ie/")
    print("     (Not needed for basic functionality)")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    main()
