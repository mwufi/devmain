from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import Response
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import uuid

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="some_secret_key")
templates = Jinja2Templates(directory="templates")

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

class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)

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

Base.metadata.create_all(engine)

# Utility functions
def generate_client_id():
    return str(uuid.uuid4())

def generate_client_secret():
    return str(uuid.uuid4())

def create_access_token(user_id: int, client_id: str, expires_delta: timedelta):
    to_encode = {"sub": user_id, "client_id": client_id, "exp": datetime.utcnow() + expires_delta}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Routes
@app.post("/register_client")
def register_client(redirect_uri: str):
    client_id = generate_client_id()
    client_secret = generate_client_secret()
    session = Session()
    client = ClientDB(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)
    session.add(client)
    session.commit()
    session.close()
    return {"client_id": client_id, "client_secret": client_secret}

@app.post("/register_user")
def register_user(username: str, password: str):
    hashed_password = pwd_context.hash(password)
    session = Session()
    user = UserDB(username=username, password=hashed_password)
    session.add(user)
    session.commit()
    session.close()
    return {"message": "User registered"}

@app.get("/authorize")
def authorize_get(request: Request, client_id: str, redirect_uri: str, scope: str, state: str, response_type: str = "code"):
    session = Session()
    client = session.query(ClientDB).filter_by(client_id=client_id).first()
    session.close()
    if not client or client.redirect_uri != redirect_uri:
        raise HTTPException(status_code=400, detail="Invalid client or redirect_uri")
    
    user_id = request.session.get("user_id")
    if not user_id:
        return templates.TemplateResponse("login.html", {
            "request": request, "client_id": client_id, "redirect_uri": redirect_uri, "scope": scope, "state": state
        })
    
    return templates.TemplateResponse("consent.html", {
        "request": request, "client_id": client_id, "redirect_uri": redirect_uri, "scope": scope, "state": state
    })

@app.post("/authorize")
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

@app.post("/consent")
def consent_post(request: Request, consent: str = Form(...), client_id: str = Form(...), 
                redirect_uri: str = Form(...), scope: str = Form(...), state: str = Form(...)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=403, detail="Not logged in")
    
    if consent == "yes":
        code = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        session = Session()
        auth_code = AuthCodeDB(code=code, client_id=client_id, user_id=user_id, expires_at=expires_at)
        session.add(auth_code)
        session.commit()
        session.close()
        redirect_url = f"{redirect_uri}?code={code}&state={state}"
        return Response(status_code=302, headers={"Location": redirect_url})
    else:
        redirect_url = f"{redirect_uri}?error=access_denied&state={state}"
        return Response(status_code=302, headers={"Location": redirect_url})

class TokenRequest(BaseModel):
    grant_type: str
    code: str
    redirect_uri: str
    client_id: str
    client_secret: str

@app.post("/token")
def token(request: TokenRequest):
    if request.grant_type != "authorization_code":
        raise HTTPException(status_code=400, detail="Invalid grant_type")
    
    session = Session()
    auth_code = session.query(AuthCodeDB).filter_by(code=request.code).first()
    if not auth_code or auth_code.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    
    client = session.query(ClientDB).filter_by(client_id=request.client_id).first()
    if not client or client.client_secret != request.client_secret or client.redirect_uri != request.redirect_uri:
        raise HTTPException(status_code=400, detail="Invalid client credentials")
    
    access_token = create_access_token(auth_code.user_id, request.client_id, timedelta(hours=1))
    refresh_token = str(uuid.uuid4())
    token_db = TokenDB(access_token=access_token, refresh_token=refresh_token, 
                      user_id=auth_code.user_id, client_id=request.client_id, 
                      expires_at=datetime.utcnow() + timedelta(hours=1))
    session.add(token_db)
    session.delete(auth_code)
    session.commit()
    session.close()
    
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": refresh_token
    }
