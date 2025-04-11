from fastapi import FastAPI, Request, HTTPException, status, Depends, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from db import (
    User, get_db, get_user_by_access_token, get_user_by_ara_id, create_or_update_user,
    get_user_prompts, create_prompt, delete_prompt, update_prompt
)
import secrets
import os
import httpx
from urllib.parse import urlencode
import uvicorn
from loguru import logger


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
os.environ['CLIENT_ID'] = '579b83f4-0f82-4ac3-8bdc-d36615f5b473'
os.environ['CLIENT_SECRET'] = '0795470e-4bf1-40f1-a97f-1b3fb61e82'

ARA_SERVER_URL = "http://localhost:8000/oauth2"
CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']
REDIRECT_URI = "http://localhost:5000/callback"
SCOPE = "profile email"

# Current user dependency
def get_current_user(request: Request, db: Session = Depends(get_db)):
    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = get_user_by_access_token(db, access_token)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"Current user: {user}")
    return user

@app.get("/")
async def home(request: Request, db: Session = Depends(get_db)):
    access_token = request.session.get("access_token")
    
    if not access_token:
        return templates.TemplateResponse(
            "home.html",
            {
                "request": request,
                "logged_in": False,
                "user_info": None,
                "session_data": {},
                "token_info": {}
            }
        )
    
    # Get current user
    user = get_user_by_access_token(db, access_token)
    if not user:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": "User not found",
                "show_login": True,
                "logged_in": False,
                "user_info": None,
                "session_data": {},
                "token_info": {}
            }
        )
    
    # Get user's prompts
    prompts = get_user_prompts(db, user.id)
    
    # Calculate token expiration time
    expires_in = (user.token_expires_at - datetime.utcnow()).total_seconds() if user.token_expires_at else 0
    expires_in = max(0, expires_in)  # Don't show negative time
    
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "logged_in": True,
            "user_info": {"username": user.username, "user_id": user.ara_user_id},
            "session_data": dict(request.session),
            "prompts": prompts,
            "token_info": {
                "access_token": access_token[:10] + "..." if access_token else None,
                "refresh_token": user.refresh_token[:10] + "..." if user.refresh_token else None,
                "expires_in": int(expires_in),
                "expires_at": user.token_expires_at.isoformat() if user.token_expires_at else None
            }
        }
    )

@app.get("/prompts")
async def get_prompts(request: Request, db: Session = Depends(get_db)):
    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = get_user_by_access_token(db, access_token)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    prompts = get_user_prompts(db, user.id)
    return {"prompts": [{"id": p.id, "title": p.title, "content": p.content} for p in prompts]}

@app.post("/prompts")
async def create_prompt_endpoint(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    create_prompt(db, current_user.id, title, content)
    return RedirectResponse(url="/", status_code=303)

@app.post("/prompts/{prompt_id}")
async def handle_prompt_operation(
    prompt_id: int,
    request: Request,
    method_override: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if method_override == "delete":
        if not delete_prompt(db, prompt_id, current_user.id):
            raise HTTPException(status_code=404, detail="Prompt not found")
        return RedirectResponse(url="/", status_code=303)
    raise HTTPException(status_code=405, detail="Method Not Allowed")

@app.put("/prompts/{prompt_id}")
async def update_prompt_endpoint(
    prompt_id: int,
    request: Request,
    title: str,
    content: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prompt = update_prompt(db, prompt_id, current_user.id, title, content)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return RedirectResponse(url="/", status_code=303)

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
async def callback(request: Request, code: str | None = None, state: str | None = None, db: Session = Depends(get_db)):
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
            refresh_token = token_info.get("refresh_token")
            expires_in = token_info.get("expires_in", 3600)
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # Get user info from Ara using a new client
            async with httpx.AsyncClient() as user_client:
                user_response = await user_client.get(
                    f"{ARA_SERVER_URL}/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if user_response.status_code != 200:
                    return templates.TemplateResponse(
                        "error.html",
                        {
                            "request": request,
                            "error_message": "Failed to fetch user information",
                            "show_login": False
                        }
                    )
                
                user_data = user_response.json()
                ara_user_id = user_data["user_id"]
                username = user_data["username"]
                
                # Store or update user in database
                user = create_or_update_user(
                    db, ara_user_id, username, access_token, refresh_token, expires_at
                )
                
                # Store access token in session
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

@app.post("/refresh-token")
async def refresh_token(request: Request, db: Session = Depends(get_db)):
    access_token = request.session.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = get_user_by_access_token(db, access_token)
    if not user or not user.refresh_token:
        raise HTTPException(status_code=400, detail="No refresh token available")
    
    # Exchange refresh token for new tokens
    token_url = f"{ARA_SERVER_URL}/token"
    token_data = {
        "grant_type": "refresh_token",
        "refresh_token": user.refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=token_data)
            logger.info(f"Refresh token response: {response.status_code} - {response.text}")
            
            if response.status_code == 200:
                token_info = response.json()
                new_access_token = token_info.get("access_token")
                new_refresh_token = token_info.get("refresh_token")
                expires_in = token_info.get("expires_in", 3600)
                expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                
                # Update user tokens
                user = create_or_update_user(
                    db, user.ara_user_id, user.username, 
                    new_access_token, new_refresh_token, expires_at
                )
                
                # Update session
                request.session["access_token"] = new_access_token
                
                return RedirectResponse(url="/", status_code=303)
            else:
                logger.error(f"Failed to refresh token: {response.status_code} - {response.text}")
                return templates.TemplateResponse(
                    "error.html",
                    {
                        "request": request,
                        "error_message": f"Failed to refresh token: {response.text}",
                        "show_login": True
                    }
                )
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": f"Error refreshing token: {str(e)}",
                "show_login": True
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