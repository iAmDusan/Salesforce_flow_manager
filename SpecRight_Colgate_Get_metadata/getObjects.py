import requests

# Constants
API_VERSION = '54.0'
INSTANCE_URL = 'https://specright-9558.my.salesforce.com'
SESSION_ID = '00D6A000000eg1p!AQEAQL6nWAkn_G7ry6SUtAPmUjqMBPs80kDYqYXrnu8LDKELkgyxwYBKXsjdDc401lpdODvj0APpM7qCmD5Dds84ZWxysiqm'

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {SESSION_ID}',
}


def get_all_custom_objects():
    url = f"{INSTANCE_URL}/services/data/v{API_VERSION}/sobjects/"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        sobjects = response.json()['sobjects']
        custom_objects = [obj for obj in sobjects if obj['name'].endswith('__c')]
        return sorted(custom_objects, key=lambda obj: obj['name'])  # Sort by 'name' field
    else:
        print(f"Error retrieving sObjects: {response.text}")
        return []


def filter_custom_objects(custom_objects, patterns):
    """Filters objects starting with any of the provided patterns."""
    filtered_objects = [
        obj for obj in custom_objects
        if any(pattern in obj['name'] for pattern in patterns)
    ]
    return filtered_objects


def main():
    custom_objects = get_all_custom_objects()
    patterns = ['SR_%', 'specright_%', 'Part_']

    filtered_objects = filter_custom_objects(custom_objects, patterns)

    print("Filtered Custom Objects (sorted):")
    for obj in filtered_objects:
        print(obj['name'])


if __name__ == "__main__":
    main()
