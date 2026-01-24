"""
Test Property.ie base RSS feed
"""
import feedparser
import requests

# Test base URL
test_url = 'https://rss.property.ie/property-for-sale/'

print(f"Testing: {test_url}\n")

# Try with feedparser
print("1. Testing with feedparser:")
feedparser.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
feed = feedparser.parse(test_url)
print(f"   Status: {feed.get('status', 'unknown')}")
print(f"   Entries: {len(feed.entries)}")

if feed.entries:
    print("\n   ✓ SUCCESS!\n")
    for i, entry in enumerate(feed.entries[:3], 1):
        print(f"   {i}. {entry.get('title', 'No title')}")
        print(f"      Link: {entry.get('link', 'N/A')}")
else:
    print(f"   Error: {feed.get('bozo_exception', 'No entries')}")

# Try with requests
print("\n2. Testing with requests:")
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
}
response = requests.get(test_url, headers=headers, timeout=10)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    print(f"   Content length: {len(response.content)} bytes")
    print(f"   Content type: {response.headers.get('content-type', 'unknown')}")
