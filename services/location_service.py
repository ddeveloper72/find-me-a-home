from models import School, TransportStation, Property
import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    Returns distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r

def find_nearby_schools(latitude, longitude, max_distance_km=5):
    """
    Find schools within a certain distance of a location
    """
    # Get all schools with coordinates
    schools = School.query.filter(
        School.latitude.isnot(None),
        School.longitude.isnot(None)
    ).all()
    
    nearby_schools = []
    
    for school in schools:
        distance = haversine_distance(
            latitude, longitude,
            school.latitude, school.longitude
        )
        
        if distance <= max_distance_km:
            # Add distance as an attribute for sorting/display
            school.distance = round(distance, 2)
            nearby_schools.append(school)
    
    # Sort by distance
    nearby_schools.sort(key=lambda x: x.distance)
    
    return nearby_schools

def find_nearby_transport(latitude, longitude, max_distance_km=2):
    """
    Find transport stations within a certain distance of a location
    """
    # Get all stations with coordinates
    stations = TransportStation.query.filter(
        TransportStation.latitude.isnot(None),
        TransportStation.longitude.isnot(None)
    ).all()
    
    nearby_stations = []
    
    for station in stations:
        distance = haversine_distance(
            latitude, longitude,
            station.latitude, station.longitude
        )
        
        if distance <= max_distance_km:
            # Add distance as an attribute for sorting/display
            station.distance = round(distance, 2)
            nearby_stations.append(station)
    
    # Sort by distance
    nearby_stations.sort(key=lambda x: x.distance)
    
    return nearby_stations

def find_properties_near_location(latitude, longitude, max_distance_km=5):
    """
    Find properties within a certain distance of a location
    """
    # Get all properties with coordinates
    properties = Property.query.filter(
        Property.latitude.isnot(None),
        Property.longitude.isnot(None)
    ).all()
    
    nearby_properties = []
    
    for prop in properties:
        distance = haversine_distance(
            latitude, longitude,
            prop.latitude, prop.longitude
        )
        
        if distance <= max_distance_km:
            prop.distance = round(distance, 2)
            nearby_properties.append(prop)
    
    # Sort by distance
    nearby_properties.sort(key=lambda x: x.distance)
    
    return nearby_properties
