# Local Data Directory

This directory stores downloaded school data files.

## Files

- `primary_schools_2025_2026.xlsx` - Primary schools Excel file from Department of Education
- `post_primary_schools_2025_2026.xlsx` - Post-primary schools Excel file  
- `primary_schools_2025_2026.csv` - Converted CSV for easier processing
- `post_primary_schools_2025_2026.csv` - Converted CSV for easier processing

## Source

Data downloaded from:
- Primary: https://assets.gov.ie/static/documents/d85298b3/Data_on_Individual_Schools_Mainstream_preliminary_2025-2026.xlsx
- Post-Primary: https://assets.gov.ie/static/documents/c409b1b1/Data_on_Individual_Schools_PPOD_preliminary_2025-2026.xlsx

Run `python scripts/import_schools.py` to download and import data.

## Geolocation for Schools

The Department of Education CSV files do not include latitude/longitude for most schools,
so run geocoding after import:

- `python scripts/geocode_schools.py --test 50` (safe test batch)
- `python scripts/geocode_schools.py` (full run)

Provider order for geocoding is:
1. GeoDirectory API (`GEOADDRESS_CHECKED_API_TOKEN`)
2. Google Geocoding API (`GOOGLE_MAPS_API_KEY`)
3. Nominatim fallback (no key required)

**Note**: These files are not tracked in Git due to their size. They will be downloaded automatically when running the import script.
