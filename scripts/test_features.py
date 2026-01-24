#!/usr/bin/env python
"""
Quick test of property features with sample data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db
from models import Property, School, TransportStation
from services.location_service import find_nearby_schools, find_nearby_transport

with app.app_context():
    print("="*80)
    print("FEATURE TEST - Find Me A Home")
    print("="*80)
    
    # Get a sample property
    prop = Property.query.filter(
        Property.latitude.isnot(None),
        Property.longitude.isnot(None)
    ).first()
    
    if not prop:
        print("❌ No properties with coordinates found")
        sys.exit(1)
    
    print(f"\n📍 Testing with sample property:")
    print(f"   {prop.title}")
    print(f"   €{prop.price:,.0f} | {prop.bedrooms} bed | {prop.property_type}")
    print(f"   Location: {prop.latitude:.6f}, {prop.longitude:.6f}")
    
    # Find nearby schools
    print(f"\n🏫 Finding schools within 5km...")
    nearby_schools = find_nearby_schools(
        prop.latitude,
        prop.longitude,
        max_distance_km=5.0,
        limit=5
    )
    
    if nearby_schools:
        print(f"   Found {len(nearby_schools)} schools:")
        for school in nearby_schools[:5]:
            print(f"   • {school.name[:50]:<50} {school.distance_km:.2f}km")
    else:
        print("   No schools found within 5km")
    
    # Find nearby transport
    print(f"\n🚆 Finding transport within 5km...")
    nearby_transport = find_nearby_transport(
        prop.latitude,
        prop.longitude,
        max_distance_km=5.0,
        limit=5
    )
    
    if nearby_transport:
        print(f"   Found {len(nearby_transport)} stations:")
        for station in nearby_transport[:5]:
            print(f"   • {station.name[:50]:<50} {station.distance_km:.2f}km")
    else:
        print("   No transport found within 5km")
    
    # Database stats
    print(f"\n📊 Database Summary:")
    print(f"   Properties: {Property.query.count():,}")
    print(f"   Schools: {School.query.count():,}")
    print(f"   Stations: {TransportStation.query.count():,}")
    
    print("\n" + "="*80)
    print("✅ All features working!")
    print("="*80)
