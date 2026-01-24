# Property Data Sources for Ireland

## Summary of Findings (January 2026)

### RSS Feeds
**Property.ie** - Has RSS feeds but blocks automated access (403 Forbidden)
- URLs: `https://rss.property.ie/property-for-sale/{county}/`
- Data includes: Price, beds, baths, type, agent, **latitude/longitude**
- Format: XML with geo namespace
- **Issue**: Requires browser session/cookies to access

**Daft.ie** - No RSS endpoint found
**MyHome.ie** - No RSS endpoint found

### Public APIs
- **None found** - All major Irish property sites lack public APIs
- Commercial APIs exist (PropertyData.ie, Reapit) but are paid services

### Web Scraping Options

**Property.ie**
- Clean HTML structure
- Listings at: `/property-for-sale/{area}/`
- Geocoded data available
- ⚠️ Check robots.txt and terms of service

**Daft.ie**  
- JSON data embedded in pages
- Listings at: `/property-for-sale/ireland/`
- Modern React/Next.js site
- ⚠️ Dynamic content, may need Selenium/Playwright

**MyHome.ie**
- Standard property listing structure
- Listings at: `/residential/{county}/property-for-sale/`
- ⚠️ Check terms before scraping

### Recommendations

**For Development/Testing:**
1. ✅ **Generate sample data** - Create realistic test properties
2. ✅ **Manual CSV import** - Upload curated property lists
3. ⚠️ **Browser automation** - Use Playwright to access RSS feeds with session

**For Production:**
1. **Partner with estate agents** - Direct data feeds
2. **Commercial API** - PropertyData.ie or similar
3. **Web scraping** - With proper rate limiting and compliance
   - Respect robots.txt
   - Review terms of service  
   - Use polite crawling (delays, user-agent)
   - Cache responsibly

### Legal Considerations
- Most Irish property sites prohibit automated scraping in their terms
- Database copyright applies in Ireland/EU
- Consider:
  - Fair use for research/development
  - Attribution requirements
  - Commercial vs personal use
  - Frequency of access

### Next Steps
1. **Create sample data generator** (immediate - for development)
2. **Implement web scraper template** (structure ready, use responsibly)
3. **Schedule for geocoding schools** (when convenient)
4. **Explore commercial APIs** (for production deployment)
