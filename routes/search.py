from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import SavedSearch, Property
from extensions import db
from services.search_service import find_matching_properties

bp = Blueprint('search', __name__, url_prefix='/search')

@bp.route('/')
def search_form():
    """Display search form"""
    return render_template('search/form.html')

@bp.route('/results')
def search_results():
    """Show search results"""
    # Get search parameters from query string
    criteria = {
        'min_price': request.args.get('min_price', type=float),
        'max_price': request.args.get('max_price', type=float),
        'counties': request.args.getlist('counties'),
        'cities': request.args.getlist('cities'),
        'min_bedrooms': request.args.get('min_bedrooms', type=int),
        'max_bedrooms': request.args.get('max_bedrooms', type=int),
        'property_types': request.args.getlist('property_types'),
        'min_size_sqm': request.args.get('min_size_sqm', type=float),
        'max_size_sqm': request.args.get('max_size_sqm', type=float),
        'ber_rating': request.args.get('ber_rating'),
        'source': request.args.get('source'),
        'max_school_distance_km': request.args.get('max_school_distance_km', type=float),
        'max_transport_distance_km': request.args.get('max_transport_distance_km', type=float),
    }
    
    properties = find_matching_properties(criteria)
    
    return render_template('search/results.html', properties=properties, criteria=criteria)

@bp.route('/save', methods=['POST'])
@login_required
def save_search():
    """Save search criteria for alerts"""
    data = request.get_json()
    
    saved_search = SavedSearch(
        user_id=current_user.id,
        name=data.get('name', 'My Search'),
        min_price=data.get('min_price'),
        max_price=data.get('max_price'),
        counties=data.get('counties'),
        cities=data.get('cities'),
        min_bedrooms=data.get('min_bedrooms'),
        max_bedrooms=data.get('max_bedrooms'),
        property_types=data.get('property_types'),
        min_size_sqm=data.get('min_size_sqm'),
        max_size_sqm=data.get('max_size_sqm'),
        max_school_distance_km=data.get('max_school_distance_km'),
        preferred_school_gender=data.get('preferred_school_gender'),
        preferred_school_denomination=data.get('preferred_school_denomination'),
        max_transport_distance_km=data.get('max_transport_distance_km'),
        preferred_transport_types=data.get('preferred_transport_types'),
        email_alerts=data.get('email_alerts', True),
        alert_frequency=data.get('alert_frequency', 'daily')
    )
    
    db.session.add(saved_search)
    db.session.commit()
    
    return jsonify({'success': True, 'search_id': saved_search.id})

@bp.route('/saved')
@login_required
def saved_searches():
    """List user's saved searches"""
    searches = SavedSearch.query.filter_by(user_id=current_user.id).all()
    return render_template('search/saved.html', searches=searches)

@bp.route('/saved/<int:search_id>/delete', methods=['POST'])
@login_required
def delete_saved_search(search_id):
    """Delete a saved search"""
    saved_search = SavedSearch.query.filter_by(
        id=search_id,
        user_id=current_user.id
    ).first_or_404()
    
    db.session.delete(saved_search)
    db.session.commit()
    
    return jsonify({'success': True})

@bp.route('/saved/<int:search_id>/run')
@login_required
def run_saved_search(search_id):
    """Run a saved search"""
    saved_search = SavedSearch.query.filter_by(
        id=search_id,
        user_id=current_user.id
    ).first_or_404()
    
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
    
    properties = find_matching_properties(criteria)
    
    return render_template('search/results.html', properties=properties, criteria=criteria, saved_search=saved_search)
