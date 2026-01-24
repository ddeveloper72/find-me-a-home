import requests
from models import School
from extensions import db
import csv
from io import StringIO

def fetch_schools_from_gov():
    """
    Fetch school data from Irish government sources
    Note: This would require scraping or using available datasets
    """
    # The education.ie website doesn't provide a direct API
    # You would need to:
    # 1. Download the schools dataset from data.gov.ie
    # 2. Or scrape the ArcGIS map data
    # 3. Or use the CSV/Excel exports available
    
    # Example: Using ArcGIS REST API
    url = "https://services-eu1.arcgis.com/HkXiH6hCLlYq7qYC/arcgis/rest/services/Schools_Map/FeatureServer/0/query"
    
    params = {
        'where': '1=1',
        'outFields': '*',
        'f': 'json',
        'resultRecordCount': 1000,  # Fetch in batches
        'resultOffset': 0
    }
    
    schools = []
    has_more = True
    
    try:
        while has_more:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'features' not in data or not data['features']:
                has_more = False
                break
            
            for feature in data['features']:
                attrs = feature.get('attributes', {})
                geom = feature.get('geometry', {})
                
                # Extract school data
                school_data = {
                    'roll_number': attrs.get('Roll_Number'),
                    'name': attrs.get('Official_School_Name') or attrs.get('School_Name'),
                    'address': attrs.get('Address_1'),
                    'city': attrs.get('Address_2'),
                    'county': attrs.get('County'),
                    'eircode': attrs.get('Eircode'),
                    'latitude': geom.get('y'),
                    'longitude': geom.get('x'),
                    'school_type': attrs.get('School_Type'),
                    'denomination': attrs.get('Ethos'),
                    'gender': attrs.get('Gender'),
                    'website': attrs.get('Website'),
                    'phone': attrs.get('Phone'),
                    'email': attrs.get('Email'),
                }
                
                # Only process if we have required fields
                if school_data['roll_number'] and school_data['name']:
                    # Filter for secondary schools only
                    if school_data['school_type'] and 'secondary' in school_data['school_type'].lower():
                        # Check if school already exists
                        existing = School.query.filter_by(roll_number=school_data['roll_number']).first()
                        
                        if not existing:
                            school = School(**school_data)
                            schools.append(school)
            
            # Check if there are more records
            if len(data['features']) < params['resultRecordCount']:
                has_more = False
            else:
                params['resultOffset'] += params['resultRecordCount']
        
        if schools:
            db.session.add_all(schools)
            db.session.commit()
        
        return len(schools)
        
    except Exception as e:
        print(f"Error fetching schools: {e}")
        return 0

def update_school_data():
    """
    Update school information in the database
    """
    return fetch_schools_from_gov()
