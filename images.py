import requests
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# API credentials
TRAKT_CLIENT_ID = os.getenv('TRAKT_CLIENT_ID')
TRAKT_ACCESS_TOKEN = os.getenv('TRAKT_ACCESS_TOKEN')
TMDB_ACCESS_TOKEN = os.getenv('TMDB_ACCESS_TOKEN')

# API endpoints
TRAKT_TV_ENDPOINT = 'https://api.trakt.tv/users/me/history/shows'
TRAKT_MOVIE_ENDPOINT = 'https://api.trakt.tv/users/me/history/movies'
TMDB_TV_URL = 'https://api.themoviedb.org/3/tv/'
TMDB_MOVIE_URL = 'https://api.themoviedb.org/3/movie/'
TMDB_IMAGE_BASE_URL = 'https://image.tmdb.org/t/p/w200'  # Using width 200px images

# Headers
trakt_headers = {
    'Content-Type': 'application/json',
    'trakt-api-version': '2',
    'trakt-api-key': TRAKT_CLIENT_ID,
    'Authorization': f'Bearer {TRAKT_ACCESS_TOKEN}'
}

tmdb_headers = {
    'Authorization': f'Bearer {TMDB_ACCESS_TOKEN}',
    'accept': 'application/json'
}

def fetch_last_watched(endpoint):
    response = requests.get(endpoint, headers=trakt_headers)
    if response.status_code == 200:
        data = response.json()
        return data[0] if data else None
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def get_tmdb_image(tmdb_id, media_type):
    if media_type == 'tv':
        url = f"{TMDB_TV_URL}{tmdb_id}"
    else:
        url = f"{TMDB_MOVIE_URL}{tmdb_id}"
    
    response = requests.get(url, headers=tmdb_headers)
    
    if response.status_code == 200:
        data = response.json()
        poster_path = data.get('poster_path')
        if poster_path:
            return f"{TMDB_IMAGE_BASE_URL}{poster_path}"
    return None

# Fetch last watched TV show and movie
last_show = fetch_last_watched(TRAKT_TV_ENDPOINT)
last_movie = fetch_last_watched(TRAKT_MOVIE_ENDPOINT)

# Generate HTML
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Last Watched on Trakt</title>
    <style>
        .trakt-embed {
            font-family: Arial, sans-serif;
            max-width: 500px;
            border: 1px solid #ddd;
            padding: 15px;
            border-radius: 8px;
            background-color: #f9f9f9;
        }
        .trakt-embed h3 {
            margin-top: 0;
            color: #2c3e50;
        }
        .trakt-embed .item {
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #eee;
            display: flex;
            align-items: start;
        }
        .trakt-embed .item:last-child {
            margin-bottom: 0;
            padding-bottom: 0;
            border-bottom: none;
        }
        .trakt-embed .item-image {
            width: 100px;
            margin-right: 15px;
        }
        .trakt-embed .item-details {
            flex-grow: 1;
        }
        .trakt-embed p {
            margin: 5px 0;
            color: #34495e;
        }
        .trakt-embed .timestamp {
            font-size: 0.8em;
            color: #7f8c8d;
        }
    </style>
</head>
<body>
    <div class="trakt-embed">
        <h3>Last Watched on Trakt</h3>
"""

if last_show:
    show = last_show['show']
    episode = last_show['episode']
    watched_at = datetime.fromisoformat(last_show['watched_at'].replace('Z', '+00:00'))
    image_url = get_tmdb_image(show['ids']['tmdb'], 'tv')
    html_content += f"""
        <div class="item">
            <img class="item-image" src="{image_url or '/path/to/default/image.jpg'}" alt="{show['title']}">
            <div class="item-details">
                <p><strong>TV Show:</strong> {show['title']}</p>
                <p><strong>Episode:</strong> {episode['title']} (S{episode['season']:02d}E{episode['number']:02d})</p>
                <p class="timestamp">Watched: {watched_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
        </div>
    """

if last_movie:
    movie = last_movie['movie']
    watched_at = datetime.fromisoformat(last_movie['watched_at'].replace('Z', '+00:00'))
    image_url = get_tmdb_image(movie['ids']['tmdb'], 'movie')
    html_content += f"""
        <div class="item">
            <img class="item-image" src="{image_url or '/path/to/default/image.jpg'}" alt="{movie['title']}">
            <div class="item-details">
                <p><strong>Movie:</strong> {movie['title']} ({movie['year']})</p>
                <p class="timestamp">Watched: {watched_at.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>
        </div>
    """

html_content += """
    </div>
</body>
</html>
"""

# Save HTML to file
with open('trakt_embed.html', 'w') as f:
    f.write(html_content)

print("HTML embed with images generated and saved as 'trakt_embed.html'")