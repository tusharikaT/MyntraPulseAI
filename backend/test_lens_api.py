import requests
import json

base_url = "http://127.0.0.1:8000/api/lens/records"

def test_api():
    print("Testing no filters...")
    r = requests.get(base_url, params={'page': 1, 'limit': 12})
    print(f"No filters: {len(r.json().get('data', []))} records, Total: {r.json().get('pagination', {}).get('total')}")

    print("Testing source_type='Reddit'...")
    r = requests.get(base_url, params={'page': 1, 'limit': 12, 'source_type': 'Reddit'})
    print(f"Reddit filter: {len(r.json().get('data', []))} records, Total: {r.json().get('pagination', {}).get('total')}")

    print("Testing source_type='' (empty string)...")
    r = requests.get(base_url, params={'page': 1, 'limit': 12, 'source_type': ''})
    print(f"Empty source_type: {len(r.json().get('data', []))} records, Total: {r.json().get('pagination', {}).get('total')}")

if __name__ == "__main__":
    test_api()
