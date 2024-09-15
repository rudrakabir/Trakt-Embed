import requests
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv('TRAKT_CLIENT_ID')
CLIENT_SECRET = os.getenv('TRAKT_CLIENT_SECRET')

# Step 1: Get a device code
response = requests.post('https://api.trakt.tv/oauth/device/code', json={
    'client_id': CLIENT_ID
})
data = response.json()
device_code = data['device_code']
user_code = data['user_code']
verification_url = data['verification_url']

print(f"Please go to {verification_url} and enter the code: {user_code}")

# Step 2: Poll for the access token
while True:
    response = requests.post('https://api.trakt.tv/oauth/device/token', json={
        'code': device_code,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    })
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data['access_token']
        refresh_token = token_data['refresh_token']
        
        print(f"Access Token: {access_token}")
        print(f"Refresh Token: {refresh_token}")
        
        # Save tokens to .env file
        with open('.env', 'a') as env_file:
            env_file.write(f"\nTRAKT_ACCESS_TOKEN={access_token}")
            env_file.write(f"\nTRAKT_REFRESH_TOKEN={refresh_token}")
        
        
        print("Tokens have been saved to .env file")
        break
    elif response.status_code == 400:
        print("Waiting for user to authorize...")
        time.sleep(5)
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        break