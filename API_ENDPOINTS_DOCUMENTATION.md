# Ireland Data API Endpoints - Complete Documentation

## 📊 Overview

This document contains all working API endpoints and data sources for the Find Me a Home application, with geolocation data (latitude/longitude) for calculating distances from properties.

---

## 🏫 Schools Data

### **Department of Education - Post Primary Schools CSV**
**✅ RECOMMENDED - Has Full Geolocation Data**

- **Download URL**: `https://www.education.ie/en/Publications/Statistics/Data-on-Individual-Schools/Education-UT-post_primaryEducation-IE-DepartmentofEducationAndSkills-Post-PrimarySchoolsLocations2016-2017_080617.csv`
- **Data.gov.ie Page**: https://data.gov.ie/dataset/post-primary-schools-list-2017
- **Format**: CSV
- **Update Frequency**: Annual
- **License**: Creative Commons Attribution 4.0

**Data Includes**:
- School Name
- Roll Number
- Address
- **Latitude & Longitude** ✅
- **Eircode** (Irish postal code)
- Contact Details

**Note**: This is for POST-PRIMARY schools (secondary/high schools) from 2016/2017. You may want to find a similar dataset for PRIMARY schools.

**How to Use**:
1. Download the CSV file
2. Parse it in Python using pandas
3. Calculate distance from each property using the Haversine formula
4. Filter schools within desired radius (e.g., 5km)

**Alternative**: Look for primary schools at https://www.education.ie/en/find-a-school

---

## 🚂 Irish Rail Stations & Real-time Data

### **Irish Rail API - Station List**
**✅ WORKING - Has Full Geolocation Data**

- **Base URL**: `http://api.irishrail.ie/realtime/realtime.asmx/`
- **Documentation**: http://api.irishrail.ie/realtime/
- **Format**: XML
- **Authentication**: None required ✅
- **Rate Limits**: None specified

### **Key Endpoints**:

#### 1. Get All Stations (with coordinates)
```
GET http://api.irishrail.ie/realtime/realtime.asmx/getAllStationsXML
```

**Returns**:
- StationDesc (name)
- StationCode (unique identifier)
- StationId
- StationAlias
- **StationLatitude** ✅
- **StationLongitude** ✅

**Ordered by**: Latitude, Longitude

#### 2. Get Stations by Type
```
GET http://api.irishrail.ie/realtime/realtime.asmx/getAllStationsXML_WithStationType?StationType=A
```

**StationType values**:
- `A` = All stations
- `M` = Mainline only
- `S` = Suburban only
- `D` = DART only

#### 3. Get Current Trains (Real-time)
```
GET http://api.irishrail.ie/realtime/realtime.asmx/getCurrentTrainsXML
```

**Returns**:
- TrainStatus (N=not running, R=running)
- **TrainLatitude** ✅
- **TrainLongitude** ✅
- TrainCode
- TrainDate
- PublicMessage
- Direction

**Use Case**: Show live train positions on map

#### 4. Get Station Schedule
```
GET http://api.irishrail.ie/realtime/realtime.asmx/getStationDataByNameXML?StationDesc={station_name}
GET http://api.irishrail.ie/realtime/realtime.asmx/getStationDataByCodeXML?StationCode={code}
```

**Returns**: All trains due at station in next 90 minutes

**Why Previous Tests Failed**: Our code didn't parse the XML correctly. The API works perfectly.

---

## 🚌 Bus Routes & Stops (Dublin Bus, Bus Éireann, LUAS)

### **Transport for Ireland - GTFS Data**
**✅ RECOMMENDED - Standard GTFS Format with Geolocation**

- **Data Portal**: https://www.transportforireland.ie/transitData/
- **Alternative**: https://data.gov.ie/ (search for "GTFS")
- **Format**: GTFS (General Transit Feed Specification)
- **Authentication**: May require API key from data.gov.ie
- **License**: Open Data

**GTFS Includes**:
- `stops.txt` - All bus/LUAS stops with **latitude & longitude** ✅
- `routes.txt` - All bus/LUAS routes
- `trips.txt` - Individual trip schedules
- `stop_times.txt` - When each trip arrives at each stop
- `shapes.txt` - Geographic route paths

**How to Use**:
1. Download GTFS ZIP file
2. Extract `stops.txt` file
3. Parse CSV to get all stops with lat/lon
4. Calculate distance from property
5. Use `stop_times.txt` to show frequency of service

**Bus Operators Covered**:
- Dublin Bus
- Bus Éireann (national)
- Go-Ahead Ireland
- LUAS (tram)
- Commuter rail

### **GTFS Real-time API**
```
GET https://api.nationaltransport.ie/gtfsr/v1/
```
**Requires**: API key from https://data.gov.ie/
**Returns**: Real-time vehicle positions and arrival predictions

---

## 🏘️ Towns & Villages

### **CSO Census - Settlements with Population**
**✅ AVAILABLE - Census Geographic Data**

- **Portal**: https://www.cso.ie/en/census/
- **Datasets**: 
  - Census 2022 Small Area Population Statistics
  - Census 2022 Urban Boundaries and Built Up Areas
- **Format**: Shapefiles, GeoJSON, CSV
- **License**: Open Data

**Data Includes**:
- Town/village name
- Population
- Geographic boundaries
- **Coordinates** (centroid) ✅

**Download**: https://www.cso.ie/en/census/census2022/census2022urbanboundariesandbuiltupareas/

### **Tailte Éireann (Ordnance Survey Ireland)**
**✅ RECOMMENDED - Official Geographic Data**

- **Portal**: https://data.gov.ie/organization/tailte-eireann
- **Search**: "settlements", "placenames", "towns"
- **Format**: Multiple (GeoJSON, Shapefile, CSV)
- **License**: Open Data

**Useful Datasets**:
- Built Up Areas with coordinates
- Settlement Points with population
- Placenames database

---

## 📍 Calculating Distances

### **Geolocation Distance Calculation**

All the above datasets include **latitude and longitude**, so you can:

1. **Calculate straight-line distance** (as the crow flies):
   - Use Haversine formula
   - Python: `from geopy.distance import geodesic`

2. **Calculate driving distance** (actual road routes):
   - **Option 1**: OpenStreetMap Routing (FREE)
     - API: https://router.project-osm.org/
     - Library: OSRM Python client
   
   - **Option 2**: Google Maps Distance Matrix API
     - URL: https://developers.google.com/maps/documentation/distance-matrix
     - **Cost**: First $200/month free, then pay-per-use
     - Requires API key
   
   - **Option 3**: Mapbox Directions API
     - URL: https://docs.mapbox.com/api/navigation/directions/
     - **Cost**: 100,000 requests/month free
     - Requires API key

### **Example: Schools within 5km of Property**

```python
from geopy.distance import geodesic

property_location = (53.3498, -6.2603)  # Dublin lat/lon

for school in schools_data:
    school_location = (school['latitude'], school['longitude'])
    distance_km = geodesic(property_location, school_location).kilometers
    
    if distance_km <= 5.0:
        print(f"{school['name']}: {distance_km:.2f}km away")
```

---

## 🔄 Data Update Strategy

### **Schools**
- **Update Frequency**: Annually (September)
- **Strategy**: Download new CSV each academic year
- **Source**: Monitor https://data.gov.ie/organization/department-of-education

### **Train Stations**
- **Update Frequency**: Rare (infrastructure changes)
- **Strategy**: Cache station list, update quarterly
- **Source**: Irish Rail API endpoint 1

### **Bus Stops**
- **Update Frequency**: Monthly (routes change)
- **Strategy**: Download new GTFS monthly
- **Source**: Transport for Ireland portal

### **Towns/Settlements**
- **Update Frequency**: Every 5 years (census)
- **Strategy**: Download after each census
- **Source**: CSO Census portal

---

## 📝 Implementation Priority

### **Phase 1: Essential (Implement Now)**
1. ✅ Irish Rail Stations API - Get all stations with coordinates
2. ✅ Schools CSV Download - Post-primary schools with coordinates
3. ✅ Distance calculations - Haversine formula for straight-line distance

### **Phase 2: Enhanced Features**
4. ⏳ GTFS Bus Data - Download and parse stops.txt
5. ⏳ CSO Towns Data - Census settlements with population
6. ⏳ OpenStreetMap Routing - Driving distances (FREE!)

### **Phase 3: Advanced (Optional)**
7. ⏺️ GTFS Real-time - Live bus/LUAS arrivals
8. ⏺️ Google Maps Distance Matrix - Accurate driving times (PAID)
9. ⏺️ Primary schools dataset - Find equivalent to post-primary CSV

---

## 🛠️ Next Steps

1. **Fix Irish Rail XML parsing** in transport_service.py
   - The API works, we just need to parse the XML correctly
   - Use `xml.etree.ElementTree` or `lxml`

2. **Download Schools CSV** and create import script
   - URL in this document
   - Create `scripts/load_schools_from_csv.py`

3. **Test distance calculations**
   - Install `geopy`: `pip install geopy`
   - Add distance calculation to search filters

4. **Add GTFS bus data** (optional but recommended)
   - Download GTFS ZIP
   - Parse `stops.txt` for bus stop locations

---

## 📞 Support & Documentation

- **Irish Rail API**: http://api.irishrail.ie/realtime/
- **Data.gov.ie**: https://data.gov.ie/
- **Transport for Ireland**: https://www.transportforireland.ie/
- **CSO Census**: https://www.cso.ie/en/census/
- **Department of Education**: https://www.education.ie/en/find-a-school

---

**Last Updated**: January 24, 2026
**Maintained By**: Find Me a Home Development Team
