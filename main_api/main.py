from fastapi import FastAPI, Request, Path, Body
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import httpx
import subprocess
import os
from ai import get_ai_response, get_chat_ai_response
from db import get_whales
from typing import List, Dict, Any
from pydantic import BaseModel

class UserMessage(BaseModel):
    message: str = None

app = FastAPI()

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - in production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

print("App starting up!", flush=True)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("shell.html", {"request": request})

@app.post("/execute")
async def execute_command(command: dict):
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://localhost:3000/messages",
                json={"role": "user", "content": command["command"]}
            )

        # Get AI response
        ai_response = get_ai_response(command["command"])
        
        # Post user message to localhost:3000/messages
        async with httpx.AsyncClient() as client:
            # Post AI response to localhost:3000/messages
            await client.post(
                "http://localhost:3000/messages",
                json={"role": "assistant", "content": ai_response}
            )
        
        return {"output": ai_response}
    except Exception as e:
        return {"error": str(e)}

@app.get("/whales")
async def whales_endpoint():
    whales = get_whales()
    print(whales)
    return {"whales": whales}

@app.get("/ping-ts")
async def ping_ts():
    async with httpx.AsyncClient() as client:
        r = await client.get("http://localhost:3000/ping")
        return {"response_from_ts": r.json()}

@app.post("/threads/{thread_id}")
async def process_thread_message(
    thread_id: str = Path(..., description="The ID of the thread"),
    user_message: UserMessage = Body(default=None)
):
    try:
        print(f"Processing thread message for thread ID: {thread_id}")
        print(f"User message: {user_message}")

        # 1. Fetch the latest messages from the thread
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:3000/threads/{thread_id}")
            if response.status_code != 200:
                return {"error": f"Failed to fetch thread messages: {response.text}"}
            
            thread_messages = response.json()
        
        # 2. Process messages and generate AI response
        ai_response = get_chat_ai_response(thread_messages)
        print(f"AI response: {ai_response}")

        # 3. Add AI response to the thread
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://localhost:3000/threads/{thread_id}",
                json={"role": "assistant", "content": ai_response}
            )
            if response.status_code != 201:
                return {"error": f"Failed to add AI response to thread: {response.text}"}
            
            result = response.json()
        
        return {
            "message": "AI response added to thread successfully",
            "response": ai_response,
            "id": result.get("id")
        }
    except Exception as e:
        return {"error": str(e)}
