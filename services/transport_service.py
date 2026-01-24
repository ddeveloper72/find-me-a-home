import requests
from models import TransportStation
from extensions import db
import xml.etree.ElementTree as ET

def fetch_irish_rail_stations():
    """
    Fetch all Irish Rail stations from the API
    Returns the number of new stations added
    """
    url = "http://api.irishrail.ie/realtime/realtime.asmx/getAllStationsXML"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        stations = []
        
        # Handle XML namespace
        namespace = {'ir': 'http://api.irishrail.ie/realtime/'}
        
        # Find all station objects with namespace
        station_elements = root.findall('.//ir:objStation', namespace)
        
        # If namespace approach didn't work, try direct namespace in tag
        if not station_elements:
            station_elements = root.findall('.//{http://api.irishrail.ie/realtime/}objStation')
        
        for station in station_elements:
            # Extract data with namespace handling
            def get_text(tag_name):
                elem = station.find(f'ir:{tag_name}', namespace)
                if elem is None:
                    elem = station.find(f'{{{namespace["ir"]}}}{tag_name}')
                return elem.text if elem is not None and elem.text else None
            
            external_id = get_text('StationCode')
            name = get_text('StationDesc')
            lat_text = get_text('StationLatitude')
            lon_text = get_text('StationLongitude')
            
            # Convert coordinates to float
            try:
                latitude = float(lat_text) if lat_text else None
                longitude = float(lon_text) if lon_text else None
            except (ValueError, TypeError):
                latitude = None
                longitude = None
            
            if external_id and name:
                # Check if station already exists
                existing = TransportStation.query.filter_by(
                    external_id=external_id,
                    station_type='train'
                ).first()
                
                if not existing:
                    transport_station = TransportStation(
                        external_id=external_id,
                        name=name,
                        station_type='train',
                        latitude=latitude,
                        longitude=longitude
                    )
                    stations.append(transport_station)
        
        if stations:
            db.session.add_all(stations)
            db.session.commit()
            print(f"✅ Added {len(stations)} new Irish Rail stations to database")
        
        return len(stations)
        
    except Exception as e:
        print(f"❌ Error fetching Irish Rail stations: {e}")
        import traceback
        traceback.print_exc()
        return 0

def fetch_gtfs_realtime_data():
    """
    Fetch realtime passenger information from GTFS-R feed
    """
    url = "https://api.nationaltransport.ie/gtfsr/v2/gtfsr"
    
    # Note: This API requires authentication
    # You'll need to register at https://data.gov.ie/ to get an API key
    
    # TODO: Implement GTFS-R parsing
    # This requires the gtfs-realtime-bindings library
    pass

def get_realtime_info(station):
    """
    Get realtime arrival/departure information for a station
    """
    if station.station_type == 'train':
        return get_irish_rail_realtime(station.external_id)
    else:
        # TODO: Implement for buses, LUAS, etc.
        return []

def get_irish_rail_realtime(station_code):
    """
    Get realtime train information for an Irish Rail station
    """
    url = f"http://api.irishrail.ie/realtime/realtime.asmx/getStationDataByCodeXML"
    params = {'StationCode': station_code}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        trains = []
        
        # Handle XML namespace
        namespace = {'ir': 'http://api.irishrail.ie/realtime/'}
        
        # Find all train objects with namespace
        train_elements = root.findall('.//ir:objStationData', namespace)
        
        # If namespace approach didn't work, try direct namespace
        if not train_elements:
            train_elements = root.findall('.//{http://api.irishrail.ie/realtime/}objStationData')
        
        for train in train_elements:
            # Extract data with namespace handling
            def get_text(tag_name):
                elem = train.find(f'ir:{tag_name}', namespace)
                if elem is None:
                    elem = train.find(f'{{{namespace["ir"]}}}{tag_name}')
                return elem.text if elem is not None and elem.text else None
            
            train_data = {
                'train_code': get_text('Traincode'),
                'origin': get_text('Origin'),
                'destination': get_text('Destination'),
                'expected_arrival': get_text('Exparrival'),
                'expected_departure': get_text('Expdepart'),
                'status': get_text('Status'),
                'due_in': get_text('Duein'),
                'late': get_text('Late'),
            }
            trains.append(train_data)
        
        return trains
        
    except Exception as e:
        print(f"Error fetching realtime info: {e}")
        return []
