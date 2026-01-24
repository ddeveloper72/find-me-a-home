"""
Test accessing Property.ie RSS feeds with different User-Agent headers
"""
import requests
import xml.etree.ElementTree as ET

# Test different User-Agents
user_agents = {
    'RSS Reader': 'Mozilla/5.0 (compatible; NewsBlur Feed Fetcher - http://www.newsblur.com)',
    'Firefox': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
    'Chrome': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Feedparser': 'FeedParser/6.0.10 +https://github.com/kurtmckee/feedparser/'
}

# Test URL - Dublin for sale
test_url = 'https://rss.property.ie/property-for-sale/dublin/'

print("Testing Property.ie RSS feed access...\n")

for name, ua in user_agents.items():
    print(f"Testing with {name}:")
    headers = {
        'User-Agent': ua,
        'Accept': 'application/rss+xml, application/xml, text/xml, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br'
    }
    
    try:
        response = requests.get(test_url, headers=headers, timeout=10)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            # Try to parse as XML
            try:
                root = ET.fromstring(response.content)
                items = root.findall('.//item')
                print(f"  ✓ Success! Found {len(items)} property items")
                
                # Show first property
                if items:
                    first = items[0]
                    title = first.find('title')
                    print(f"  First property: {title.text if title is not None else 'N/A'}")
                break
            except ET.ParseError as e:
                print(f"  × Parse error: {e}")
        else:
            print(f"  × Failed: {response.reason}")
            
    except Exception as e:
        print(f"  × Error: {e}")
    
    print()
