"""Generate a static widget, preserving the existing file if Trakt fails."""
import argparse
import json
from datetime import datetime, timezone
from html import escape
import os
from pathlib import Path
import sys
import tempfile
from urllib.parse import quote
import requests
from dotenv import load_dotenv

TIMEOUT = (5, 25)


class FetchError(Exception):
    pass


class AuthError(FetchError):
    pass


def fetch_last_watched(kind, headers, session=requests, username='me'):
    try:
        response = session.get(f'https://api.trakt.tv/users/{quote(username, safe="")}/history/{kind}',
                               headers=headers, params={'limit': 1}, timeout=TIMEOUT)
        if response.status_code == 401:
            raise AuthError('Trakt authentication failed. Refresh or reauthorize your token.')
        if response.status_code != 200:
            raise FetchError(f'Trakt history failed (HTTP {response.status_code}).')
        data = response.json()
        if not isinstance(data, list):
            raise FetchError('Invalid Trakt history response.')
        if not data:
            return None
        item = data[0]
        media = 'movie' if kind == 'movies' else 'show'
        if not isinstance(item, dict) or not isinstance(item.get(media), dict):
            raise FetchError('Incomplete Trakt history item.')
        if not item[media].get('title') or not item.get('watched_at'):
            raise FetchError('Missing title or watch date.')
        if kind == 'episodes' and not isinstance(item.get('episode'), dict):
            raise FetchError('Missing episode details.')
        return item
    except (requests.RequestException, ValueError) as exc:
        raise FetchError('Unable to read Trakt history; existing output preserved.') from exc


def get_tmdb_image(media, kind, token, session=requests):
    tmdb_id = (media.get('ids') or {}).get('tmdb')
    if not token or not isinstance(tmdb_id, int) or tmdb_id <= 0:
        return None
    try:
        response = session.get(f'https://api.themoviedb.org/3/{kind}/{tmdb_id}',
                               headers={'Authorization': f'Bearer {token}'}, timeout=TIMEOUT)
        if response.status_code == 200:
            path = response.json().get('poster_path')
            if isinstance(path, str) and path.startswith('/') and not path.startswith('//'):
                return 'https://image.tmdb.org/t/p/w200' + path
    except (requests.RequestException, ValueError, AttributeError):
        pass
    return None


def render_card(item, kind, poster=None):
    label = 'Episode' if kind == 'episodes' else 'Movie'
    if item is None:
        return f'<article class="card empty"><span class="label">{label}</span><p>No watch history yet.</p></article>'
    media = item['show' if kind == 'episodes' else 'movie']
    details = str(media.get('year') or '')
    if kind == 'episodes':
        episode = item['episode']
        season, number = episode.get('season'), episode.get('number')
        code = f'S{season:02d}E{number:02d}' if isinstance(season, int) and isinstance(number, int) else ''
        details = ' · '.join(p for p in [code, str(episode.get('title') or '')] if p)
    try:
        watched = datetime.fromisoformat(item['watched_at'].replace('Z', '+00:00'))
        if watched.tzinfo is None:
            raise ValueError('Missing timezone')
        watched = watched.astimezone(timezone.utc)
    except (ValueError, TypeError, AttributeError) as exc:
        raise FetchError('Invalid watch date; existing output preserved.') from exc
    art = (f'<img class="poster" src="{escape(poster, quote=True)}" alt="" loading="lazy" width="80" height="120">'
           if poster else '<div class="poster placeholder" aria-hidden="true">▶</div>')
    return (f'<article class="card">{art}<div class="details"><span class="label">{label}</span>'
            f'<h2>{escape(str(media["title"]))}</h2><p>{escape(details)}</p>'
            f'<time datetime="{watched.isoformat()}">Watched {watched:%d %b %Y · %H:%M UTC}</time></div></article>')


def render_html(show, movie, posters=(None, None), fragment=False):
    style = Path(__file__).with_name('widget.css').read_text(encoding='utf-8')
    body = ('<style>' + style + '</style><section class="trakt-embed" aria-label="Recent watch history">'
            '<header><h1>Recently watched</h1><span class="badge">Trakt</span></header>'
            + render_card(show, 'episodes', posters[0]) + render_card(movie, 'movies', posters[1])
            + '<footer>Watch history from <a href="https://trakt.tv">Trakt</a>. '
            'Artwork from <a href="https://www.themoviedb.org">TMDB</a>.<br>'
            'This product uses the TMDB API but is not endorsed or certified by TMDB.</footer></section>')
    if fragment:
        return body + '\n'
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Recently watched · Trakt</title></head><body>' + body + '</body></html>\n')


def write_atomic(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as temp:
        name = temp.name
        temp.write(content)
    try:
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def main(argv=None):
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='trakt_embed.html')
    parser.add_argument('--fragment', action='store_true', help='Generate an HTML fragment for Jekyll')
    parser.add_argument('--username', default=os.getenv('TRAKT_USERNAME', 'me'), help='Public Trakt username; me uses OAuth')
    parser.add_argument('--json-output', help='Also publish a minimal public JSON feed')
    args = parser.parse_args(argv)
    client, token = os.getenv('TRAKT_CLIENT_ID'), os.getenv('TRAKT_ACCESS_TOKEN')
    if not client or (args.username == 'me' and not token):
        print('Set TRAKT_CLIENT_ID, and TRAKT_ACCESS_TOKEN when using me.', file=sys.stderr)
        return 1
    headers = {'trakt-api-version': '2', 'trakt-api-key': client}
    if args.username == 'me':
        headers['Authorization'] = f'Bearer {token}'
    try:
        show = fetch_last_watched('episodes', headers, username=args.username)
        movie = fetch_last_watched('movies', headers, username=args.username)
        token = os.getenv('TMDB_ACCESS_TOKEN')
        posters = (get_tmdb_image(show['show'], 'tv', token) if show else None,
                   get_tmdb_image(movie['movie'], 'movie', token) if movie else None)
        html = render_html(show, movie, posters, args.fragment)
        feed = {'version': 1, 'items': []}
        for item, kind, poster in zip((show, movie), ('episodes', 'movies'), posters):
            if not item:
                continue
            media = item['show' if kind == 'episodes' else 'movie']
            episode = item.get('episode', {})
            feed['items'].append({'type': kind, 'title': media['title'], 'year': media.get('year'),
                                  'episode': episode.get('title'), 'season': episode.get('season'),
                                  'number': episode.get('number'), 'watched_at': item['watched_at'], 'poster': poster})
        serialized = json.dumps(feed, ensure_ascii=False, indent=2) + '\n'
        write_atomic(args.output, html)
        if args.json_output:
            write_atomic(args.json_output, serialized)
    except AuthError as exc:
        print(str(exc), file=sys.stderr)
        return 10
    except (FetchError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f'Widget saved to {args.output}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
