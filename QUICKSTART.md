# Find Me a Home - Quick Start Guide

## Prerequisites
- Python 3.11 installed
- PostgreSQL installed (or use SQLite for local development)
- Git installed
- Azure AD B2C tenant (optional for testing - can skip auth initially)

## Quick Setup (5 minutes)

### 1. Set Up Virtual Environment
```powershell
# Navigate to project directory
cd "c:\Users\Duncan\VS_Code_Projects\Find me a home"

# Create virtual environment
python -m venv .venv

# Activate it
.\.venv\Scripts\activate
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Configure Environment
```powershell
# Copy the example environment file
copy .env.example .env

# Edit .env with your settings
notepad .env
```

**Minimum configuration for local testing:**
```
SECRET_KEY=your-secret-key-here-change-this
DATABASE_URL=sqlite:///findmehome.db
```

### 4. Initialize Database
```powershell
python
```
```python
from app import app, db
with app.app_context():
    db.create_all()
exit()
```

### 5. Load Sample Data
```powershell
python scripts\load_data.py
```

This will:
- ✓ Load school data from Department of Education
- ✓ Load Irish Rail stations
- ✓ Create 3 sample properties

### 6. Run the Application
```powershell
python app.py
```

Visit: **http://localhost:5000**

## Testing Without Authentication

To test without Azure AD B2C, you can temporarily modify `app.py` to create a test user:

```python
# Add this temporary route to app.py for testing
@app.route('/test-login')
def test_login():
    from models import User
    from flask_login import login_user
    
    # Create or get test user
    user = User.query.filter_by(email='test@test.com').first()
    if not user:
        user = User(email='test@test.com', name='Test User')
        db.session.add(user)
        db.session.commit()
    
    login_user(user)
    return redirect(url_for('dashboard'))
```

Then visit `http://localhost:5000/test-login` to login as a test user.

## Azure AD B2C Setup (For Production)

### 1. Create Azure AD B2C Tenant
1. Go to https://portal.azure.com
2. Create a new Azure AD B2C tenant
3. Note your tenant name (e.g., yourtenant.onmicrosoft.com)

### 2. Register Application
1. In Azure AD B2C, go to "App registrations"
2. Click "New registration"
3. Name: "Find Me a Home"
4. Redirect URI: `https://your-app.herokuapp.com/auth/callback`
5. For local testing also add: `http://localhost:5000/auth/callback`
6. Click "Register"

### 3. Create Client Secret
1. Go to "Certificates & secrets"
2. Click "New client secret"
3. Copy the secret value (you won't see it again!)

### 4. Configure User Flows
1. Go to "User flows"
2. Click "New user flow"
3. Select "Sign up and sign in"
4. Name it: `B2C_1_signupsignin`
5. Enable email signup
6. Select attributes to collect

### 5. Update .env File
```
AZURE_AD_CLIENT_ID=<your-application-id>
AZURE_AD_CLIENT_SECRET=<your-client-secret>
AZURE_AD_TENANT_NAME=<yourtenant>
AZURE_AD_AUTHORITY=https://<yourtenant>.b2clogin.com/<yourtenant>.onmicrosoft.com/B2C_1_signupsignin
```

## Deployment to Heroku

### 1. Install Heroku CLI
Download from: https://devcenter.heroku.com/articles/heroku-cli

### 2. Login to Heroku
```powershell
heroku login
```

### 3. Create Heroku App
```powershell
heroku create find-me-home-ireland
```

### 4. Add PostgreSQL
```powershell
heroku addons:create heroku-postgresql:mini
```

### 5. Set Environment Variables
```powershell
heroku config:set SECRET_KEY=your-production-secret-key
heroku config:set AZURE_AD_CLIENT_ID=your-client-id
heroku config:set AZURE_AD_CLIENT_SECRET=your-client-secret
# ... set all other variables
```

### 6. Initialize Git (if not already done)
```powershell
git init
git add .
git commit -m "Initial commit"
```

### 7. Deploy
```powershell
git push heroku main
```

### 8. Initialize Database on Heroku
```powershell
heroku run python
```
```python
from app import app, db
with app.app_context():
    db.create_all()
exit()
```

### 9. Load Data on Heroku
```powershell
heroku run python scripts/load_data.py
```

### 10. Open Your App
```powershell
heroku open
```

## Common Issues & Solutions

### Issue: Module not found
```powershell
# Make sure virtual environment is activated
.\.venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Database errors
```powershell
# Drop and recreate database
python
```
```python
from app import app, db
with app.app_context():
    db.drop_all()
    db.create_all()
exit()
```

### Issue: Port already in use
```python
# In app.py, change the port:
if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Changed from 5000
```

### Issue: Azure AD authentication fails
- Check redirect URLs in Azure AD B2C match your application URL
- Verify client secret hasn't expired
- Ensure authority URL is correct

## Development Workflow

1. **Make changes to code**
2. **Run the app**: `python app.py`
3. **Test in browser**: http://localhost:5000
4. **Check for errors**: Look at terminal output
5. **Commit changes**: 
   ```powershell
   git add .
   git commit -m "Description of changes"
   ```
6. **Deploy to Heroku**:
   ```powershell
   git push heroku main
   ```

## Useful Commands

### Database Management
```powershell
# View all users
python -c "from app import app, db; from models import User; app.app_context().push(); print(User.query.all())"

# View all properties
python -c "from app import app, db; from models import Property; app.app_context().push(); print(Property.query.count(), 'properties')"

# Clear all data
python -c "from app import app, db; app.app_context().push(); db.drop_all(); db.create_all()"
```

### Heroku Management
```powershell
# View logs
heroku logs --tail

# Run Python shell on Heroku
heroku run python

# Restart app
heroku restart

# View config
heroku config
```

## Next Steps

1. ✅ Set up development environment
2. ✅ Test basic functionality locally
3. ⬜ Configure Azure AD B2C
4. ⬜ Implement property data source
5. ⬜ Set up email alerts
6. ⬜ Deploy to Heroku
7. ⬜ Test production environment
8. ⬜ Add custom domain (optional)

## Resources

- **Flask Documentation**: https://flask.palletsprojects.com/
- **Bootstrap**: https://getbootstrap.com/docs/5.3/
- **Leaflet**: https://leafletjs.com/
- **Heroku Docs**: https://devcenter.heroku.com/
- **Azure AD B2C**: https://docs.microsoft.com/en-us/azure/active-directory-b2c/

## Need Help?

- Check the README.md for detailed information
- Review copilot-instructions.md for architecture details
- Check Flask logs for error messages
- Use Heroku logs for production debugging

Happy house hunting! 🏠
