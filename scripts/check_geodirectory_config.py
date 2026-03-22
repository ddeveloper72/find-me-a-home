"""Check if GeoDirectory API token is configured"""
import os
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

GEODIRECTORY_TOKEN = os.getenv('GEOADDRESS_CHECKED_API_TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

print("="*70)
print("GEODIRECTORY CONFIGURATION CHECK")
print("="*70)
print()
print("Environment Variables:")
print(f"  GEOADDRESS_CHECKED_API_TOKEN: {'✓ Configured' if GEODIRECTORY_TOKEN else '✗ Not set (empty)'}")
print(f"  GOOGLE_MAPS_API_KEY:          {'✓ Configured' if GOOGLE_API_KEY else '✗ Not set'}")
print()
print("Geocoding Provider Priority:")
if GEODIRECTORY_TOKEN:
    print("  1. ✓ GeoDirectory (PREFERRED - most accurate for Irish addresses)")
    print("  2. ✓ Google Maps (fallback)")
    print("  3. ✓ Nominatim (final fallback)")
elif GOOGLE_API_KEY:
    print("  1. ✗ GeoDirectory (disabled - no token)")
    print("  2. ✓ Google Maps (ACTIVE)")
    print("  3. ✓ Nominatim (fallback)")
else:
    print("  1. ✗ GeoDirectory (disabled - no token)")
    print("  2. ✗ Google Maps (disabled - no key)")
    print("  3. ✓ Nominatim (ACTIVE - free but slower)")
print()
print("Next Steps:")
if not GEODIRECTORY_TOKEN:
    print("  → Waiting for GeoDirectory token from info@geodirectory.ie")
    print("  → Once received, add to .env: GEOADDRESS_CHECKED_API_TOKEN=your-token-here")
    print("  → Then run: python scripts/geocode_schools.py --test 10")
else:
    print("  → Ready to geocode! Run: python scripts/geocode_schools.py --test 10")
print()
print("="*70)
