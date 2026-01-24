"""
Test Property.ie RSS feed with feedparser library
"""
import feedparser

# Test URL
test_url = 'https://rss.property.ie/property-for-sale/dublin/'

print("Testing with feedparser library...\n")

# Try with custom agent
feedparser.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"

feed = feedparser.parse(test_url)

print(f"Feed status: {feed.get('status', 'unknown')}")
print(f"Entries found: {len(feed.entries)}")

if feed.entries:
    print("\n✓ SUCCESS! Feed is accessible\n")
    print("First 3 properties:")
    for i, entry in enumerate(feed.entries[:3], 1):
        print(f"\n{i}. {entry.get('title', 'No title')}")
        print(f"   Link: {entry.get('link', 'N/A')}")
        print(f"   Published: {entry.get('published', 'N/A')}")
        
        # Check for geo coordinates
        if hasattr(entry, 'geo_lat'):
            print(f"   Location: {entry.geo_lat}, {entry.geo_long}")
else:
    print("\n× Feed returned no entries")
    if feed.get('bozo'):
        print(f"Error: {feed.get('bozo_exception', 'Unknown error')}")
