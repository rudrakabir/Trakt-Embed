"""Authorize locally using Trakt's device flow. Never print bearer tokens."""
import os
from pathlib import Path
import sys
import time
import requests
from dotenv import load_dotenv, set_key


def main():
    load_dotenv()
    client, secret = os.getenv('TRAKT_CLIENT_ID'), os.getenv('TRAKT_CLIENT_SECRET')
    if not client or not secret:
        print('Set TRAKT_CLIENT_ID and TRAKT_CLIENT_SECRET in .env first.')
        return 1
    try:
        response = requests.post('https://api.trakt.tv/oauth/device/code',
                                 json={'client_id': client}, timeout=(5, 25))
        response.raise_for_status()
        data = response.json()
        deadline = time.monotonic() + data['expires_in']
        interval = max(1, data['interval'])
        print(f"Open {data['verification_url']} and enter: {data['user_code']}")
        while time.monotonic() < deadline:
            time.sleep(interval)
            if time.monotonic() >= deadline:
                break
            response = requests.post('https://api.trakt.tv/oauth/device/token',
                                     json={'code': data['device_code'], 'client_id': client,
                                           'client_secret': secret}, timeout=(5, 25))
            if response.status_code == 200:
                tokens = response.json()
                access, refresh = tokens['access_token'], tokens['refresh_token']
                path = Path('.env')
                path.touch(mode=0o600, exist_ok=True)
                path.chmod(0o600)
                set_key(str(path), 'TRAKT_ACCESS_TOKEN', access)
                set_key(str(path), 'TRAKT_REFRESH_TOKEN', refresh)
                print('Authorized. Tokens saved to .env; keep this file private.')
                return 0
            if response.status_code == 400:
                continue
            if response.status_code == 429:
                interval += 5
                continue
            print(f'Authorization stopped (HTTP {response.status_code}). Start again when ready.')
            return 1
        print('Authorization code expired. Run embed.py again.')
    except (requests.RequestException, ValueError, KeyError, OSError):
        print('Authorization could not be completed. Check your app settings and connection.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
