# refresh_trakt_token.py
import requests
import os
import sys

CLIENT_ID = os.getenv('TRAKT_CLIENT_ID')
CLIENT_SECRET = os.getenv('TRAKT_CLIENT_SECRET')
REFRESH_TOKEN = os.getenv('TRAKT_REFRESH_TOKEN')
OUTPUT = os.getenv('GITHUB_OUTPUT')
if not OUTPUT:
    print('Run this helper through GitHub Actions; tokens are not printed.', file=sys.stderr)
    sys.exit(1)

# This redirect_uri must match EXACTLY what you set in your Trakt API App settings
# For device auth, it's typically 'urn:ietf:wg:oauth:2.0:oob'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
    print("Error: Missing one or more required environment variables (TRAKT_CLIENT_ID, TRAKT_CLIENT_SECRET, TRAKT_REFRESH_TOKEN)")
    sys.exit(1)

data = {
    'refresh_token': REFRESH_TOKEN,
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'redirect_uri': REDIRECT_URI,
    'grant_type': 'refresh_token'
}

try:
    response = requests.post('https://api.trakt.tv/oauth/token', json=data, timeout=(5, 25))
except requests.RequestException:
    print('Token refresh request failed.', file=sys.stderr)
    sys.exit(1)

if response.status_code == 200:
    try:
        token_data = response.json()
        new_access_token = token_data['access_token']
        new_refresh_token = token_data['refresh_token']
        if not all(isinstance(value, str) and value and '\n' not in value and '\r' not in value
                   for value in (new_access_token, new_refresh_token)):
            raise ValueError('Invalid token response')
    except (ValueError, KeyError, TypeError):
        print('Invalid token response; reauthorization may be required.', file=sys.stderr)
        sys.exit(1)
    
    print(f'::add-mask::{new_access_token}')
    print(f'::add-mask::{new_refresh_token}')
    with open(OUTPUT, 'a', encoding='utf-8') as handle:
        handle.write(f'access_token={new_access_token}\nrefresh_token={new_refresh_token}\n')
    print("Token refreshed successfully.")
else:
    print(f"Error refreshing token: {response.status_code}")
    sys.exit(1)
