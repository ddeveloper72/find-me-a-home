import sys
sys.path.insert(0, '.')
from app import app
from models import TransportStation

with app.app_context():
    stations = TransportStation.query.limit(5).all()
    print('Sample stations:')
    for s in stations:
        print(f'{s.name}: address="{s.address}", lat={s.latitude}, lon={s.longitude}')
    
    print(f'\nTotal stations: {TransportStation.query.count()}')
    print(f'Stations with address: {TransportStation.query.filter(TransportStation.address.isnot(None)).count()}')
    print(f'Stations with coords: {TransportStation.query.filter(TransportStation.latitude.isnot(None)).count()}')
