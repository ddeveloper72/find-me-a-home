"""
Location and proximity services
Handles finding nearby amenities (schools, transport) relative to properties
"""

from models import School, TransportStation, Property
from services.distance_service import filter_by_distance, get_nearest, get_bounding_box


def find_nearby_schools(latitude, longitude, max_distance_km=5, limit=None):
    """
    Find schools within a certain distance of a location
    
    Args:
        latitude (float): Center point latitude
        longitude (float): Center point longitude
        max_distance_km (float): Maximum distance in kilometers (default 5km)
        limit (int): Optional limit on number of results
    
    Returns:
        list: Schools within distance, sorted by proximity, with distance_km attribute
    """
    # Use bounding box for efficient database query
    bbox = get_bounding_box(latitude, longitude, max_distance_km)
    
    # Get schools within bounding box
    schools = School.query.filter(
        School.latitude.between(bbox['min_lat'], bbox['max_lat']),
        School.longitude.between(bbox['min_lon'], bbox['max_lon']),
        School.latitude.isnot(None),
        School.longitude.isnot(None)
    ).all()
    
    # Filter by exact distance and sort
    nearby_schools = filter_by_distance(
        schools, 
        latitude, 
        longitude, 
        max_distance_km
    )
    
    if limit:
        return nearby_schools[:limit]
    
    return nearby_schools


def find_nearby_transport(latitude, longitude, max_distance_km=2, station_type=None, limit=None):
    """
    Find transport stations within a certain distance of a location
    
    Args:
        latitude (float): Center point latitude
        longitude (float): Center point longitude
        max_distance_km (float): Maximum distance in kilometers (default 2km)
        station_type (str): Optional filter by station type ('train', 'bus', 'luas')
        limit (int): Optional limit on number of results
    
    Returns:
        list: Stations within distance, sorted by proximity, with distance_km attribute
    """
    # Use bounding box for efficient database query
    bbox = get_bounding_box(latitude, longitude, max_distance_km)
    
    # Build query
    query = TransportStation.query.filter(
        TransportStation.latitude.between(bbox['min_lat'], bbox['max_lat']),
        TransportStation.longitude.between(bbox['min_lon'], bbox['max_lon']),
        TransportStation.latitude.isnot(None),
        TransportStation.longitude.isnot(None)
    )
    
    # Filter by station type if specified
    if station_type:
        query = query.filter(TransportStation.station_type == station_type)
    
    stations = query.all()
    
    # Filter by exact distance and sort
    nearby_stations = filter_by_distance(
        stations, 
        latitude, 
        longitude, 
        max_distance_km
    )
    
    if limit:
        return nearby_stations[:limit]
    
    return nearby_stations


def find_properties_near_location(latitude, longitude, max_distance_km=5, limit=None):
    """
    Find properties within a certain distance of a location
    
    Args:
        latitude (float): Center point latitude
        longitude (float): Center point longitude
        max_distance_km (float): Maximum distance in kilometers (default 5km)
        limit (int): Optional limit on number of results
    
    Returns:
        list: Properties within distance, sorted by proximity, with distance_km attribute
    """
    # Use bounding box for efficient database query
    bbox = get_bounding_box(latitude, longitude, max_distance_km)
    
    # Get properties within bounding box
    properties = Property.query.filter(
        Property.latitude.between(bbox['min_lat'], bbox['max_lat']),
        Property.longitude.between(bbox['min_lon'], bbox['max_lon']),
        Property.latitude.isnot(None),
        Property.longitude.isnot(None)
    ).all()
    
    # Filter by exact distance and sort
    nearby_properties = filter_by_distance(
        properties, 
        latitude, 
        longitude, 
        max_distance_km
    )
    
    if limit:
        return nearby_properties[:limit]
    
    return nearby_properties


def get_nearest_schools(latitude, longitude, limit=5):
    """
    Get the N nearest schools to a location
    
    Args:
        latitude (float): Center point latitude
        longitude (float): Center point longitude
        limit (int): Number of schools to return (default 5)
    
    Returns:
        list: Nearest schools with distance_km attribute
    """
    schools = School.query.filter(
        School.latitude.isnot(None),
        School.longitude.isnot(None)
    ).all()
    
    return get_nearest(schools, latitude, longitude, limit=limit)


def get_nearest_transport(latitude, longitude, station_type=None, limit=5):
    """
    Get the N nearest transport stations to a location
    
    Args:
        latitude (float): Center point latitude
        longitude (float): Center point longitude
        station_type (str): Optional filter by station type
        limit (int): Number of stations to return (default 5)
    
    Returns:
        list: Nearest stations with distance_km attribute
    """
    query = TransportStation.query.filter(
        TransportStation.latitude.isnot(None),
        TransportStation.longitude.isnot(None)
    )
    
    if station_type:
        query = query.filter(TransportStation.station_type == station_type)
    
    stations = query.all()
    
    return get_nearest(stations, latitude, longitude, limit=limit)


def enrich_property_with_nearby_amenities(property_obj, school_distance_km=5, transport_distance_km=2):
    """
    Enrich a property object with information about nearby schools and transport
    
    Args:
        property_obj: Property object to enrich
        school_distance_km (float): Radius for school search
        transport_distance_km (float): Radius for transport search
    
    Returns:
        dict: Dictionary with nearby_schools and nearby_transport lists
    """
    if not property_obj.latitude or not property_obj.longitude:
        return {
            'nearby_schools': [],
            'nearby_transport': []
        }
    
    nearby_schools = find_nearby_schools(
        property_obj.latitude,
        property_obj.longitude,
        school_distance_km
    )
    
    nearby_transport = find_nearby_transport(
        property_obj.latitude,
        property_obj.longitude,
        transport_distance_km
    )
    
    return {
        'nearby_schools': nearby_schools,
        'nearby_transport': nearby_transport
    }
