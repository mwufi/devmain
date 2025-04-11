from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
import secrets
import os
import httpx
from urllib.parse import urlencode
import uvicorn

app = FastAPI()

# Configure templates
templates = Jinja2Templates(directory="sample-consumer/templates")

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

@app.get("/")
async def home(request: Request):
    access_token = request.session.get("access_token")
    
    if not access_token:
        return templates.TemplateResponse(
            "home.html",
            {"request": request, "logged_in": False}
        )
    
    # Fetch user info if logged in
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ARA_SERVER_URL}/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
    
    if response.status_code != 200:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": "Failed to fetch user information",
                "show_login": True
            }
        )
    
    user_info = response.json()
    session_data = dict(request.session)
    
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "logged_in": True,
            "user_info": user_info,
            "session_data": session_data
        }
    )

@app.get("/login")
async def login(request: Request):
    # Generate a state parameter for CSRF protection
    state = secrets.token_urlsafe(16)
    request.session["state"] = state
    
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
    return RedirectResponse(url=auth_url, status_code=303)

@app.get("/callback")
async def callback(request: Request, code: str | None = None, state: str | None = None):
    if not code or not state:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": "Missing code or state parameter",
                "show_login": False
            }
        )
    
    # Verify state to prevent CSRF
    stored_state = request.session.get("state")
    if state != stored_state:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": "Invalid state parameter",
                "show_login": False
            }
        )
    
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
        
        # Redirect to home page
        return RedirectResponse(url="/", status_code=303)
    else:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": "Failed to obtain access token",
                "show_login": False
            }
        )

@app.get("/set-session")
async def set_session(request: Request, key: str, value: str):
    request.session[key] = value
    return RedirectResponse(url="/", status_code=303)

@app.get("/clear-session")
async def clear_session(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

if __name__ == "__main__":
    uvicorn.run("login_web:app", host="0.0.0.0", port=5000, reload=True)