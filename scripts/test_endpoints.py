"""
Comprehensive Endpoint Testing Script
Tests all application endpoints and reports errors
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app, db
from models import User
from flask import url_for
import traceback

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def create_test_user():
    """Create or get test user for authenticated endpoints"""
    with app.app_context():
        user = User.query.filter_by(email='test@test.com').first()
        if not user:
            user = User(email='test@test.com', name='Test User')
            db.session.add(user)
            db.session.commit()
        return user

def test_endpoint(client, method, url, auth_required=False, expected_status=200, description=""):
    """Test a single endpoint"""
    try:
        if method == 'GET':
            response = client.get(url, follow_redirects=False)
        elif method == 'POST':
            response = client.post(url, follow_redirects=False)
        else:
            response = client.get(url, follow_redirects=False)
        
        # Check status code
        status_ok = response.status_code == expected_status
        
        # 308 Permanent Redirect is OK for trailing slash redirects
        if response.status_code == 308 and expected_status == 200:
            print(f"  {GREEN}✓{RESET} {method:4} {url:50} → 308 (trailing slash redirect)")
            return True
        
        # Check for template errors in HTML
        template_error = False
        if response.content_type and 'text/html' in response.content_type:
            html = response.data.decode('utf-8', errors='ignore')
            if 'TemplateNotFound' in html or 'Jinja2Error' in html or 'UndefinedError' in html:
                template_error = True
        
        # Determine result
        if status_ok and not template_error:
            print(f"  {GREEN}✓{RESET} {method:4} {url:50} → {response.status_code}")
            return True
        elif response.status_code in [301, 302] and not auth_required:
            print(f"  {YELLOW}↻{RESET} {method:4} {url:50} → {response.status_code} (redirect)")
            return True
        elif response.status_code == 302 and auth_required:
            print(f"  {YELLOW}⚠{RESET} {method:4} {url:50} → {response.status_code} (needs auth)")
            return True
        elif template_error:
            print(f"  {RED}✗{RESET} {method:4} {url:50} → Template Error!")
            return False
        else:
            print(f"  {RED}✗{RESET} {method:4} {url:50} → {response.status_code} (expected {expected_status})")
            return False
            
    except Exception as e:
        print(f"  {RED}✗{RESET} {method:4} {url:50} → Exception: {str(e)[:50]}")
        return False

def main():
    """Run comprehensive endpoint tests"""
    print("="*80)
    print(f"{BLUE}Find Me a Home - Endpoint Testing Suite{RESET}")
    print("="*80)
    print()
    
    with app.app_context():
        # Create test client
        client = app.test_client()
        
        # Test user for authenticated tests
        test_user = create_test_user()
        
        results = {
            'passed': 0,
            'failed': 0,
            'total': 0
        }
        
        # Define all endpoints to test
        tests = [
            # Core routes
            ('GET', '/', False, 200, "Home page"),
            ('GET', '/test-login', False, 302, "Test login (redirects)"),
            ('GET', '/dashboard', True, [200, 302], "Dashboard (may need auth)"),
            
            # Properties
            ('GET', '/properties', False, 200, "Properties list"),
            ('GET', '/properties/1', False, [200, 404], "Property detail"),
            ('GET', '/properties/1/feasibility', True, [200, 302, 404], "Property feasibility"),
            ('GET', '/properties/refresh', False, 200, "Refresh properties"),
            
            # Schools
            ('GET', '/schools', False, 200, "Schools list"),
            ('GET', '/schools/1', False, [200, 404], "School detail"),
            ('GET', '/schools/nearby?lat=53.3&lon=-6.3', False, 200, "Nearby schools with coords"),
            
            # Transport
            ('GET', '/transport', False, 200, "Transport list"),
            ('GET', '/transport/1', False, [200, 404], "Transport detail"),
            ('GET', '/transport/nearby?lat=53.3&lon=-6.3', False, 200, "Nearby transport with coords"),
            ('GET', '/transport/autocomplete', False, 200, "Transport autocomplete"),
            
            # Search
            ('GET', '/search', False, 200, "Search form"),
            ('GET', '/search/results', False, 200, "Search results"),
            ('GET', '/search/saved', True, [200, 302], "Saved searches (may need auth)"),
            
            # Financial
            ('GET', '/financial/profile', True, [200, 302], "Financial profile"),
            ('GET', '/financial/summary', True, [200, 302], "Financial summary"),
            
            # Auth
            ('GET', '/auth/login', False, [200, 302], "Login page"),
            ('GET', '/auth/logout', False, 302, "Logout (redirects)"),
        ]
        
        # Run tests by category
        categories = {
            'Core': [],
            'Properties': [],
            'Schools': [],
            'Transport': [],
            'Search': [],
            'Financial': [],
            'Auth': []
        }
        
        for test in tests:
            method, url, auth_req, expected, desc = test
            
            # Determine category
            if url.startswith('/properties'):
                category = 'Properties'
            elif url.startswith('/schools'):
                category = 'Schools'
            elif url.startswith('/transport'):
                category = 'Transport'
            elif url.startswith('/search'):
                category = 'Search'
            elif url.startswith('/financial'):
                category = 'Financial'
            elif url.startswith('/auth'):
                category = 'Auth'
            else:
                category = 'Core'
            
            categories[category].append(test)
        
        # Test each category
        for category, tests in categories.items():
            if not tests:
                continue
                
            print(f"\n{BLUE}Testing {category} Endpoints{RESET}")
            print("-" * 80)
            
            for method, url, auth_req, expected, desc in tests:
                # Handle multiple expected status codes
                if isinstance(expected, list):
                    # Test with first expected status
                    success = False
                    for exp_status in expected:
                        if test_endpoint(client, method, url, auth_req, exp_status, desc):
                            success = True
                            break
                    
                    if success:
                        results['passed'] += 1
                    else:
                        results['failed'] += 1
                else:
                    if test_endpoint(client, method, url, auth_req, expected, desc):
                        results['passed'] += 1
                    else:
                        results['failed'] += 1
                
                results['total'] += 1
        
        # Summary
        print()
        print("="*80)
        print(f"{BLUE}Test Summary{RESET}")
        print("="*80)
        print(f"Total Tests: {results['total']}")
        print(f"{GREEN}Passed: {results['passed']}{RESET}")
        print(f"{RED}Failed: {results['failed']}{RESET}")
        print(f"Success Rate: {(results['passed']/results['total']*100):.1f}%")
        print()
        
        if results['failed'] > 0:
            print(f"{YELLOW}⚠ Some endpoints have issues. Review failed tests above.{RESET}")
            print()
            print("Common issues:")
            print("  - Template not found: Missing or misnamed template file")
            print("  - Jinja2 error: Variable undefined or syntax error in template")
            print("  - 404: Route not registered or resource doesn't exist")
            print("  - 500: Server error, check app logs for details")
        else:
            print(f"{GREEN}✓ All endpoints working correctly!{RESET}")
        
        print("="*80)
        
        return 0 if results['failed'] == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
