"""Quick test to check schools CSV download"""
import requests

url = "https://www.education.ie/en/Publications/Statistics/Data-on-Individual-Schools/Education-UT-post_primaryEducation-IE-DepartmentofEducationAndSkills-Post-PrimarySchoolsLocations2016-2017_080617.csv"

print(f"Testing URL: {url}")
print()

try:
    response = requests.get(url, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Content Type: {response.headers.get('content-type')}")
    print(f"Content Length: {len(response.content)} bytes")
    print()
    
    if response.status_code == 200:
        # Try to parse first few lines
        lines = response.text.split('\n')[:5]
        print("First 5 lines:")
        for i, line in enumerate(lines, 1):
            print(f"{i}: {line[:100]}")
    else:
        print("Failed to download")
        print(f"Response: {response.text[:500]}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
