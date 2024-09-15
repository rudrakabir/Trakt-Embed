import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Trakt.tv API credentials
CLIENT_ID = os.getenv('TRAKT_CLIENT_ID')
ACCESS_TOKEN = os.getenv('TRAKT_ACCESS_TOKEN')

# API endpoint for last watched item
API_ENDPOINT = 'https://api.trakt.tv/users/me/history/shows'

# Headers for authentication
headers = {
    'Content-Type': 'application/json',
    'trakt-api-version': '2',
    'trakt-api-key': CLIENT_ID,
    'Authorization': f'Bearer {ACCESS_TOKEN}'
}

# Make the API request
response = requests.get(API_ENDPOINT, headers=headers)

if response.status_code == 200:
    data = response.json()
    if data:
        last_watched = data[0]
        show = last_watched['show']
        episode = last_watched['episode']
        
        print(f"Last watched show: {show['title']}")
        print(f"Episode: {episode['title']} (S{episode['season']:02d}E{episode['number']:02d})")
        print(f"Watched at: {last_watched['watched_at']}")
    else:
        print("No watch history found.")
else:
    print(f"Error: {response.status_code}")
    print(response.text)