# MyHome.ie API Integration

## Overview
This integration uses MyHome.ie's undocumented JSON API to fetch property listings. The API is the same one used by MyHome.ie's website and mobile apps.

## Important Notes

⚠️ **This API is NOT officially documented**
- No public API documentation exists
- No published terms of service for API usage
- Structure may change without notice
- Use responsibly with conservative request rates

✅ **Verified as Legitimate**
- Owned by The Irish Times (DNS: irishtimes.map.fastly.net)
- Uses Fastly CDN (professional infrastructure)
- Returns structured JSON data
- Property IDs match website URLs

## Usage

### Basic Import
Import featured and recently added properties:
```bash
python scripts/import_myhome_properties.py
```

### Limit Results
Import only the first N properties:
```bash
python scripts/import_myhome_properties.py --max-results 50
```

## Data Retrieved

The API provides:
- ✅ **Property Type**: House, Apartment, Bungalow, etc.
- ✅ **Price**: Numeric prices (POA properties stored as €0)
- ✅ **Address**: Full display address
- ✅ **County/City**: Extracted from address
- ✅ **Bedrooms**: Extracted from "X beds" string
- ✅ **Size**: Square meters
- ✅ **BER Rating**: A1-G energy ratings
- ✅ **Images**: Primary property image URL
- ✅ **URL**: Link to MyHome.ie listing page

### Missing Data
The `/home` endpoint does not provide:
- ❌ **Coordinates** (latitude/longitude) - will need geocoding
- ❌ **Property Description** - not in this endpoint
- ❌ **Eircode** - not in this endpoint
- ❌ **Bathrooms** - not in this endpoint
- ❌ **Multiple Images** - only primary image

## API Endpoint

**URL**: `https://api.myhome.ie/home`

**Method**: GET

**Format**: JSON

**Response Structure**:
```json
{
  "Home": {
    "ForSaleFeaturedProperties": [...],
    "ForRentFeaturedProperties": [...],
    "RecentlyAddedProperties": {
      "1": [...],  // Residential for sale
      "3": [...],  // Rentals
      "6": [...]   // Commercial
    },
    "PropertyCountByClass": {
      "1": 11336,   // Residential for sale
      "3": 652,     // Rentals
      "6": 5884     // Commercial
    }
  }
}
```

**Property Object**:
```json
{
  "PropertyId": 4976229,
  "PropertyType": "Semi-Detached House",
  "PriceAsString": "€425,000",
  "DisplayAddress": "11 The Forts, Dooradoyle, Limerick",
  "BedsString": "4 beds",
  "SizeStringMeters": "122",
  "EnergyRatingMediaPath": "https://photos-a.propertyimages.ie/static/images/energyRating/B3.png",
  "BrochureUrl": "/residential/brochure/11-the-forts-dooradoyle-limerick/4976229",
  "SetImageForCache": "https://photos-a.propertyimages.ie/media/9/2/2/4976229/05d619a6-4339-4228-9159-558e5d600689_l.jpg",
  "PropertyClassId": 1,
  "IsTransact": false
}
```

## Property Class IDs

- **1**: Residential for sale (what we import)
- **3**: Rentals
- **6**: Commercial
- **Other**: Various specialty categories

## Import Behavior

The script automatically:
- ✅ **Adds new properties** by PropertyId
- ✅ **Updates existing properties** if price changes
- ✅ **Skips unchanged properties** to avoid duplicates
- ✅ **Filters to residential only** (PropertyClassId=1)
- ✅ **Extracts BER ratings** from image URLs
- ✅ **Parses addresses** to extract county/city
- ✅ **Handles POA prices** as €0

## Best Practices

### Rate Limiting
- The API has no documented rate limits
- **Be conservative**: Don't hammer the API
- **Recommended**: Run import once per day maximum
- **Add delays**: Script should include reasonable delays

### Data Freshness
```bash
# Daily import via cron
0 2 * * * cd /path/to/project && python scripts/import_myhome_properties.py
```

### Geocoding Follow-up
Since coordinates aren't provided:
```bash
# After importing, geocode addresses
python scripts/geocode_properties.py --source myhome.ie
```

## Comparison with Other APIs

| Feature | MyHome.ie | Daft.ie | Sample Data |
|---------|-----------|---------|-------------|
| **Access** | Undocumented | Personal key required | Generated |
| **Coordinates** | ❌ No | ✅ Yes | ✅ Yes |
| **Descriptions** | ❌ No | ✅ Yes | ✅ Yes |
| **Images** | ✅ One | ✅ Multiple | ✅ Multiple |
| **BER Rating** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Reliability** | ⚠️ May change | ✅ Stable | ✅ Stable |
| **Properties** | ~11,000 | Full listings | 103 |

## Troubleshooting

### "No properties fetched"
- API structure may have changed
- Check if https://api.myhome.ie/home returns JSON
- Verify internet connection

### "Database commit failed"
- Check database is running
- Verify property model matches data structure
- Check for duplicate external_ids with different sources

### Properties show as €0
- These are "POA" (Price on Application) listings
- Filter them out in searches if desired:
  ```python
  properties = Property.query.filter(Property.price > 0)
  ```

## Next Steps

1. **Import properties**:
   ```bash
   python scripts/import_myhome_properties.py
   ```

2. **Geocode addresses** (for map functionality):
   ```bash
   python scripts/geocode_properties.py --source myhome.ie
   ```

3. **View in app**:
   - Properties will appear in search results
   - Filter by "MyHome.ie" in data source dropdown
   - Dashboard shows property count by source

4. **Monitor for changes**:
   - API structure could change anytime
   - Test periodically
   - Have fallback to Daft.ie API when key arrives

## Alternative: Daft.ie API

For a more reliable, documented API:
- See `DAFT_API_SETUP.md`
- Request personal developer API key
- Free for personal use (1,000 req/day)
- Includes coordinates, descriptions, more data
