"""Read only the rendered, signed-out Trakt profile; no account or API keys."""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import quote
import requests
from images import FetchError, TIMEOUT, render_html, write_atomic


def parse_history(text, kind, today=None):
    today = today or datetime.now(timezone.utc).date()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    try:
        start = lines.index('History') + 1
        date_text, title, detail = lines[start:start + 3]
    except (ValueError, IndexError) as exc:
        raise FetchError('Public history was not found; existing output preserved.') from exc
    if date_text == 'Today':
        watched = today
    elif date_text == 'Yesterday':
        watched = today - timedelta(days=1)
    else:
        clean = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_text)
        try:
            watched = datetime.strptime(clean, '%B %d, %Y').date()
        except ValueError as exc:
            raise FetchError('Unrecognized public watch date; existing output preserved.') from exc
    if watched > today or not title:
        raise FetchError('Invalid public history; existing output preserved.')
    item = {'type': kind, 'title': title, 'year': None, 'episode': None, 'season': None,
            'number': None, 'watched_at': watched.isoformat(), 'date_precision': 'day', 'poster': None}
    if kind == 'episodes':
        match = re.fullmatch(r'S(\d+)\s*•\s*E(\d+)\s*-\s*(.+)', detail)
        if not match:
            raise FetchError('Episode details changed; existing output preserved.')
        item.update(season=int(match[1]), number=int(match[2]), episode=match[3])
    elif detail != 'Movie':
        raise FetchError('Movie details changed; existing output preserved.')
    return item


def poster_for(item):
    token = os.getenv('TMDB_ACCESS_TOKEN')
    if not token:
        return None
    media = 'tv' if item['type'] == 'episodes' else 'movie'
    title_key = 'name' if media == 'tv' else 'title'
    try:
        response = requests.get(f'https://api.themoviedb.org/3/search/{media}',
                                headers={'Authorization': f'Bearer {token}'},
                                params={'query': item['title'], 'include_adult': 'false'}, timeout=TIMEOUT)
        response.raise_for_status()
        matches = [row for row in response.json()['results']
                   if str(row.get(title_key, '')).casefold() == item['title'].casefold()]
        if len(matches) == 1:
            path = matches[0].get('poster_path')
            if isinstance(path, str) and re.fullmatch(r'/[A-Za-z0-9_.-]+', path):
                return 'https://image.tmdb.org/t/p/w200' + path
    except (requests.RequestException, ValueError, KeyError, TypeError):
        pass
    return None


def as_history(item):
    key = 'show' if item['type'] == 'episodes' else 'movie'
    return {key: {'title': item['title'], 'year': item['year']},
            'episode': {'season': item['season'], 'number': item['number'], 'title': item['episode']},
            'watched_at': item['watched_at'], 'date_precision': 'day'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--username', default=os.getenv('TRAKT_USERNAME', 'rudrakabir'))
    parser.add_argument('--output', default='trakt_embed.html')
    parser.add_argument('--json-output', default='trakt_data.json')
    args = parser.parse_args(argv)
    from playwright.sync_api import sync_playwright, Error
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(locale='en-US', timezone_id='UTC')
            page = context.new_page()
            items = []
            for kind, mode in [('episodes', 'show'), ('movies', 'movie')]:
                page.goto(f'https://app.trakt.tv/profile/{quote(args.username, safe="")}?mode={mode}',
                          wait_until='networkidle', timeout=60000)
                page.get_by_text('History', exact=True).wait_for(timeout=30000)
                item = parse_history(page.locator('body').inner_text(), kind)
                item['poster'] = poster_for(item)
                items.append(item)
            browser.close()
        html = render_html(as_history(items[0]), as_history(items[1]), tuple(i['poster'] for i in items))
        feed = json.dumps({'version': 1, 'source': 'public-profile', 'items': items}, ensure_ascii=False, indent=2) + '\n'
        write_atomic(args.output, html)
        write_atomic(args.json_output, feed)
    except (FetchError, Error, OSError) as exc:
        print(f'Public history update failed ({type(exc).__name__}); existing output preserved.', file=sys.stderr)
        return 1
    print('Published latest public episode and movie.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
