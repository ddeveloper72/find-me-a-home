from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from models import User
from extensions import db
import os
import uuid

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Azure AD B2C configuration (optional - only needed for production)
CLIENT_ID = os.getenv('AZURE_AD_CLIENT_ID')
CLIENT_SECRET = os.getenv('AZURE_AD_CLIENT_SECRET')
AUTHORITY = os.getenv('AZURE_AD_AUTHORITY')
REDIRECT_PATH = os.getenv('AZURE_AD_REDIRECT_PATH', '/auth/callback')
SCOPE = ["User.Read"]

# Check if Azure AD is configured
AZURE_AD_ENABLED = all([CLIENT_ID, CLIENT_SECRET, AUTHORITY]) and \
                   not CLIENT_ID.startswith('your-') and \
                   not AUTHORITY.startswith('https://your-tenant')

def _build_msal_app(cache=None):
    """Build MSAL app - only works if Azure AD is configured"""
    if not AZURE_AD_ENABLED:
        raise ValueError("Azure AD B2C is not configured. Use /test-login for development.")
    
    # Import msal only when needed
    try:
        import msal
    except ImportError:
        raise ValueError("msal package not available. Use /test-login for development.")
    
    return msal.ConfidentialClientApplication(
        CLIENT_ID, 
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
        token_cache=cache
    )

def _build_auth_url(authority=None, scopes=None, state=None):
    """Build auth URL - only works if Azure AD is configured"""
    if not AZURE_AD_ENABLED:
        raise ValueError("Azure AD B2C is not configured. Use /test-login for development.")
    
    return _build_msal_app().get_authorization_request_url(
        scopes or [],
        state=state or str(uuid.uuid4()),
        redirect_uri=url_for('auth.authorized', _external=True)
    )

@bp.route('/login')
def login():
    """Redirect to Azure AD B2C login"""
    if not AZURE_AD_ENABLED:
        flash('Azure AD B2C is not configured. Using test login for development.', 'warning')
        return redirect(url_for('test_login'))
    
    try:
        session["flow"] = _build_msal_app().initiate_auth_code_flow(
            SCOPE,
            redirect_uri=url_for('auth.authorized', _external=True)
        )
        return redirect(session["flow"]["auth_uri"])
    except Exception as e:
        flash(f'Azure AD login error: {str(e)}. Use /test-login for development.', 'danger')
        return redirect(url_for('index'))

@bp.route('/callback')
def authorized():
    """Handle the redirect from Azure AD B2C"""
    if not AZURE_AD_ENABLED:
        flash('Azure AD B2C is not configured.', 'warning')
        return redirect(url_for('test_login'))
    
    try:
        cache = None
        result = _build_msal_app(cache=cache).acquire_token_by_auth_code_flow(
            session.get("flow", {}),
            request.args
        )
        
        if "error" in result:
            flash(f"Login error: {result.get('error_description')}", 'danger')
            return redirect(url_for('index'))
        
        # Get user info from token
        user_info = result.get("id_token_claims")
        email = user_info.get("emails", [None])[0] or user_info.get("email")
        name = user_info.get("name", "User")
        azure_oid = user_info.get("oid")
        
        # Find or create user
        user = User.query.filter_by(azure_oid=azure_oid).first()
        if not user:
            user = User(
                azure_oid=azure_oid,
                email=email,
                name=name
            )
            db.session.add(user)
            db.session.commit()
        
        # Log user in
        login_user(user)
        flash(f'Welcome, {user.name}!', 'success')
        
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        flash(f'Authentication error: {str(e)}', 'danger')
        return redirect(url_for('index'))

@bp.route('/logout')
@login_required
def logout():
    """Log out the user"""
    logout_user()
    flash('You have been logged out.', 'info')
    
    # Clear Azure AD session only if Azure AD is enabled
    if AZURE_AD_ENABLED and AUTHORITY:
        return redirect(
            AUTHORITY + "/oauth2/v2.0/logout" +
            "?post_logout_redirect_uri=" + url_for('index', _external=True)
        )
    
    # For development/test login, just redirect to index
    return redirect(url_for('index'))
