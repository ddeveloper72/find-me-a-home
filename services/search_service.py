from models import Property, SavedSearch
from services.location_service import find_nearby_schools, find_nearby_transport

def find_matching_properties(criteria):
    """
    Find properties matching the given search criteria
    """
    query = Property.query
    
    # Price filters
    if criteria.get('min_price'):
        query = query.filter(Property.price >= criteria['min_price'])
    if criteria.get('max_price'):
        query = query.filter(Property.price <= criteria['max_price'])
    
    # Location filters
    if criteria.get('counties') and len(criteria['counties']) > 0:
        query = query.filter(Property.county.in_(criteria['counties']))
    if criteria.get('cities') and len(criteria['cities']) > 0:
        query = query.filter(Property.city.in_(criteria['cities']))
    
    # Property characteristics
    if criteria.get('min_bedrooms'):
        query = query.filter(Property.bedrooms >= criteria['min_bedrooms'])
    if criteria.get('max_bedrooms'):
        query = query.filter(Property.bedrooms <= criteria['max_bedrooms'])
    
    if criteria.get('property_types') and len(criteria['property_types']) > 0:
        query = query.filter(Property.property_type.in_(criteria['property_types']))
    
    if criteria.get('min_size_sqm'):
        query = query.filter(Property.size_sqm >= criteria['min_size_sqm'])
    if criteria.get('max_size_sqm'):
        query = query.filter(Property.size_sqm <= criteria['max_size_sqm'])
    
    # BER rating filter (includes selected rating and better)
    if criteria.get('ber_rating'):
        ber_order = ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3', 'D1', 'D2', 'E1', 'E2', 'F', 'G']
        selected_rating = criteria['ber_rating']
        if selected_rating in ber_order:
            # Get all ratings equal to or better than selected
            valid_ratings = ber_order[:ber_order.index(selected_rating) + 1]
            query = query.filter(Property.ber_rating.in_(valid_ratings))
    
    # Data source filter
    if criteria.get('source'):
        query = query.filter(Property.source == criteria['source'])
    
    # Get base properties
    properties = query.all()
    
    # Filter by proximity to schools and transport if specified
    if criteria.get('max_school_distance_km') or criteria.get('max_transport_distance_km'):
        filtered_properties = []
        
        for prop in properties:
            if not prop.latitude or not prop.longitude:
                continue
            
            include = True
            
            # Check school proximity
            if criteria.get('max_school_distance_km'):
                nearby_schools = find_nearby_schools(
                    prop.latitude,
                    prop.longitude,
                    criteria['max_school_distance_km']
                )
                if not nearby_schools:
                    include = False
            
            # Check transport proximity
            if include and criteria.get('max_transport_distance_km'):
                nearby_transport = find_nearby_transport(
                    prop.latitude,
                    prop.longitude,
                    criteria['max_transport_distance_km']
                )
                if not nearby_transport:
                    include = False
            
            if include:
                filtered_properties.append(prop)
        
        properties = filtered_properties
    
    return properties

def check_for_new_matches(saved_search, since_datetime):
    """
    Check if there are new properties matching a saved search
    """
    criteria = {
        'min_price': saved_search.min_price,
        'max_price': saved_search.max_price,
        'counties': saved_search.counties,
        'cities': saved_search.cities,
        'min_bedrooms': saved_search.min_bedrooms,
        'max_bedrooms': saved_search.max_bedrooms,
        'property_types': saved_search.property_types,
        'min_size_sqm': saved_search.min_size_sqm,
        'max_size_sqm': saved_search.max_size_sqm,
        'max_school_distance_km': saved_search.max_school_distance_km,
        'max_transport_distance_km': saved_search.max_transport_distance_km,
    }
    
    # Get matching properties created since the specified datetime
    properties = find_matching_properties(criteria)
    new_properties = [p for p in properties if p.created_at >= since_datetime]
    
    return new_properties
