from fastapi import APIRouter, HTTPException, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import Response, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from loguru import logger
import uuid

router = APIRouter(prefix="/oauth2")
templates = Jinja2Templates(directory="oauth/templates")
logger.add("oauth.log")

# Security setup
SECRET_KEY = "another_secret_key"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database setup
Base = declarative_base()
engine = create_engine("sqlite:///ara.db")
Session = sessionmaker(bind=engine)

class ClientDB(Base):
    __tablename__ = "clients"
    client_id = Column(String, primary_key=True)
    client_secret = Column(String)
    redirect_uri = Column(String)
    name = Column(String)

class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    display_name = Column(String)
    email = Column(String, unique=True)

class AuthCodeDB(Base):
    __tablename__ = "auth_codes"
    code = Column(String, primary_key=True)
    client_id = Column(String)
    user_id = Column(Integer)
    expires_at = Column(DateTime)

class TokenDB(Base):
    __tablename__ = "tokens"
    access_token = Column(String, primary_key=True)
    refresh_token = Column(String)
    user_id = Column(Integer)
    client_id = Column(String)
    expires_at = Column(DateTime)

class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    session_id = Column(String, unique=True)
    client_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)

Base.metadata.create_all(engine)

# Utility functions
def generate_client_id():
    return str(uuid.uuid4())

def generate_client_secret():
    return str(uuid.uuid4())

def create_access_token(user_id: int, client_id: str, expires_delta: timedelta):
    to_encode = {"sub": str(user_id), "client_id": client_id, "exp": datetime.utcnow() + expires_delta}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def recreate_tables():
    try:
        # Drop all tables
        Base.metadata.drop_all(engine)
        logger.info("Dropped all existing tables")
        
        # Create all tables
        Base.metadata.create_all(engine)
        logger.info("Created all tables with new schema")
    except Exception as e:
        logger.error(f"Error recreating tables: {e}")

# Update ensure_tables to use recreate_tables
def ensure_tables():
    try:
        # Create all tables if they don't exist
        Base.metadata.create_all(engine)
        logger.info("All database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

# Call it when the module is imported
ensure_tables()

# Routes
@router.post("/register_client")
def register_client(name: str, redirect_uri: str):
    client_id = generate_client_id()
    client_secret = generate_client_secret()
    session = Session()
    client = ClientDB(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        name=name
    )
    session.add(client)
    session.commit()
    session.close()
    return {"client_id": client_id, "client_secret": client_secret}

@router.post("/register_user")
def register_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    display_name: str = Form(None),
    email: str = Form(None)
):
    try:
        logger.info(f"Registering new user: {username}")
        hashed_password = pwd_context.hash(password)
        session = Session()
        
        # Check if username already exists
        existing_user = session.query(UserDB).filter_by(username=username).first()
        if existing_user:
            session.close()
            return {"error": "Username already exists"}
        
        # Create new user with optional fields
        user = UserDB(
            username=username,
            password=hashed_password,
            display_name=display_name or username,  # Use username as display_name if not provided
            email=email
        )
        session.add(user)
        session.commit()
        session.close()
        
        logger.info(f"User registered successfully: {username}")
        return {"message": "User registered successfully"}
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}", exc_info=True)
        return {"error": str(e)}

@router.get("/test_authorize")
def authorize_get(request: Request, client_id: str, redirect_uri: str, scope: str, state: str, response_type: str = "code"):
    session = Session()
    client = session.query(ClientDB).filter_by(client_id=client_id).first()
    return {"client": client}

@router.get("/authorize")
def authorize_get(request: Request, client_id: str, redirect_uri: str, scope: str, state: str, response_type: str = "code"):
    session = Session()
    client = session.query(ClientDB).filter_by(client_id=client_id).first()
    session.close()
    
    if not client or client.redirect_uri != redirect_uri:
        raise HTTPException(status_code=400, detail="Invalid client or redirect_uri")
    
    # Get all active sessions
    db_session = Session()
    active_sessions = db_session.query(UserSession, UserDB).join(
        UserDB, UserSession.user_id == UserDB.id
    ).filter(UserSession.is_active == 1).all()
    db_session.close()
    
    # If no active sessions, show login page
    if not active_sessions:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state
        })
    
    # Show account picker
    return templates.TemplateResponse("account_picker.html", {
        "request": request,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state,
        "active_sessions": active_sessions
    })

@router.get("/select_account")
def select_account(request: Request, user_id: int, client_id: str, redirect_uri: str, scope: str, state: str):
    # Verify the user exists
    session = Session()
    user = session.query(UserDB).filter_by(id=user_id).first()
    session.close()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Store the selected user's ID in the session
    request.session["user_id"] = user.id
    
    # Show consent page for the selected user
    return templates.TemplateResponse("consent.html", {
        "request": request,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state,
        "user": user
    })

@router.post("/authorize")
def authorize_post(request: Request, username: str = Form(...), password: str = Form(...), 
                  client_id: str = Form(...), redirect_uri: str = Form(...), scope: str = Form(...), state: str = Form(...)):
    session = Session()
    user = session.query(UserDB).filter_by(username=username).first()
    if not user or not pwd_context.verify(password, user.password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    
    request.session["user_id"] = user.id
    session.close()
    return templates.TemplateResponse("consent.html", {
        "request": request, "client_id": client_id, "redirect_uri": redirect_uri, "scope": scope, "state": state
    })

@router.post("/consent")
def consent_post(request: Request, consent: str = Form(...), client_id: str = Form(...), 
                redirect_uri: str = Form(...), scope: str = Form(...), state: str = Form(...)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=403, detail="Not logged in")
    
    # Verify the user exists
    session = Session()
    user = session.query(UserDB).filter_by(id=user_id).first()
    if not user:
        session.close()
        raise HTTPException(status_code=404, detail="User not found")
    
    if consent == "yes":
        code = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        auth_code = AuthCodeDB(code=code, client_id=client_id, user_id=user_id, expires_at=expires_at)
        session.add(auth_code)
        session.commit()
        session.close()
        redirect_url = f"{redirect_uri}?code={code}&state={state}"
        return Response(status_code=302, headers={"Location": redirect_url})
    else:
        session.close()
        redirect_url = f"{redirect_uri}?error=access_denied&state={state}"
        return Response(status_code=302, headers={"Location": redirect_url})

class TokenRequest(BaseModel):
    grant_type: str
    code: str = None
    refresh_token: str = None
    redirect_uri: str
    client_id: str
    client_secret: str

@router.post("/token")
def token(grant_type: str = Form(...), code: str = Form(None), refresh_token: str = Form(None), 
          redirect_uri: str = Form(...), client_id: str = Form(...), client_secret: str = Form(...)):
    logger.info(f"Token request received - grant_type: {grant_type}, client_id: {client_id}, redirect_uri: {redirect_uri}")
    session = Session()
    
    # Verify client credentials
    client = session.query(ClientDB).filter_by(client_id=client_id).first()
    if not client:
        logger.info(f"Client not found: {client_id}")
        session.close()
        raise HTTPException(status_code=400, detail="Invalid client credentials")
    if client.client_secret != client_secret:
        logger.info(f"Invalid client secret for client: {client_id}")
        session.close()
        raise HTTPException(status_code=400, detail="Invalid client credentials")
    if client.redirect_uri != redirect_uri:
        logger.info(f"Invalid redirect URI for client: {client_id}. Expected: {client.redirect_uri}, Got: {redirect_uri}")
        session.close()
        raise HTTPException(status_code=400, detail="Invalid client credentials")
    
    if grant_type == "authorization_code":
        if not code:
            logger.info("No code provided for authorization_code grant type")
            session.close()
            raise HTTPException(status_code=400, detail="Code is required for authorization_code grant type")
        
        # Verify authorization code
        auth_code = session.query(AuthCodeDB).filter_by(code=code).first()
        if not auth_code:
            logger.info(f"Authorization code not found: {code}")
            session.close()
            raise HTTPException(status_code=400, detail="Invalid or expired code")
        if auth_code.expires_at < datetime.utcnow():
            logger.info(f"Authorization code expired: {code}")
            session.close()
            raise HTTPException(status_code=400, detail="Invalid or expired code")
        
        # Generate new tokens
        access_token = create_access_token(auth_code.user_id, client_id, timedelta(hours=1))
        refresh_token = str(uuid.uuid4())
        token_db = TokenDB(access_token=access_token, refresh_token=refresh_token, 
                          user_id=auth_code.user_id, client_id=client_id, 
                          expires_at=datetime.utcnow() + timedelta(hours=1))
        session.add(token_db)
        session.delete(auth_code)
        session.commit()
        session.close()
        
        logger.info(f"Tokens generated for client: {client_id}, user: {auth_code.user_id}")
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": refresh_token
        }
    
    elif grant_type == "refresh_token":
        if not refresh_token:
            session.close()
            raise HTTPException(status_code=400, detail="Refresh token is required for refresh_token grant type")
        
        # Verify refresh token
        token_db = session.query(TokenDB).filter_by(refresh_token=refresh_token, client_id=client_id).first()
        if not token_db:
            session.close()
            raise HTTPException(status_code=400, detail="Invalid refresh token")
        
        # Generate new tokens
        new_access_token = create_access_token(token_db.user_id, client_id, timedelta(hours=1))
        new_refresh_token = str(uuid.uuid4())
        
        # Update token record
        token_db.access_token = new_access_token
        token_db.refresh_token = new_refresh_token
        token_db.expires_at = datetime.utcnow() + timedelta(hours=1)
        
        session.commit()
        session.close()
        
        return {
            "access_token": new_access_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": new_refresh_token
        }
    
    else:
        session.close()
        raise HTTPException(status_code=400, detail="Unsupported grant type")

@router.get("/userinfo")
def userinfo(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        session = Session()
        user = session.query(UserDB).filter_by(id=user_id).first()
        session.close()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "user_id": user.id,
            "username": user.username
        }
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/dashboard")
def dashboard(request: Request):
    try:
        session = Session()
        # Get all active sessions
        active_sessions = session.query(UserSession, UserDB).join(
            UserDB, UserSession.user_id == UserDB.id
        ).filter(UserSession.is_active == 1).all()
        
        # Get all clients
        clients = session.query(ClientDB).all()
        
        # Get all users
        users = session.query(UserDB).all()
        
        session.close()
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "active_sessions": active_sessions,
            "clients": clients,
            "users": users
        })
    except Exception as e:
        logger.error(f"Error in dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/login")
def login_get(request: Request, client_id: str = None, redirect_uri: str = None, scope: str = None, state: str = None):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": None,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state
    })

@router.post("/login")
def login_post(request: Request, username: str = Form(...), password: str = Form(...),
              client_id: str = Form(None), redirect_uri: str = Form(None), 
              scope: str = Form(None), state: str = Form(None)):
    try:
        logger.info(f"Login attempt for username: {username}")
        session = Session()
        
        # Find user
        user = session.query(UserDB).filter_by(username=username).first()
        if not user:
            logger.warning(f"User not found: {username}")
            session.close()
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "Invalid credentials",
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "scope": scope,
                "state": state
            })
        
        # Verify password
        if not pwd_context.verify(password, user.password):
            logger.warning(f"Invalid password for user: {username}")
            session.close()
            return templates.TemplateResponse("login.html", {
                "request": request,
                "error": "Invalid credentials",
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "scope": scope,
                "state": state
            })
        
        logger.info(f"User authenticated: {username}")
        
        # Create new session
        session_id = str(uuid.uuid4())
        logger.info(f"Creating new session: {session_id} for user: {username}")
        
        user_session = UserSession(
            user_id=user.id,
            session_id=session_id,
            client_id=client_id  # Store the client_id if this is an OAuth2 flow
        )
        session.add(user_session)
        session.commit()
        
        # Store session ID in request session
        request.session["session_id"] = session_id
        request.session["user_id"] = user.id
        logger.info(f"Session stored for user: {username}")
        
        session.close()

        # If this is part of an OAuth2 flow, show the consent page
        if client_id and redirect_uri:
            return templates.TemplateResponse("consent.html", {
                "request": request,
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "scope": scope,
                "state": state,
                "user": user
            })
        
        # Otherwise, go to dashboard
        return RedirectResponse(url="/oauth2/dashboard", status_code=303)
    except Exception as e:
        logger.error(f"Error in login: {str(e)}", exc_info=True)
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": f"An error occurred during login: {str(e)}",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state
        })

@router.post("/logout")
def logout(request: Request, session_id: str = Form(None)):
    try:
        db_session = Session()
        
        # If specific session_id is provided, log out that session
        if session_id:
            user_session = db_session.query(UserSession).filter_by(session_id=session_id).first()
            if user_session:
                user_session.is_active = 0
                db_session.commit()
                logger.info(f"Logged out session: {session_id}")
        else:
            # Otherwise, log out the current session
            current_session_id = request.session.get("session_id")
            if current_session_id:
                user_session = db_session.query(UserSession).filter_by(session_id=current_session_id).first()
                if user_session:
                    user_session.is_active = 0
                    db_session.commit()
                    logger.info(f"Logged out current session: {current_session_id}")
        
        db_session.close()
        
        # Clear the session if it's the current session being logged out
        if not session_id:
            request.session.clear()
            return RedirectResponse(url="/oauth2/login", status_code=303)
        
        # If logging out another session, stay on dashboard
        return RedirectResponse(url="/oauth2/dashboard", status_code=303)
    except Exception as e:
        logger.error(f"Error in logout: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/switch_account")
def switch_account(request: Request, user_id: int = Form(...)):
    session_id = request.session.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not logged in")
    
    db_session = Session()
    # Deactivate current session
    current_session = db_session.query(UserSession).filter_by(session_id=session_id).first()
    if current_session:
        current_session.is_active = 0
    
    # Create new session for selected user
    new_session_id = str(uuid.uuid4())
    new_session = UserSession(
        user_id=user_id,
        session_id=new_session_id,
        client_id=current_session.client_id if current_session else None
    )
    db_session.add(new_session)
    db_session.commit()
    
    # Update request session
    request.session["session_id"] = new_session_id
    request.session["user_id"] = user_id
    
    db_session.close()
    return RedirectResponse(url="/oauth2/dashboard", status_code=303)

@router.get("/")
def oauth_root(request: Request):
    session_id = request.session.get("session_id")
    if session_id:
        return RedirectResponse(url="/oauth2/dashboard", status_code=303)
    return RedirectResponse(url="/oauth2/login", status_code=303)

@router.get("/debug/db")
def debug_db():
    try:
        session = Session()
        users = session.query(UserDB).all()
        clients = session.query(ClientDB).all()
        user_sessions = session.query(UserSession).all()
        
        result = {
            "users": [{"id": u.id, "username": u.username} for u in users],
            "clients": [{"client_id": c.client_id, "redirect_uri": c.redirect_uri} for c in clients],
            "sessions": [{"session_id": s.session_id, "user_id": s.user_id, "is_active": s.is_active} for s in user_sessions]
        }
        
        session.close()
        return result
    except Exception as e:
        logger.error(f"Debug error: {str(e)}", exc_info=True)
        return {"error": str(e)}

@router.post("/debug/recreate_tables")
def debug_recreate_tables():
    """Debug endpoint to recreate all database tables"""
    try:
        recreate_tables()
        return {"message": "Tables recreated successfully"}
    except Exception as e:
        logger.error(f"Error recreating tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))
