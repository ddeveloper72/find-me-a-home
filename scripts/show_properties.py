"""Show all properties in the database"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import app
from models import Property

with app.app_context():
    props = Property.query.filter_by(source='myhome.ie').order_by(Property.id).all()
    
    print(f'\n{"="*80}')
    print(f'MyHome.ie Properties ({len(props)})')
    print(f'{"="*80}\n')
    
    for p in props:
        print(f'[{p.id}] €{p.price:,.0f} - {p.bedrooms}bed/{p.bathrooms or 0}bath - {p.property_type}')
        print(f'    {p.address}')
        
        if p.latitude:
            print(f'    📍 Coords: ({p.latitude:.6f}, {p.longitude:.6f})')
        else:
            print(f'    📍 Coords: None')
        
        if p.eircode:
            print(f'    📮 Eircode: {p.eircode}')
        
        if p.ber_rating:
            print(f'    ⚡ BER: {p.ber_rating}')
        
        if p.size_sqm:
            print(f'    📐 Size: {p.size_sqm} m²')
        
        print(f'    🔗 {p.url}')
        print()
