from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
from fastapi import Request, Form, Depends
from fastapi.responses import RedirectResponse

# Database setup
Base = declarative_base()
engine = create_engine("sqlite:///sample-consumer/users.db")
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    ara_user_id = Column(String, unique=True)
    username = Column(String)
    access_token = Column(String)
    refresh_token = Column(String)
    token_expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class Prompt(Base):
    __tablename__ = "prompts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    content = Column(String)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create tables
Base.metadata.create_all(engine)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# User operations
def get_user_by_access_token(db: Session, access_token: str):
    return db.query(User).filter_by(access_token=access_token).first()

def get_user_by_ara_id(db: Session, ara_user_id: str):
    return db.query(User).filter_by(ara_user_id=ara_user_id).first()

def create_or_update_user(db: Session, ara_user_id: str, username: str, 
                         access_token: str, refresh_token: str, expires_at: datetime):
    user = get_user_by_ara_id(db, ara_user_id)
    if user:
        user.username = username
        user.access_token = access_token
        user.refresh_token = refresh_token
        user.token_expires_at = expires_at
    else:
        user = User(
            ara_user_id=ara_user_id,
            username=username,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=expires_at
        )
        db.add(user)
    db.commit()
    return user

# Prompt operations
def get_user_prompts(db: Session, user_id: int):
    return db.query(Prompt).filter(
        (Prompt.user_id == user_id) | (Prompt.is_public == True)
    ).order_by(Prompt.updated_at.desc()).all()

def create_prompt(db: Session, user_id: int, title: str, content: str, is_public: bool = False) -> Prompt:
    prompt = Prompt(user_id=user_id, title=title, content=content, is_public=is_public)
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt

def delete_prompt(db: Session, prompt_id: int, user_id: int) -> bool:
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id, Prompt.user_id == user_id).first()
    if prompt:
        db.delete(prompt)
        db.commit()
        return True
    return False

def update_prompt(db: Session, prompt_id: int, user_id: int, title: str, content: str) -> Prompt | None:
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id, Prompt.user_id == user_id).first()
    if prompt:
        prompt.title = title
        prompt.content = content
        prompt.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(prompt)
    return prompt 