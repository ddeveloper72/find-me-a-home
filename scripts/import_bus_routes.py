"""
Import bus route numbers for each bus stop from GTFS data.
Extracts which route numbers (e.g., "16", "46A", "123") serve each stop.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import TransportStation
import requests
import zipfile
import io
import csv
from collections import defaultdict

GTFS_URL = "https://www.transportforireland.ie/transitData/Data/GTFS_All.zip"

def download_and_extract_gtfs():
    """Download GTFS zip file"""
    print("Downloading GTFS data...")
    response = requests.get(GTFS_URL)
    response.raise_for_status()
    
    print(f"Downloaded {len(response.content) / (1024*1024):.1f} MB")
    
    return zipfile.ZipFile(io.BytesIO(response.content))

def parse_routes(zip_file):
    """Parse routes.txt to get route_id -> route_short_name mapping"""
    print("Parsing routes.txt...")
    
    route_names = {}
    
    with zip_file.open('routes.txt') as f:
        reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig'))
        for row in reader:
            route_id = row['route_id']
            # Use route_short_name (e.g., "16", "46A") instead of long name
            route_short_name = row.get('route_short_name', row.get('route_long_name', route_id))
            route_names[route_id] = route_short_name
    
    print(f"Found {len(route_names):,} routes")
    return route_names

def parse_trips(zip_file):
    """Parse trips.txt to get trip_id -> route_id mapping"""
    print("Parsing trips.txt...")
    
    trip_routes = {}
    
    with zip_file.open('trips.txt') as f:
        reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig'))
        for row in reader:
            trip_id = row['trip_id']
            route_id = row['route_id']
            trip_routes[trip_id] = route_id
    
    print(f"Found {len(trip_routes):,} trips")
    return trip_routes

def parse_stop_times(zip_file, trip_routes, route_names):
    """Parse stop_times.txt to link stops to routes"""
    print("Parsing stop_times.txt (this may take a minute)...")
    
    # stop_id -> set of route short names
    stop_routes = defaultdict(set)
    
    with zip_file.open('stop_times.txt') as f:
        reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig'))
        processed = 0
        
        for row in reader:
            stop_id = row['stop_id']
            trip_id = row['trip_id']
            
            # Get route for this trip
            if trip_id in trip_routes:
                route_id = trip_routes[trip_id]
                if route_id in route_names:
                    route_name = route_names[route_id]
                    stop_routes[stop_id].add(route_name)
            
            processed += 1
            if processed % 100000 == 0:
                print(f"  Processed {processed:,} stop times...")
    
    print(f"Processed {processed:,} stop times")
    print(f"Found routes for {len(stop_routes):,} unique stops")
    
    return stop_routes

def main():
    with app.app_context():
        # Download GTFS data
        zip_file = download_and_extract_gtfs()
        
        # Parse GTFS files
        route_names = parse_routes(zip_file)
        trip_routes = parse_trips(zip_file)
        stop_routes = parse_stop_times(zip_file, trip_routes, route_names)
        
        # Update database
        print("\nUpdating bus stops with route numbers...")
        
        bus_stops = TransportStation.query.filter_by(station_type='bus').all()
        updated = 0
        no_routes = 0
        
        for stop in bus_stops:
            if stop.external_id and stop.external_id in stop_routes:
                # Sort route numbers for consistent display
                routes = sorted(list(stop_routes[stop.external_id]), key=lambda x: (len(x), x))
                stop.routes = routes  # Store as JSON array
                updated += 1
                
                if updated % 100 == 0:
                    print(f"  Updated {updated:,} stops...")
                    db.session.commit()
            else:
                no_routes += 1
        
        db.session.commit()
        
        print()
        print("=== Completed ===")
        print(f"Total bus stops: {len(bus_stops):,}")
        print(f"Updated with routes: {updated:,}")
        print(f"No routes found: {no_routes:,}")
        print()
        print("Route numbers saved to 'routes' field in database")
        print("Example: ['16', '46A', '123'] for a stop served by those routes")

if __name__ == '__main__':
    main()
