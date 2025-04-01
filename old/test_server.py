# /// script
# dependencies = [
#   "requests<3",
#   "rich",
#   "typer",
# ]
# ///

import os
import requests
import json
from rich import print as rprint
import typer
from typing import Optional

app = typer.Typer()

BASE_URL = os.environ.get("TEST_SERVER_URL", "http://localhost:8000")
DEFAULT_MODEL = os.environ.get("TEST_MODEL", "openai/gpt-4o-2024-11-20")

def get_thread(thread_id: str):
    """Get a thread by ID"""
    response = requests.get(f"{BASE_URL}/threads/{thread_id}")
    return response.json() if response.status_code == 200 else None

def create_thread(system_prompt: Optional[str] = None) -> Optional[str]:
    """Create a new thread and return its ID"""
    payload = {}
    if system_prompt:
        payload["systemPrompt"] = system_prompt
        rprint(f"[blue]Using system prompt:[/blue] {system_prompt}")
    
    response = requests.post(f"{BASE_URL}/threads", json=payload)
    if response.status_code == 200:
        return response.json().get("threadId")
    return None

def add_message(thread_id: str, message: str, model: Optional[str] = None):
    """Add a message to a thread"""
    payload = {
        "message": message,
    }
    if model:
        payload["model"] = model
        rprint(f"[blue]Using model:[/blue] {model}")
    
    response = requests.post(
        f"{BASE_URL}/threads/{thread_id}",
        json=payload
    )
    return response.json() if response.status_code == 200 else None

@app.command("new-thread")
def cmd_new_thread(
    system_prompt: Optional[str] = typer.Option(None, "--system", "-s", help="Set system prompt for the thread")
):
    """Create a new thread"""
    thread_id = create_thread(system_prompt)
    if thread_id:
        rprint(f"[green]Created new thread:[/green] {thread_id}")
        if system_prompt:
            rprint(f"[blue]System prompt:[/blue] {system_prompt}")
    else:
        rprint("[red]Failed to create thread[/red]")

@app.command("chat")
def cmd_chat(
    message: str,
    thread: str,
    model: Optional[str] = typer.Option(None, help="Override the model to use")
):
    """Send a message to a thread"""
    rprint(f"\n[blue]Thread ID:[/blue] {thread}")
    rprint(f"[blue]Sending message:[/blue] {message}")
    
    # Use model from environment or command line
    selected_model = model or DEFAULT_MODEL
    
    # First, verify the thread exists
    thread_data = get_thread(thread)
    if not thread_data:
        rprint("[red]Thread not found[/red]")
        return

    # Send the message
    response = add_message(thread, message, selected_model)
    if response:
        # Show the conversation
        for msg in response["messages"]:
            color = "green" if msg["role"] == "assistant" else "yellow"
            rprint(f"\n[{color}]{msg['role']}:[/{color}] {msg['content']}")
    else:
        rprint("[red]Failed to send message[/red]")

@app.command("show")
def cmd_show(thread: str):
    """Show all messages in a thread"""
    thread_data = get_thread(thread)
    if not thread_data:
        rprint("[red]Thread not found[/red]")
        return

    rprint(f"\n[blue]Thread ID:[/blue] {thread}")
    for msg in thread_data["messages"]:
        color = "green" if msg["role"] == "assistant" else "yellow"
        rprint(f"\n[{color}]{msg['role']}:[/{color}] {msg['content']}")

if __name__ == "__main__":
    app() 