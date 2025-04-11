import requests
import argparse
import json
import os
from urllib.parse import urlencode
from getpass import getpass

def register_client(redirect_uri):
    # Configuration
    ARA_SERVER_URL = "http://localhost:8000/oauth2"
    
    # Prepare query parameters
    params = {
        "redirect_uri": redirect_uri
    }
    
    # Make the registration request
    response = requests.post(
        f"{ARA_SERVER_URL}/register_client",
        params=params
    )
    
    if response.status_code == 200:
        client_info = response.json()
        print("\nRegistration successful!")
        print("\nClient credentials:")
        print(f"Client ID: {client_info['client_id']}")
        print(f"Client Secret: {client_info['client_secret']}")
        print(f"\nSave these credentials in your .env file:")
        print(f"CLIENT_ID={client_info['client_id']}")
        print(f"CLIENT_SECRET={client_info['client_secret']}")
    else:
        print(f"Registration failed: {response.status_code}")
        print(response.text)

def register_user():
    # Get user credentials
    print("\nUser Registration")
    print("----------------")
    username = input("Enter username: ")
    password = getpass("Enter password: ")
    
    # Configuration
    ARA_SERVER_URL = "http://localhost:8000/oauth2"
    
    # Prepare registration data
    data = {
        "username": username,
        "password": password
    }
    
    # Make the registration request
    response = requests.post(
        f"{ARA_SERVER_URL}/register_user",
        json=data
    )
    
    if response.status_code == 200:
        print("\nUser registration successful!")
        print(f"Username: {username}")
    else:
        print(f"\nUser registration failed: {response.status_code}")
        print(response.text)

def main():
    parser = argparse.ArgumentParser(description='OAuth2 registration tools')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Client registration command
    client_parser = subparsers.add_parser('client', help='Register a new OAuth client')
    client_parser.add_argument('--uri', required=True, help='The redirect URI to register')
    
    # User registration command
    user_parser = subparsers.add_parser('user', help='Register a new user')
    
    args = parser.parse_args()
    
    if args.command == 'client':
        register_client(args.uri)
    elif args.command == 'user':
        register_user()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()

