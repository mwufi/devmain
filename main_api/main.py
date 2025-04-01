from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import httpx
import subprocess
import os
from ai import get_ai_response

app = FastAPI()
templates = Jinja2Templates(directory="templates")

print("App starting up!", flush=True)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("shell.html", {"request": request})

@app.post("/execute")
async def execute_command(command: dict):
    try:
        ai_response = get_ai_response(command["command"])
        return {"output": ai_response}
    except Exception as e:
        return {"error": str(e)}


@app.get("/ping-ts")
async def ping_ts():
    async with httpx.AsyncClient() as client:
        r = await client.get("http://localhost:3000/ping")
        return {"response_from_ts": r.json()}
