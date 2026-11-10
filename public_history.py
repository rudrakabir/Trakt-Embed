"""Read only the rendered, signed-out Trakt profile; no account or API keys."""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
import re
import sys
from urllib.parse import quote
import requests
from images import FetchError, TIMEOUT, render_html, write_atomic


WEEKDAYS = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')
WATCH_DATE = re.compile(
    r'^(?:Today|Yesterday|Last [A-Za-z]+|[A-Za-z]+ \d{1,2}(?:st|nd|rd|th)?, \d{4})$',
    re.IGNORECASE,
)


def parse_history(text, kind, today=None):
    today = today or datetime.now(timezone.utc).date()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    try:
        start = lines.index('History') + 1
        date_text, title, detail = lines[start:start + 3]
    except (ValueError, IndexError) as exc:
        raise FetchError('Public history was not found; existing output preserved.') from exc
    date_label = date_text.casefold()
    if date_label == 'today':
        watched = today
    elif date_label == 'yesterday':
        watched = today - timedelta(days=1)
    elif date_label.startswith('last ') and date_label[5:] in WEEKDAYS:
        days_ago = (today.weekday() - WEEKDAYS.index(date_label[5:])) % 7 or 7
        watched = today - timedelta(days=days_ago)
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


def read_history(page, username, kind, mode):
    from playwright.sync_api import Error

    status = 'unavailable'
    stage = 'opening profile'
    try:
        response = page.goto(f'https://app.trakt.tv/profile/{quote(username, safe="")}?mode={mode}',
                             wait_until='domcontentloaded', timeout=60000)
        if response is not None:
            status = response.status
            if (response.headers.get('cf-mitigated') == 'challenge'
                    or page.get_by_text('Sorry, you have been blocked', exact=True).count()):
                raise FetchError('Cloudflare blocked the runner from reading the public profile.')
            if status >= 400:
                raise FetchError(f'Trakt returned HTTP {status}.')

        stage = 'waiting for a public history entry'
        link = page.get_by_role('link', name='View all history', exact=True)
        history = page.locator('section.section-list-container').filter(has=link)
        history.scroll_into_view_if_needed(timeout=30000)
        history.get_by_text(WATCH_DATE).first.wait_for(timeout=30000)
        stage = 'parsing the history entry'
        lines = history.inner_text().splitlines()
        start = next((i for i, line in enumerate(lines) if WATCH_DATE.fullmatch(line.strip())), None)
        if start is None:
            raise FetchError('No recognized date was found in the history section.')
        return parse_history('History\n' + '\n'.join(lines[start:]), kind)
    except (Error, FetchError) as exc:
        try:
            title = ' '.join(page.title().split())[:120]
        except Error:
            title = 'unavailable'
        final_url = page.url.split('?', 1)[0].split('#', 1)[0]
        detail = str(exc) if isinstance(exc, FetchError) else type(exc).__name__
        raise FetchError(f'{mode} view, {stage}: {detail} '
                         f'(HTTP {status}, URL {final_url}, title {title!r}).') from exc


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
                item = read_history(page, args.username, kind, mode)
                item['poster'] = poster_for(item)
                items.append(item)
            browser.close()
        html = render_html(as_history(items[0]), as_history(items[1]), tuple(i['poster'] for i in items))
        feed = json.dumps({'version': 1, 'source': 'public-profile', 'items': items}, ensure_ascii=False, indent=2) + '\n'
        write_atomic(args.output, html)
        write_atomic(args.json_output, feed)
    except (FetchError, Error, OSError) as exc:
        detail = str(exc) if isinstance(exc, FetchError) else type(exc).__name__
        print(f'Public history update failed: {detail} Existing output preserved.', file=sys.stderr)
        return 1
    print('Published latest public episode and movie.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
