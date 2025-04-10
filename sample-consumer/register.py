import requests
import getpass

# redirect_uri = "http://localhost:8000/callback"
# response = requests.post("http://localhost:8000/oauth2/register_client", params={"redirect_uri": redirect_uri})
# print(response.json())

# client_id = response.json()["client_id"]
# client_secret = response.json()["client_secret"]

# print(f"Client ID: {client_id}")
# print(f"Client Secret: {client_secret}")

client_id = "2c768dd5-9f97-4cba-825f-752c0337e5a3"
client_secret = "32f0a951-58d2-4426-b663-9b43031c503c"

# response = requests.post("http://localhost:8000/oauth2/token", data={
#     "grant_type": "client_credentials",
#     "client_id": client_id,
#     "client_secret": client_secret
# })
# print(response.json())

def register_user(username: str, password: str):
    response = requests.post(
        "http://localhost:8000/oauth2/register_user",
        params={
            "username": username,
            "password": password
        }
    )
    return response.json()

if __name__ == "__main__":
    print("User Registration")
    print("----------------")
    username = input("Enter username: ")
    password = getpass.getpass("Enter password: ")
    
    try:
        result = register_user(username, password)
        print("\nRegistration result:", result)
    except Exception as e:
        print(f"\nError during registration: {e}")

