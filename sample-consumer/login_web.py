from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
import secrets
import os
import httpx
from urllib.parse import urlencode
import uvicorn

app = FastAPI()

# Session configuration
app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_hex(32),
    max_age=360000,  # Session expires in 1 hour
    same_site="lax",
    session_cookie="session_5000",  # Make cookie name port-specific
    https_only=False,  # Allow cookies in development
    path="/"  # Explicitly set path
)

# OAuth2 configuration
os.environ['CLIENT_ID'] = '7d55c1db-a93d-431a-87c2-165a25929eac'
os.environ['CLIENT_SECRET'] = '5bb01630-ff69-4290-bbb2-90b60f1998c6'

ARA_SERVER_URL = "http://localhost:8000/oauth2"
CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']
REDIRECT_URI = "http://localhost:5000/callback"
SCOPE = "profile email"

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Welcome to Ara Login</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                text-align: center;
            }
            .login-button {
                display: inline-block;
                padding: 10px 20px;
                background-color: #4CAF50;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin-top: 20px;
            }
            .login-button:hover {
                background-color: #45a049;
            }
        </style>
    </head>
    <body>
        <h1>Welcome to Ara Login</h1>
        <p>Please sign in to continue</p>
        <a href="/login" class="login-button">Sign in with Ara</a>
    </body>
    </html>
    """

@app.get("/login")
async def login(request: Request):
    # Generate a state parameter for CSRF protection
    state = secrets.token_urlsafe(16)
    request.session["state"] = state
    print(f"Stored state in session: {state}")
    print(f"Current session data: {dict(request.session)}")
    
    # Build query parameters
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "state": state
    }
    
    # Build the authorization URL
    auth_url = f"{ARA_SERVER_URL}/authorize?{urlencode(params)}"
    response = RedirectResponse(url=auth_url, status_code=303)
    return response

@app.get("/callback", response_class=HTMLResponse)
async def callback(request: Request, code: str | None = None, state: str | None = None):
    if not code or not state:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    text-align: center;
                }
                .error {
                    color: #f44336;
                    margin: 20px 0;
                }
                .button {
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 20px;
                }
            </style>
        </head>
        <body>
            <h1>Error</h1>
            <p class="error">Missing code or state parameter</p>
            <a href="/" class="button">Return to Home</a>
        </body>
        </html>
        """)
    
    # Verify state to prevent CSRF
    stored_state = request.session.get("state")
    print(f"Received state: {state}, Stored state: {stored_state}")  # Debug log
    
    if state != stored_state:
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    text-align: center;
                }}
                .error {{
                    color: #f44336;
                    margin: 20px 0;
                }}
                .debug {{
                    background: #f5f5f5;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                    text-align: left;
                }}
                .button {{
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <h1>Error</h1>
            <p class="error">Invalid state parameter</p>
            <div class="debug">
                <h3>Debug Information:</h3>
                <p>Received state: {state}</p>
                <p>Stored state: {stored_state}</p>
            </div>
            <a href="/" class="button">Return to Home</a>
        </body>
        </html>
        """)
    
    # Exchange code for access token
    token_url = f"{ARA_SERVER_URL}/token"
    token_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=token_data)
    
    if response.status_code == 200:
        token_info = response.json()
        access_token = token_info.get("access_token")
        request.session["access_token"] = access_token
        
        # Clear the state after successful verification
        request.session.pop("state", None)
        
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login Successful</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    text-align: center;
                }
                .success {
                    color: #4CAF50;
                    margin: 20px 0;
                }
                .debug {
                    background: #f5f5f5;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                    text-align: left;
                }
                .button {
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 20px;
                }
            </style>
        </head>
        <body>
            <h1>Login Successful!</h1>
            <p class="success">You have been successfully authenticated.</p>
            <div class="debug">
                <h3>Session Information:</h3>
                <p>Access token stored in session</p>
                <p>State parameter cleared</p>
            </div>
            <a href="/test-session" class="button">View Session Data</a>
            <a href="/" class="button">Return to Home</a>
        </body>
        </html>
        """)
    else:
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    text-align: center;
                }}
                .error {{
                    color: #f44336;
                    margin: 20px 0;
                }}
                .debug {{
                    background: #f5f5f5;
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                    text-align: left;
                }}
                .button {{
                    display: inline-block;
                    padding: 10px 20px;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <h1>Error</h1>
            <p class="error">Failed to obtain access token</p>
            <div class="debug">
                <h3>Error Details:</h3>
                <p>Status Code: {response.status_code}</p>
                <p>Response: {response.text}</p>
            </div>
            <a href="/" class="button">Return to Home</a>
        </body>
        </html>
        """)

@app.get("/test-session", response_class=HTMLResponse)
async def test_session(request: Request):
    # Get current session data
    session_data = dict(request.session)
    
    # Create HTML to display session data
    session_html = "<ul>"
    for key, value in session_data.items():
        session_html += f"<li><strong>{key}:</strong> {value}</li>"
    session_html += "</ul>"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Session Test</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}
            .session-data {{
                background: #f5f5f5;
                padding: 20px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .button {{
                display: inline-block;
                padding: 10px 20px;
                margin: 10px;
                background-color: #4CAF50;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                border: none;
                cursor: pointer;
            }}
            .button:hover {{
                background-color: #45a049;
            }}
            .danger {{
                background-color: #f44336;
            }}
            .danger:hover {{
                background-color: #d32f2f;
            }}
        </style>
    </head>
    <body>
        <h1>Session Test Page</h1>
        
        <div class="session-data">
            <h2>Current Session Data:</h2>
            {session_html}
        </div>
        
        <form action="/set-session" method="get">
            <input type="text" name="key" placeholder="Key" required>
            <input type="text" name="value" placeholder="Value" required>
            <button type="submit" class="button">Set Session Value</button>
        </form>
        
        <form action="/clear-session" method="get">
            <button type="submit" class="button danger">Clear Session</button>
        </form>
        
        <a href="/test-session" class="button">Refresh Page</a>
    </body>
    </html>
    """

@app.get("/set-session", response_class=HTMLResponse)
async def set_session(request: Request, key: str, value: str):
    request.session[key] = value
    print(f"Setting session key '{key}' to '{value}'")
    print(f"Current session data: {dict(request.session)}")
    response = RedirectResponse(url="/test-session", status_code=303)
    return response

@app.get("/clear-session", response_class=HTMLResponse)
async def clear_session(request: Request):
    print("Clearing session data")
    print(f"Session data before clear: {dict(request.session)}")
    request.session.clear()
    response = RedirectResponse(url="/test-session", status_code=303)
    return response

@app.get("/other-page", response_class=HTMLResponse)
async def other_page(request: Request):
    # Get current session data
    session_data = dict(request.session)
    
    # Create HTML to display session data
    session_html = "<ul>"
    for key, value in session_data.items():
        session_html += f"<li><strong>{key}:</strong> {value}</li>"
    session_html += "</ul>"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Other Page</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}
            .session-data {{
                background: #f5f5f5;
                padding: 20px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .button {{
                display: inline-block;
                padding: 10px 20px;
                margin: 10px;
                background-color: #4CAF50;
                color: white;
                text-decoration: none;
                border-radius: 5px;
            }}
            .button:hover {{
                background-color: #45a049;
            }}
        </style>
    </head>
    <body>
        <h1>Other Page</h1>
        <p>This is a different page, but it should show the same session data!</p>
        
        <div class="session-data">
            <h2>Current Session Data:</h2>
            {session_html}
        </div>
        
        <a href="/test-session" class="button">Go to Test Page</a>
        <a href="/" class="button">Go to Home</a>
    </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)