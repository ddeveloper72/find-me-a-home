from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///findmehome.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
from extensions import db, login_manager
db.init_app(app)
login_manager.init_app(app)

# Import models and routes after app initialization
from models import User, Property, School, TransportStation, SavedSearch, FavoriteProperty
from routes import auth, properties, schools, transport, search

# Register blueprints
app.register_blueprint(auth.bp)
app.register_blueprint(properties.bp)
app.register_blueprint(schools.bp)
app.register_blueprint(transport.bp)
app.register_blueprint(search.bp)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test-login')
def test_login():
    """Temporary test login - bypasses Azure AD for development"""
    from models import User
    
    # Create or get test user
    user = User.query.filter_by(email='test@test.com').first()
    if not user:
        user = User(email='test@test.com', name='Test User')
        db.session.add(user)
        db.session.commit()
    
    login_user(user)
    flash('Logged in as Test User (development mode)', 'success')
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    saved_searches = SavedSearch.query.filter_by(user_id=current_user.id).all()
    favorites = FavoriteProperty.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', saved_searches=saved_searches, favorites=favorites)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
