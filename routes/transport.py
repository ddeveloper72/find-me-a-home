from flask import Blueprint, render_template, request, jsonify
from models import TransportStation
from services.location_service import find_nearby_transport
from services.transport_service import get_realtime_info

bp = Blueprint('transport', __name__, url_prefix='/transport')

@bp.route('/')
def list_stations():
    """List all transport stations with pagination"""
    station_type = request.args.get('type')
    county = request.args.get('county')
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 50  # Show 50 stations per page
    
    query = TransportStation.query
    
    if station_type:
        query = query.filter(TransportStation.station_type == station_type)
    if county:
        # Only apply county filter if stations have county data
        # Bus stops don't have county data yet
        query = query.filter(TransportStation.county == county)
    if search:
        query = query.filter(TransportStation.name.ilike(f'%{search}%'))
    
    # Paginate results
    pagination = query.order_by(TransportStation.name).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    stations = pagination.items
    
    return render_template('transport/list.html', 
                         stations=stations, 
                         pagination=pagination)

@bp.route('/autocomplete')
def autocomplete():
    """Autocomplete endpoint for station search"""
    query = request.args.get('q', '').strip()
    station_type = request.args.get('type', '')
    
    if not query or len(query) < 2:
        return jsonify([])
    
    # Build query
    stations_query = TransportStation.query.filter(
        TransportStation.name.ilike(f'%{query}%')
    )
    
    if station_type:
        stations_query = stations_query.filter(
            TransportStation.station_type == station_type
        )
    
    # Limit to 10 results for autocomplete
    stations = stations_query.order_by(TransportStation.name).limit(10).all()
    
    results = [{
        'id': station.id,
        'name': station.name,
        'county': station.county or 'N/A',
        'type': station.station_type or 'train'
    } for station in stations]
    
    return jsonify(results)

@bp.route('/<int:station_id>')
def station_detail(station_id):
    """Show detailed station information with realtime data"""
    station = TransportStation.query.get_or_404(station_id)
    
    # Get realtime information
    realtime_data = get_realtime_info(station)
    
    return render_template('transport/detail.html', station=station, realtime_data=realtime_data)

@bp.route('/nearby')
def nearby_stations():
    """Find transport stations near a location"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    max_distance = request.args.get('max_distance', 2, type=float)
    
    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    stations = find_nearby_transport(lat, lon, max_distance)
    
    return jsonify({
        'stations': [{
            'id': s.id,
            'name': s.name,
            'station_type': s.station_type,
            'address': s.address,
            'latitude': s.latitude,
            'longitude': s.longitude,
            'routes': s.routes,
            'distance': s.distance
        } for s in stations]
    })
