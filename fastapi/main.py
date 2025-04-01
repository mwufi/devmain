from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import httpx
import subprocess
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("shell.html", {"request": request})


@app.post("/execute")
async def execute_command(command: dict):
    try:
        # Execute the command and capture both stdout and stderr
        result = subprocess.run(
            command["command"], shell=True, capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            return {"output": result.stdout}
        else:
            return {"error": result.stderr or "Command failed"}

    except subprocess.TimeoutExpired:
        return {"error": "Command timed out"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/ping-ts")
async def ping_ts():
    async with httpx.AsyncClient() as client:
        r = await client.get("http://localhost:3000/ping")
        return {"response_from_ts": r.json()}
