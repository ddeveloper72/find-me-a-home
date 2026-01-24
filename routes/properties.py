from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import Property, FavoriteProperty
from extensions import db
from services.property_service import update_properties_from_apis, fetch_property_details
import math

bp = Blueprint('properties', __name__, url_prefix='/properties')

@bp.route('/')
def list_properties():
    """List properties with optional filtering"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get filter parameters
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    county = request.args.get('county')
    city = request.args.get('city')
    min_bedrooms = request.args.get('min_bedrooms', type=int)
    property_type = request.args.get('property_type')
    
    # Build query
    query = Property.query
    
    if min_price:
        query = query.filter(Property.price >= min_price)
    if max_price:
        query = query.filter(Property.price <= max_price)
    if county:
        query = query.filter(Property.county == county)
    if city:
        query = query.filter(Property.city == city)
    if min_bedrooms:
        query = query.filter(Property.bedrooms >= min_bedrooms)
    if property_type:
        query = query.filter(Property.property_type == property_type)
    
    # Paginate results
    properties = query.order_by(Property.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('properties/list.html', properties=properties)

@bp.route('/<int:property_id>')
def property_detail(property_id):
    """Show detailed property information"""
    property = Property.query.get_or_404(property_id)
    
    # Get nearby schools and transport
    from services.location_service import find_nearby_schools, find_nearby_transport
    
    nearby_schools = find_nearby_schools(property.latitude, property.longitude, max_distance_km=5)
    nearby_transport = find_nearby_transport(property.latitude, property.longitude, max_distance_km=2)
    
    # Check if property is favorited by current user
    is_favorite = False
    favorite = None
    if current_user.is_authenticated:
        favorite = FavoriteProperty.query.filter_by(
            user_id=current_user.id,
            property_id=property_id
        ).first()
        is_favorite = favorite is not None
    
    return render_template(
        'properties/detail.html',
        property=property,
        nearby_schools=nearby_schools,
        nearby_transport=nearby_transport,
        is_favorite=is_favorite,
        favorite=favorite
    )

@bp.route('/<int:property_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(property_id):
    """Add or remove property from favorites"""
    property = Property.query.get_or_404(property_id)
    
    favorite = FavoriteProperty.query.filter_by(
        user_id=current_user.id,
        property_id=property_id
    ).first()
    
    if favorite:
        # Remove from favorites
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'success': True, 'is_favorite': False})
    else:
        # Add to favorites
        favorite = FavoriteProperty(
            user_id=current_user.id,
            property_id=property_id
        )
        db.session.add(favorite)
        db.session.commit()
        return jsonify({'success': True, 'is_favorite': True})

@bp.route('/<int:property_id>/favorite/update', methods=['POST'])
@login_required
def update_favorite(property_id):
    """Update favorite property notes and ranking"""
    favorite = FavoriteProperty.query.filter_by(
        user_id=current_user.id,
        property_id=property_id
    ).first_or_404()
    
    data = request.get_json()
    
    if 'rank' in data:
        favorite.rank = data['rank']
    if 'notes' in data:
        favorite.notes = data['notes']
    
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/refresh')
@login_required
def refresh_properties():
    """Trigger refresh of property data from external APIs"""
    from services.property_service import update_properties_from_apis
    
    try:
        count = update_properties_from_apis()
        return jsonify({'success': True, 'message': f'Updated {count} properties'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
