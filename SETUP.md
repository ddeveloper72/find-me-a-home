# Find Me a Home - Application Setup

## ✅ Application Structure Created!

Your "Find Me a Home" application is now set up with a complete structure including:

### Core Components
- ✅ Flask application with blueprints
- ✅ PostgreSQL database models
- ✅ Azure AD B2C authentication
- ✅ RESTful API endpoints
- ✅ Service layer for business logic
- ✅ Responsive Bootstrap 5 frontend
- ✅ Interactive Leaflet maps
- ✅ Heroku deployment configuration

### Features Implemented
1. **Property Listings**
   - Browse and search properties
   - Filter by price, location, bedrooms, type
   - Property detail pages
   - Favorite and rank properties

2. **School Information**
   - List secondary schools
   - Filter by county, type, gender
   - School detail pages
   - Proximity search

3. **Transport Options**
   - Train and bus stations
   - Real-time Irish Rail information
   - Transport proximity search

4. **User Features**
   - User authentication (Azure AD B2C)
   - Save search criteria
   - Set up email alerts
   - Personal dashboard

5. **Maps**
   - Interactive Leaflet maps
   - Property markers (blue)
   - School markers (green)
   - Transport markers (red)

## 🚀 Quick Start

### Option 1: Quick Setup (Recommended for First Time)

```powershell
# 1. Set up Git
.\setup-git.ps1

# 2. Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
# Edit .env file with your settings (start with SQLite for testing)

# 5. Initialize database
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
>>> exit()

# 6. Load sample data
python scripts\load_data.py

# 7. Run the application
python app.py
```

Visit: http://localhost:5000

### Option 2: See Full Instructions
Read [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions including:
- Azure AD B2C configuration
- Heroku deployment
- Troubleshooting
- Development workflow

## 📝 Configuration Needed

Before running the application, you need to configure:

### Minimum (for local testing):
1. **.env file**: Copy `.env.example` to `.env`
2. **SECRET_KEY**: Set a random secret key
3. **DATABASE_URL**: Use SQLite for testing: `sqlite:///findmehome.db`

### For Full Functionality:
4. **Azure AD B2C**: Configure authentication
5. **Google Maps API**: For geocoding (optional)
6. **Email Server**: For alerts (optional)
7. **Data.gov.ie API Key**: For GTFS-R data (optional)

## 📁 Important Files

- **app.py**: Main Flask application
- **models.py**: Database models
- **requirements.txt**: Python dependencies
- **.env.example**: Environment variables template
- **QUICKSTART.md**: Detailed setup guide
- **README.md**: Full documentation

## 🔄 Next Steps

1. **Setup Development Environment**
   ```powershell
   # Follow Quick Start Option 1 above
   ```

2. **Test Locally**
   - Visit http://localhost:5000
   - Browse sample properties
   - View schools and transport data
   - Test search functionality

3. **Configure Authentication**
   - Set up Azure AD B2C tenant
   - Register application
   - Update .env with credentials
   - See QUICKSTART.md for details

4. **Add Property Data**
   - Implement property scraping OR
   - Integrate with property data API OR
   - Continue using sample data for testing

5. **Deploy to Heroku**
   - Create Heroku app
   - Add PostgreSQL addon
   - Configure environment variables
   - Push and deploy
   - See QUICKSTART.md for full instructions

## 🛠️ Technology Stack

- **Backend**: Flask, SQLAlchemy, PostgreSQL
- **Frontend**: Bootstrap 5, Leaflet.js, Font Awesome
- **Auth**: Azure AD B2C with MSAL
- **APIs**: Irish Rail, Department of Education ArcGIS
- **Hosting**: Heroku
- **Maps**: Leaflet.js with OpenStreetMap

## 📚 Resources

- [QUICKSTART.md](QUICKSTART.md) - Quick setup guide
- [README.md](README.md) - Full documentation
- [.github/instructions/copilot-instructions.md](.github/instructions/copilot-instructions.md) - Architecture details

## ⚠️ Important Notes

1. **Property Data**: The major Irish property websites (Daft.ie, MyHome.ie) don't have public APIs. You'll need to either:
   - Implement web scraping (check their terms of service)
   - Use a third-party property data service
   - Continue with sample data for testing

2. **API Keys**: Some features require API keys:
   - GTFS-R (bus/LUAS data): Register at data.gov.ie
   - Google Maps (geocoding): Get from Google Cloud Console

3. **Production Ready**: Before deploying to production:
   - Change all secret keys
   - Enable HTTPS
   - Configure proper email server
   - Set up monitoring and logging
   - Review Azure AD B2C security settings

## 🎯 Features Summary

| Feature | Status | Notes |
|---------|--------|-------|
| Property Listings | ✅ Ready | Sample data provided |
| School Information | ✅ Ready | Auto-loads from gov API |
| Transport Data | ✅ Ready | Irish Rail API integrated |
| User Authentication | ✅ Ready | Requires Azure AD B2C config |
| Search & Filters | ✅ Ready | Multi-criteria search |
| Saved Searches | ✅ Ready | Requires authentication |
| Favorites | ✅ Ready | Requires authentication |
| Interactive Maps | ✅ Ready | Leaflet.js integration |
| Email Alerts | 🔄 Pending | Needs email config |
| Real-time Bus Data | 🔄 Pending | Needs GTFS-R API key |
| Property Scraping | 🔄 Pending | Custom implementation needed |

## 📞 Support

For issues or questions:
1. Check QUICKSTART.md troubleshooting section
2. Review Flask/Heroku logs for errors
3. Verify environment variables are set correctly
4. Check Azure AD B2C configuration

---

**Ready to start?** Run the Quick Start commands above and visit http://localhost:5000!

Good luck with your home search! 🏠🍀
