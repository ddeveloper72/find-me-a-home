# Find Me a Home - Ireland

A comprehensive web application to help find homes for sale in Ireland with integrated information about nearby secondary schools and transport options.

## Features

- 🏠 **Property Listings**: Browse properties from multiple sources across Ireland
- 🎓 **School Information**: Detailed info about nearby secondary schools
- 🚆 **Transport Options**: Real-time transport information for trains and buses
- 🔔 **Smart Alerts**: Get notified when new properties match your criteria
- ❤️ **Favorites & Rankings**: Save and rank your favorite properties
- 🗺️ **Interactive Maps**: Visualize properties, schools, and transport on maps
- 🔐 **Secure Authentication**: Azure AD B2C integration

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL
- **Authentication**: Azure AD B2C
- **Frontend**: Bootstrap 5, Leaflet.js
- **APIs**: Irish Rail API, Department of Education data, GTFS-R
- **Hosting**: Heroku

## Setup Instructions

### Prerequisites

- Python 3.11+
- PostgreSQL database
- Azure AD B2C tenant (for authentication)
- API keys (Google Maps, if using geocoding)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd "Find me a home"
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   - Copy `.env.example` to `.env`
   - Update with your credentials:
     - Database URL
     - Azure AD B2C settings
     - API keys
     - Email configuration

5. **Initialize database**
   ```bash
   python
   >>> from app import app, db
   >>> with app.app_context():
   >>>     db.create_all()
   >>> exit()
   ```

6. **Load initial data** (optional)
   ```bash
   python scripts/load_data.py
   ```

7. **Run the application**
   ```bash
   python app.py
   ```

   Visit http://localhost:5000

## Deployment to Heroku

1. **Create Heroku app**
   ```bash
   heroku create your-app-name
   ```

2. **Add PostgreSQL addon**
   ```bash
   heroku addons:create heroku-postgresql:mini
   ```

3. **Set environment variables**
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set AZURE_AD_CLIENT_ID=your-client-id
   # ... set all other environment variables
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

5. **Initialize database**
   ```bash
   heroku run python
   >>> from app import app, db
   >>> with app.app_context():
   >>>     db.create_all()
   ```

## Project Structure

```
Find me a home/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── requirements.txt       # Python dependencies
├── Procfile              # Heroku configuration
├── runtime.txt           # Python version
├── .env.example          # Environment variables template
├── routes/               # Blueprint routes
│   ├── auth.py          # Authentication routes
│   ├── properties.py    # Property routes
│   ├── schools.py       # School routes
│   ├── transport.py     # Transport routes
│   └── search.py        # Search routes
├── services/             # Business logic
│   ├── property_service.py
│   ├── school_service.py
│   ├── transport_service.py
│   ├── location_service.py
│   └── search_service.py
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── dashboard.html
│   └── ... (more templates)
└── static/               # Static files
    ├── css/
    │   └── styles.css
    └── js/
        └── scripts.js
```

## Data Sources

- **Properties**: MyHome.ie, Daft.ie, Property.ie (requires scraping or third-party service)
- **Schools**: [Department of Education ArcGIS](https://education-statistics-doeirl.hub.arcgis.com/)
- **Transport**: 
  - [Irish Rail API](http://api.irishrail.ie/)
  - [GTFS-R Real-time Data](https://data.gov.ie/)

## API Integration Notes

### Property Listings
The major Irish property websites (Daft.ie, MyHome.ie) don't provide public APIs. You'll need to either:
- Use web scraping (check their robots.txt and terms of service)
- Use a third-party service that aggregates property data
- Manually add sample data for testing

### Schools Data
The Department of Education provides data through ArcGIS REST API. The implementation in `services/school_service.py` fetches this data.

### Transport Data
- Irish Rail provides a free XML API
- Bus and LUAS data available through GTFS-R (requires API key from data.gov.ie)

## Next Steps

1. **Implement property data scraping** or integrate with a property data service
2. **Set up Azure AD B2C** tenant and configure authentication
3. **Add background jobs** for periodic data updates (using APScheduler)
4. **Implement email alerts** for saved searches
5. **Add more detailed property templates** with image galleries
6. **Implement advanced search filters**
7. **Add unit tests**

## Contributing

This is a personal project, but suggestions and improvements are welcome!

## License

Personal use only.

## Contact

GitHub: [@ddeveloper72](https://github.com/ddeveloper72)
```

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running
- Check DATABASE_URL in .env
- Verify database credentials

### Authentication Issues
- Verify Azure AD B2C configuration
- Check redirect URLs match your application URL
- Ensure all required scopes are configured

### API Rate Limiting
- Irish Rail API has rate limits
- Implement caching for frequently accessed data
- Consider background jobs for data updates

## Future Enhancements

- [ ] Mobile app version
- [ ] Price prediction using ML
- [ ] Commute time calculator
- [ ] School comparison tool
- [ ] Mortgage calculator integration
- [ ] Virtual property tours
- [ ] Community ratings and reviews
