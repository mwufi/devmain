import requests
from urllib.parse import urlparse, parse_qs, quote
import os
import secrets

os.environ['CLIENT_ID'] = '2c768dd5-9f97-4cba-825f-752c0337e5a3'
os.environ['CLIENT_SECRET'] = '32f0a951-58d2-4426-b663-9b43031c503c'

# Configuration (replace with your actual values)
ARA_SERVER_URL = "http://localhost:8000/oauth2"  # URL where Ara is running
CLIENT_ID = os.environ['CLIENT_ID']              # Obtained from Ara during registration
CLIENT_SECRET = os.environ['CLIENT_SECRET']      # Obtained from Ara during registration
REDIRECT_URI = "http://localhost:8000/callback"  # A dummy URI for this example
SCOPE = "profile email"                    # Requested scopes (adjust as needed)

# Generate a random state parameter for CSRF protection
STATE = secrets.token_urlsafe(16)

# Step 1: Generate the authorization URL
auth_params = {
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "response_type": "code",
    "scope": quote(SCOPE),  # URL-encode the scope parameter
    "state": STATE  # Add state parameter
}
auth_url = f"{ARA_SERVER_URL}/authorize?" + "&".join([f"{quote(str(k))}={quote(str(v))}" for k, v in auth_params.items()])
print(f"Please visit this URL to authorize: {auth_url}")

# Step 2: Instruct the user to log in and copy the redirected URL
print("\nAfter authorizing, you will be redirected to a URL like:")
print(f"{REDIRECT_URI}?code=abc123")
print("Please copy the entire URL from your browser's address bar and paste it here.")

# Step 3: Wait for the user to paste the redirected URL
redirected_url = input("\nPaste the redirected URL here: ")

# Step 4: Parse the authorization code from the URL
try:
    parsed_url = urlparse(redirected_url)
    query_params = parse_qs(parsed_url.query)
    code = query_params.get("code", [None])[0]
    if not code:
        raise ValueError("Authorization code not found in the URL.")
except Exception as e:
    print(f"Error parsing the URL: {e}")
    exit(1)

# Step 5: Exchange the authorization code for an access token
token_url = f"{ARA_SERVER_URL}/token"
token_data = {
    "grant_type": "authorization_code",
    "code": code,
    "redirect_uri": REDIRECT_URI,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET
}

response = requests.post(token_url, data=token_data)

if response.status_code == 200:
    token_info = response.json()
    access_token = token_info.get("access_token")
    print(f"\nSuccess! Access token: {access_token}")
else:
    print(f"\nError: {response.status_code} - {response.text}")