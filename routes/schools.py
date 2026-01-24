from flask import Blueprint, render_template, request, jsonify
from models import School
from services.location_service import find_nearby_schools

bp = Blueprint('schools', __name__, url_prefix='/schools')

@bp.route('/')
def list_schools():
    """List all schools"""
    county = request.args.get('county')
    school_type = request.args.get('type')
    gender = request.args.get('gender')
    
    query = School.query
    
    if county:
        query = query.filter(School.county == county)
    if school_type:
        query = query.filter(School.school_type == school_type)
    if gender:
        query = query.filter(School.gender == gender)
    
    schools = query.order_by(School.name).all()
    
    return render_template('schools/list.html', schools=schools)

@bp.route('/<int:school_id>')
def school_detail(school_id):
    """Show detailed school information"""
    school = School.query.get_or_404(school_id)
    return render_template('schools/detail.html', school=school)

@bp.route('/nearby')
def nearby_schools():
    """Find schools near a location"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    max_distance = request.args.get('max_distance', 5, type=float)
    
    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    schools = find_nearby_schools(lat, lon, max_distance)
    
    return jsonify({
        'schools': [{
            'id': s.id,
            'name': s.name,
            'address': s.address,
            'latitude': s.latitude,
            'longitude': s.longitude,
            'school_type': s.school_type,
            'gender': s.gender,
            'distance': s.distance
        } for s in schools]
    })
