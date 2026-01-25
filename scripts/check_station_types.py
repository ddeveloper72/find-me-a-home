"""Check what station_type values exist in the database"""
import sys
sys.path.insert(0, '.')
from app import app, db
from models import TransportStation
from sqlalchemy import func

with app.app_context():
    # Get all unique station types
    types = db.session.query(TransportStation.station_type, func.count(TransportStation.id)).group_by(TransportStation.station_type).all()
    
    print("Station Types in database:")
    print("="*50)
    for station_type, count in types:
        print(f"  '{station_type}': {count} stations")
    
    print(f"\nTotal stations: {TransportStation.query.count()}")
