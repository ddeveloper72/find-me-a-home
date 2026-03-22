# GeoDirectory API Setup Guide

## Quick Start - When You Receive Your Token

1. **Add token to `.env` file:**
   ```bash
   # Open .env and update this line:
   GEOADDRESS_CHECKED_API_TOKEN=paste-your-token-here
   ```

2. **Verify configuration:**
   ```bash
   python scripts/check_geodirectory_config.py
   ```
   You should see "✓ Configured" next to GEOADDRESS_CHECKED_API_TOKEN

3. **Test with a small batch:**
   ```bash
   python scripts/geocode_schools.py --test 10 --provider auto
   ```
   This geocodes 10 schools and shows which provider was used.

4. **Run full geocoding:**
   ```bash
   python scripts/geocode_schools.py --provider auto
   ```
   This will geocode all ~3,700 schools (takes 1-2 hours with rate limiting).

## Provider Priority

The geocoding script uses this fallback order:

1. **GeoDirectory** (if token configured) - Most accurate for Irish addresses
2. **Google Maps** (if API key configured) - Excellent Eircode support
3. **Nominatim** (always available) - Free OpenStreetMap service

## What to Expect

With GeoDirectory token:
- **Expected success rate:** 95-98% (nearly all schools have Eircodes)
- **Speed:** ~1-2 seconds per school (API rate limits)
- **Coverage:** Best for Irish addresses and Eircodes
- **Cost:** Free trial tier (check your token limits)

Example output:
```
[1/10] St. Mary's Primary School | D02X285  ✅ 53.279522, -6.099830 [geodirectory]
[2/10] Loreto Abbey Secondary    | A96YC81  ✅ 53.279522, -6.099830 [geodirectory]
```

## Troubleshooting

**Token not working?**
```bash
python scripts/check_geodirectory_config.py
```

**API errors (401/429)?**
- 401: Token invalid or expired - contact info@geodirectory.ie
- 429: Rate limit exceeded - script already has delays, may need to increase

**Low success rate?**
```bash
# Try Google-only to compare
python scripts/geocode_schools.py --test 10 --provider google

# Or force GeoDirectory only to see what fails
python scripts/geocode_schools.py --test 10 --provider geodirectory
```

## Token Details

- **Requested from:** info@geodirectory.ie
- **Purpose:** Educational/personal development
- **Use case:** One-time bulk school geocoding + occasional updates
- **Project:** Find Me a Home (affordable Irish property finder)

## Links

- **GeoDirectory Portal:** https://www.geoaddress-checked.ie/
- **API Documentation:** https://www.geoaddress-checked.ie/ (API guide section)
- **Check tokens:** https://www.geoaddress-checked.ie/tokens (when logged in)
