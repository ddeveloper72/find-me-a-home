# Daft.ie API Setup Guide

## Overview
This application uses the Daft.ie SOAP API to fetch real property listings for sale in Ireland.

## API Access

### Personal Use
- **Daily Limit**: 1,000 requests per 24 hours
- **Cost**: Free for personal accounts
- **Data Access**: Some restrictions vs commercial (see API docs)
- **Limit Increases**: Available on request

### Getting Your API Key

1. **Register/Login to Daft.ie**
   - Go to https://api.daft.ie/
   - Look for registration or "Get Started" link
   - Create account or login with existing Daft.ie account

2. **Request API Key**
   - Contact Daft.ie to request personal developer API key
   - Mention you're building a personal property search application
   - Wait for email with your API key

3. **Add to Environment**
   ```bash
   # In your .env file
   DAFT_API_KEY=your-api-key-here
   ```

## Usage

### Basic Import
Import properties from Daft.ie (default: 100 results):
```bash
python scripts/import_daft_properties.py
```

### Filter by County
Import properties from specific county:
```bash
python scripts/import_daft_properties.py --county Dublin
python scripts/import_daft_properties.py --county Cork
python scripts/import_daft_properties.py --county Galway
```

### Filter by Price Range
```bash
python scripts/import_daft_properties.py --max-price 400000
python scripts/import_daft_properties.py --min-price 200000 --max-price 500000
```

### Filter by Bedrooms
```bash
python scripts/import_daft_properties.py --min-beds 3
python scripts/import_daft_properties.py --min-beds 2 --max-beds 4
```

### Filter by Property Type
```bash
python scripts/import_daft_properties.py --type house
python scripts/import_daft_properties.py --type apartment
```

### Combined Filters
```bash
# 3+ bed houses in Dublin under €500k
python scripts/import_daft_properties.py --county Dublin --type house --min-beds 3 --max-price 500000

# 2-bed apartments in Cork
python scripts/import_daft_properties.py --county Cork --type apartment --min-beds 2 --max-beds 2
```

### Import More Results
```bash
python scripts/import_daft_properties.py --max-results 500
```

## Data Retrieved

The API provides comprehensive property data:
- **Basic Info**: Title, description, price, address
- **Location**: County, city, eircode, latitude, longitude
- **Details**: Bedrooms, bathrooms, property type, floor area
- **Energy**: BER rating
- **Media**: Multiple image URLs
- **Link**: URL to original Daft.ie listing

## Rate Limits

### Personal Account
- **1,000 requests/day** initial limit
- Each search counts as 1 request
- Can request higher limits when needed

### Best Practices
1. **Start Small**: Test with `--max-results 10` first
2. **Use Filters**: Narrow searches to what you need
3. **Schedule Imports**: Run daily/weekly instead of real-time
4. **Cache Data**: Store in database, don't re-fetch unnecessarily

## Updating Properties

The import script automatically:
- **Adds new properties** not in database
- **Updates existing properties** by external_id
- **Tracks changes** with updated_at timestamp

Run periodically to keep listings fresh:
```bash
# Weekly cron job
python scripts/import_daft_properties.py --county Dublin --max-results 500
```

## API Documentation

- **Terms**: https://api.daft.ie/terms/
- **Docs**: https://api.daft.ie/doc/v3/
- **Getting Started**: https://api.daft.ie/gettingstarted/

## Troubleshooting

### "DAFT_API_KEY not found"
- Add key to `.env` file
- Restart Flask application after adding

### "API request failed: 401 Unauthorized"
- Check API key is correct
- Verify key is active (check email from Daft.ie)

### "API request failed: 403 Forbidden"
- Check if you've exceeded daily limit (1,000 requests)
- Contact Daft.ie to request limit increase

### "Found 0 properties"
- Filters might be too restrictive
- Try broader search (remove some filters)
- Check API docs for valid filter values

## Next Steps

Once you have your API key:
1. Add to `.env` file
2. Run test import: `python scripts/import_daft_properties.py --county Dublin --max-results 10`
3. Check database: Should see properties with `source='daft.ie'`
4. Set up regular imports for your target counties
5. Application will automatically show these properties in search results!
