"""Print the latest episode using the same validated client as the widget."""
import os
import sys
from dotenv import load_dotenv
from images import AuthError, FetchError, fetch_last_watched


def main():
    load_dotenv()
    client, token = os.getenv('TRAKT_CLIENT_ID'), os.getenv('TRAKT_ACCESS_TOKEN')
    if not client or not token:
        print('Set TRAKT_CLIENT_ID and TRAKT_ACCESS_TOKEN.')
        return 1
    try:
        item = fetch_last_watched('episodes', {'trakt-api-version': '2',
                                  'trakt-api-key': client, 'Authorization': f'Bearer {token}'})
        if item:
            print(f"Last watched show: {item['show']['title']}")
            print(f"Episode: {item['episode'].get('title', 'Untitled')}")
            print(f"Watched at: {item['watched_at']}")
        else:
            print('No episode watch history found.')
    except AuthError as exc:
        print(str(exc), file=sys.stderr)
        return 10
    except FetchError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
