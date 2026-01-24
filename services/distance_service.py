"""
Distance calculation utilities
Provides functions for calculating distances between geographic coordinates
"""

from geopy.distance import geodesic


def calculate_distance(lat1, lon1, lat2, lon2, unit='km'):
    """
    Calculate the distance between two geographic points using the Haversine formula.
    
    Args:
        lat1 (float): Latitude of first point
        lon1 (float): Longitude of first point
        lat2 (float): Latitude of second point
        lon2 (float): Longitude of second point
        unit (str): Unit of measurement ('km' or 'miles'). Default is 'km'.
    
    Returns:
        float: Distance in specified units, or None if coordinates are invalid
    
    Example:
        >>> distance = calculate_distance(53.3498, -6.2603, 53.2707, -9.0568)
        >>> print(f"Distance: {distance:.2f} km")
    """
    try:
        # Validate coordinates
        if not all([lat1, lon1, lat2, lon2]):
            return None
        
        # Create coordinate tuples (latitude, longitude)
        point1 = (lat1, lon1)
        point2 = (lat2, lon2)
        
        # Calculate distance
        dist = geodesic(point1, point2)
        
        # Return in requested units
        if unit == 'miles':
            return dist.miles
        else:  # Default to kilometers
            return dist.kilometers
            
    except Exception as e:
        print(f"Error calculating distance: {e}")
        return None


def filter_by_distance(items, center_lat, center_lon, max_distance_km, lat_field='latitude', lon_field='longitude'):
    """
    Filter a list of items by distance from a center point.
    
    Args:
        items (list): List of objects or dicts with lat/lon coordinates
        center_lat (float): Latitude of center point
        center_lon (float): Longitude of center point
        max_distance_km (float): Maximum distance in kilometers
        lat_field (str): Name of latitude field/attribute
        lon_field (str): Name of longitude field/attribute
    
    Returns:
        list: Filtered items within the distance, with 'distance_km' added
    
    Example:
        >>> schools = School.query.all()
        >>> nearby = filter_by_distance(schools, 53.3498, -6.2603, 5.0)
    """
    results = []
    
    for item in items:
        # Get coordinates from item (works for both objects and dicts)
        if isinstance(item, dict):
            lat = item.get(lat_field)
            lon = item.get(lon_field)
        else:
            lat = getattr(item, lat_field, None)
            lon = getattr(item, lon_field, None)
        
        # Skip items without coordinates
        if not lat or not lon:
            continue
        
        # Calculate distance
        distance = calculate_distance(center_lat, center_lon, lat, lon)
        
        if distance is not None and distance <= max_distance_km:
            # Add distance to item (if it's a dict, modify it; if object, add attribute)
            if isinstance(item, dict):
                item['distance_km'] = round(distance, 2)
            else:
                item.distance_km = round(distance, 2)
            
            results.append(item)
    
    # Sort by distance (closest first)
    results.sort(key=lambda x: x['distance_km'] if isinstance(x, dict) else x.distance_km)
    
    return results


def get_nearest(items, center_lat, center_lon, limit=10, lat_field='latitude', lon_field='longitude'):
    """
    Get the nearest N items to a center point.
    
    Args:
        items (list): List of objects or dicts with lat/lon coordinates
        center_lat (float): Latitude of center point
        center_lon (float): Longitude of center point
        limit (int): Maximum number of items to return
        lat_field (str): Name of latitude field/attribute
        lon_field (str): Name of longitude field/attribute
    
    Returns:
        list: Nearest items, sorted by distance, with 'distance_km' added
    
    Example:
        >>> stations = TransportStation.query.all()
        >>> nearest_5 = get_nearest(stations, 53.3498, -6.2603, limit=5)
    """
    items_with_distance = []
    
    for item in items:
        # Get coordinates
        if isinstance(item, dict):
            lat = item.get(lat_field)
            lon = item.get(lon_field)
        else:
            lat = getattr(item, lat_field, None)
            lon = getattr(item, lon_field, None)
        
        # Skip items without coordinates
        if not lat or not lon:
            continue
        
        # Calculate distance
        distance = calculate_distance(center_lat, center_lon, lat, lon)
        
        if distance is not None:
            # Add distance to item
            if isinstance(item, dict):
                item['distance_km'] = round(distance, 2)
            else:
                item.distance_km = round(distance, 2)
            
            items_with_distance.append((item, distance))
    
    # Sort by distance and take the first N
    items_with_distance.sort(key=lambda x: x[1])
    results = [item for item, distance in items_with_distance[:limit]]
    
    return results


def get_bounding_box(center_lat, center_lon, radius_km):
    """
    Calculate a bounding box (min/max lat/lon) for a given radius around a point.
    Useful for efficient database queries before calculating exact distances.
    
    Args:
        center_lat (float): Center latitude
        center_lon (float): Center longitude
        radius_km (float): Radius in kilometers
    
    Returns:
        dict: {'min_lat', 'max_lat', 'min_lon', 'max_lon'}
    
    Example:
        >>> bbox = get_bounding_box(53.3498, -6.2603, 10)
        >>> schools = School.query.filter(
        ...     School.latitude.between(bbox['min_lat'], bbox['max_lat']),
        ...     School.longitude.between(bbox['min_lon'], bbox['max_lon'])
        ... ).all()
    """
    from geopy import Point
    from geopy.distance import distance
    
    center = Point(center_lat, center_lon)
    
    # Calculate points at the edges of the radius
    north = distance(kilometers=radius_km).destination(center, bearing=0)
    south = distance(kilometers=radius_km).destination(center, bearing=180)
    east = distance(kilometers=radius_km).destination(center, bearing=90)
    west = distance(kilometers=radius_km).destination(center, bearing=270)
    
    return {
        'min_lat': south.latitude,
        'max_lat': north.latitude,
        'min_lon': west.longitude,
        'max_lon': east.longitude,
    }


# Example usage and testing
if __name__ == '__main__':
    # Test distance calculation
    dublin_city = (53.3498, -6.2603)  # Dublin, Ireland
    galway_city = (53.2707, -9.0568)  # Galway, Ireland
    
    print("Testing distance calculations...")
    print(f"Dublin coordinates: {dublin_city}")
    print(f"Galway coordinates: {galway_city}")
    
    distance_km = calculate_distance(*dublin_city, *galway_city)
    distance_miles = calculate_distance(*dublin_city, *galway_city, unit='miles')
    
    print(f"\nDistance Dublin to Galway:")
    print(f"  {distance_km:.2f} km")
    print(f"  {distance_miles:.2f} miles")
    
    # Test bounding box
    print(f"\nBounding box for 10km radius around Dublin:")
    bbox = get_bounding_box(*dublin_city, 10)
    for key, value in bbox.items():
        print(f"  {key}: {value:.4f}")
