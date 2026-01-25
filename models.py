from datetime import datetime
from flask_login import UserMixin
from extensions import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    azure_oid = db.Column(db.String(100), unique=True, nullable=True)  # Azure AD Object ID
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    saved_searches = db.relationship('SavedSearch', backref='user', lazy=True, cascade='all, delete-orphan')
    favorite_properties = db.relationship('FavoriteProperty', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'

class Property(db.Model):
    __tablename__ = 'properties'
    
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(100), unique=True)  # ID from source API
    source = db.Column(db.String(50))  # myhome.ie, daft.ie, etc.
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(300), nullable=False)
    county = db.Column(db.String(50))
    city = db.Column(db.String(100))
    eircode = db.Column(db.String(10))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Integer)
    property_type = db.Column(db.String(50))  # house, apartment, etc.
    size_sqm = db.Column(db.Float)
    ber_rating = db.Column(db.String(10))  # Energy rating
    image_urls = db.Column(db.JSON)  # Store as JSON array
    url = db.Column(db.String(500))  # Link to original listing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    favorites = db.relationship('FavoriteProperty', backref='property', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Property {self.title}>'

class School(db.Model):
    __tablename__ = 'schools'
    
    id = db.Column(db.Integer, primary_key=True)
    roll_number = db.Column(db.String(20), unique=True)  # Official school ID
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(300))
    county = db.Column(db.String(50))
    city = db.Column(db.String(100))
    eircode = db.Column(db.String(10))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    school_type = db.Column(db.String(50))  # Secondary, Community, etc.
    denomination = db.Column(db.String(50))
    gender = db.Column(db.String(20))  # Boys, Girls, Mixed
    total_students = db.Column(db.Integer)
    website = db.Column(db.String(300))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<School {self.name}>'

class TransportStation(db.Model):
    __tablename__ = 'transport_stations'
    
    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(100))  # ID from API/GTFS
    station_code = db.Column(db.String(50))  # Public-facing code/number (e.g., bus stop number)
    name = db.Column(db.String(200), nullable=False)
    station_type = db.Column(db.String(50))  # train, bus, luas, etc.
    address = db.Column(db.String(300))
    county = db.Column(db.String(50))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    routes = db.Column(db.JSON)  # Store route numbers/names as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<TransportStation {self.name}>'

class SavedSearch(db.Model):
    __tablename__ = 'saved_searches'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    
    # Search criteria
    min_price = db.Column(db.Float)
    max_price = db.Column(db.Float)
    counties = db.Column(db.JSON)  # Array of county names
    cities = db.Column(db.JSON)  # Array of city names
    min_bedrooms = db.Column(db.Integer)
    max_bedrooms = db.Column(db.Integer)
    property_types = db.Column(db.JSON)  # Array of property types
    min_size_sqm = db.Column(db.Float)
    max_size_sqm = db.Column(db.Float)
    
    # School preferences
    max_school_distance_km = db.Column(db.Float)
    preferred_school_gender = db.Column(db.String(20))
    preferred_school_denomination = db.Column(db.String(50))
    
    # Transport preferences
    max_transport_distance_km = db.Column(db.Float)
    preferred_transport_types = db.Column(db.JSON)  # Array of transport types
    
    # Alert settings
    email_alerts = db.Column(db.Boolean, default=True)
    alert_frequency = db.Column(db.String(20), default='daily')  # daily, weekly, instant
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SavedSearch {self.name}>'

class FavoriteProperty(db.Model):
    __tablename__ = 'favorite_properties'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=False)
    rank = db.Column(db.Integer)  # User's ranking (1 = highest)
    notes = db.Column(db.Text)  # User's personal notes about the property
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate favorites
    __table_args__ = (db.UniqueConstraint('user_id', 'property_id', name='unique_user_property'),)
    
    def __repr__(self):
        return f'<FavoriteProperty User:{self.user_id} Property:{self.property_id}>'
