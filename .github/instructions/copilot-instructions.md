## Application Purpose
This application helps users find homes for sale in Ireland while providing comprehensive information on:
- **Property Listings**: Browse and search properties across Ireland
- **Secondary Schools**: Detailed information about nearby schools
- **Transport Options**: Real-time transport information (trains, buses)
- **Smart Alerts**: Notifications when new properties match saved criteria
- **Favorites**: Save and rank properties with personal notes
- **Interactive Maps**: Visualize properties, schools, and transport locations

## Architecture Overview

### Technology Stack
- **Backend**: Flask (Python 3.11+)
- **Database**: PostgreSQL (hosted on Azure/Heroku)
- **Authentication**: Azure AD B2C
- **Frontend**: Bootstrap 5, Leaflet.js, Vanilla JavaScript
- **Hosting**: Heroku
- **APIs**: Irish Rail API, Department of Education ArcGIS, GTFS-R

### Project Structure
```
Find me a home/
├── app.py                    # Main Flask application
├── models.py                 # SQLAlchemy database models
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (not committed)
├── routes/                   # Blueprint route handlers
│   ├── auth.py              # Azure AD B2C authentication
│   ├── properties.py        # Property CRUD operations
│   ├── schools.py           # School information
│   ├── transport.py         # Transport data & real-time info
│   └── search.py            # Search & saved searches
├── services/                 # Business logic layer
│   ├── property_service.py  # Property data fetching
│   ├── school_service.py    # School data integration
│   ├── transport_service.py # Transport API integration
│   ├── location_service.py  # Distance calculations
│   └── search_service.py    # Search matching logic
├── templates/                # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── dashboard.html
│   └── ... (various feature templates)
├── static/
│   ├── css/styles.css       # Custom styles
│   └── js/scripts.js        # Custom JavaScript
└── scripts/
    └── load_data.py         # Data loading utilities
```

## Database Models
1. **User**: Azure AD authenticated users
2. **Property**: Property listings with geocoding
3. **School**: Secondary schools with locations
4. **TransportStation**: Train/bus stations
5. **SavedSearch**: User's search criteria with alert settings
6. **FavoriteProperty**: User's saved properties with rankings

## Key Features Implementation

### Authentication
- Azure AD B2C integration via MSAL
- Secure OAuth 2.0 flow
- User profile management

### Property Search
- Multi-criteria filtering (price, location, size, bedrooms)
- Proximity-based filtering (schools, transport)
- Saved searches with email alerts

### Maps Integration
- Leaflet.js for interactive maps
- Color-coded markers (blue=properties, green=schools, red=transport)
- Distance calculations using Haversine formula

### Real-time Data
- Irish Rail API for train schedules
- GTFS-R for bus/LUAS information

## Data Sources

### Properties
We have discovered several API options for Irish property data:

#### 1. **MyHome.ie API** (Undocumented - Currently Used)
- **Endpoint**: `https://api.myhome.ie/home`
- **Format**: JSON
- **Status**: ✅ Working (undocumented internal API)
- **Data**: Property listings, prices, BER ratings, images, addresses
- **Limitations**: No coordinates, no descriptions, structure may change
- **Implementation**: `scripts/import_myhome_properties.py`
- **Owner**: The Irish Times (verified via DNS: irishtimes.map.fastly.net)

#### 2. **Daft.ie API** (Documented - Pending Access)
- **Endpoint**: `https://api.daft.ie/v3/`
- **Format**: SOAP/XML
- **Status**: ⏳ Awaiting personal developer API key
- **Access**: Free for personal use (1,000 requests/day)
- **Data**: Full property details with coordinates, images, search filters
- **Documentation**: https://api.daft.ie/doc/v3/
- **Terms**: https://api.daft.ie/terms/
- **Implementation**: `scripts/import_daft_properties.py` (ready)
- **Setup Guide**: See `DAFT_API_SETUP.md`

#### 3. **Property.ie RSS Feeds** (Blocked)
- **Status**: ❌ Blocks automated access (403 Forbidden)
- **Note**: Feeds exist but actively prevent scraping
- **Alternative**: Manual download possible but not automated

#### 4. **PropertyInsight.ie API** (Historical Data)
- **Status**: ❓ Requires contact for pricing
- **Focus**: Historical price data, market analysis (600,000+ properties)
- **Use Case**: Price trends rather than current listings
- **Website**: https://propertyinsight.ie/features/api

**Current Strategy**: 
- Use MyHome.ie API for immediate property data
- Switch to Daft.ie API once personal key is approved
- MyHome.ie provides good coverage but limited detail
- Daft.ie will provide comprehensive data with coordinates

### Schools
- Department of Education ArcGIS REST API
- Filters for secondary schools only
- Automated data fetching implemented

### Transport
- Irish Rail XML API (implemented)
- GTFS-R feed (requires API key from data.gov.ie)

## Development Guidelines

### Environment Setup
1. Use Python virtual environment (.venv)
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and configure
4. Initialize database: Run migration scripts
5. Load initial data: `python scripts/load_data.py`

### Code Style
- Follow PEP 8 for Python
- Use Flask blueprints for route organization
- Separate business logic into services/
- Keep templates DRY with base.html inheritance

### Security
- Never commit `.env` file
- Use environment variables for secrets
- Validate user inputs
- Use HTTPS in production
- Implement CSRF protection (Flask-WTF)

## Deployment (Heroku)

### Prerequisites
- Heroku account
- Heroku CLI installed
- Git repository initialized

### Steps
1. Create Heroku app: `heroku create app-name`
2. Add PostgreSQL: `heroku addons:create heroku-postgresql:mini`
3. Set environment variables: `heroku config:set KEY=value`
4. Deploy: `git push heroku main`
5. Initialize DB: `heroku run python` → run db.create_all()

### Required Environment Variables
- `SECRET_KEY`: Flask secret key
- `DATABASE_URL`: PostgreSQL connection string (auto-set by Heroku)
- `AZURE_AD_CLIENT_ID`: Azure AD B2C application ID
- `AZURE_AD_CLIENT_SECRET`: Azure AD B2C secret
- `AZURE_AD_TENANT_NAME`: Azure AD B2C tenant
- `AZURE_AD_AUTHORITY`: Azure AD B2C authority URL
- `DAFT_API_KEY`: Daft.ie personal API key (optional, when available)
- `GOOGLE_MAPS_API_KEY`: For geocoding (optional)
- `MAIL_SERVER`, `MAIL_USERNAME`, `MAIL_PASSWORD`: For email alerts

## API Integration Notes

### Irish Rail API
- Endpoint: http://api.irishrail.ie/realtime/realtime.asmx/
- Format: XML
- Rate limits: Reasonable use
- Implementation: `services/transport_service.py`

### Department of Education ArcGIS
- Endpoint: services-eu1.arcgis.com (REST API)
- Batch fetching with pagination
- Filters for secondary schools
- Implementation: `services/school_service.py`

### GTFS-R (Bus/LUAS)
- Requires API key from data.gov.ie
- Protocol Buffers format
- Real-time updates
- Status: Placeholder implementation

## Future Enhancements
- [x] Property API integration (MyHome.ie working, Daft.ie ready)
- [ ] Geocode MyHome.ie properties for map functionality
- [ ] Add background jobs for data updates (APScheduler)
- [ ] Implement email alert system
- [ ] Add property image galleries
- [ ] Price trend analysis (PropertyInsight.ie integration)
- [ ] Mortgage calculator
- [ ] Commute time calculator
- [ ] Mobile responsive improvements
- [ ] Unit tests and CI/CD
- [ ] Switch to Daft.ie API when personal key is approved

## Resources & Links

**Transport:**
- Irish Rail API: http://api.irishrail.ie/realtime/
- GTFS-R Data: https://data.gov.ie/dataset/realtime-passenger-information-gtfsr

**Properties:**
- MyHome.ie: www.myhome.ie | API: https://api.myhome.ie/home (undocumented)
- Daft.ie: www.daft.ie | API: https://api.daft.ie/v3/ (documented, personal use available)
- Daft.ie Docs: https://api.daft.ie/doc/v3/ | Terms: https://api.daft.ie/terms/
- Property.ie: www.property.ie (RSS feeds blocked for automation)
- PropertyInsight.ie: https://propertyinsight.ie/features/api (commercial, historical data)

**Schools:**
- Find a School: https://www.gov.ie/en/department-of-education/services/find-a-school/
- Schools Map: https://education-statistics-doeirl.hub.arcgis.com/maps/doeirl::schools-map/

**Azure:**
- Azure AD B2C: https://azure.microsoft.com/en-us/services/active-directory/external-identities/b2c/
- Azure Portal: https://portal.azure.com/

## Getting Help
- Flask Documentation: https://flask.palletsprojects.com/
- Bootstrap 5: https://getbootstrap.com/docs/5.3/
- Leaflet.js: https://leafletjs.com/
- Azure AD B2C: https://docs.microsoft.com/en-us/azure/active-directory-b2c/
