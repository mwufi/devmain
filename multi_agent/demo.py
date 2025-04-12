from agentlib.master_agent import MasterAgent
import json
import os
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.text import Text
from rich import print as rprint

console = Console()

def format_json_output(data):
    """Format JSON data for display, properly handling newlines"""
    if isinstance(data, str):
        return data.replace('\\n', '\n')
    elif isinstance(data, dict):
        return {k: format_json_output(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [format_json_output(item) for item in data]
    return data

def display_formatted_output(data, title, border_style="blue"):
    """Display formatted output in a panel"""
    if isinstance(data, dict):
        # For JSON objects, format them nicely
        formatted_data = format_json_output(data)
        # Convert to a pretty string with proper indentation
        content = json.dumps(formatted_data, indent=2)
        # Create a syntax object for proper code highlighting
        syntax = Syntax(content, "json", theme="monokai", word_wrap=True)
        console.print(Panel(syntax, title=title, border_style=border_style))
    else:
        # For plain text, just format the newlines
        formatted_text = format_json_output(str(data))
        console.print(Panel(formatted_text, title=title, border_style=border_style))

async def chat_with_agent(master: MasterAgent):
    console.print(Panel.fit(
        "[bold green]Welcome to the Multi-Agent System![/bold green]\n"
        "Type 'exit' to quit, 'help' for available commands.",
        title="Multi-Agent Chat"
    ))
    
    while True:
        user_input = Prompt.ask("\n[bold blue]You[/bold blue]")
        
        if user_input.lower() == 'exit':
            break
            
        if user_input.lower() == 'help':
            console.print(Panel.fit(
                "[bold]Available Commands:[/bold]\n"
                "- [cyan]think <topic>[/cyan] - Ask the agent to think about a topic\n"
                "- [cyan]consult <colleague> <topic>[/cyan] - Consult a colleague\n"
                "- [cyan]list colleagues[/cyan] - List available colleagues\n"
                "- [cyan]help[/cyan] - Show this help message\n"
                "- [cyan]exit[/cyan] - Exit the chat\n"
                "\nOr just type your request normally!",
                title="Help"
            ))
            continue
            
        if user_input.lower() == 'list colleagues':
            colleagues = master.list_colleagues()
            console.print(Panel.fit(
                "\n".join(f"- [cyan]{colleague}[/cyan]" for colleague in colleagues),
                title="Available Colleagues"
            ))
            continue
            
        # Handle think command
        if user_input.lower().startswith('think '):
            topic = user_input[6:].strip()
            console.print(Panel("[bold yellow]Thinking about:[/bold yellow] " + topic, title="Thinking"))
            result = await master.think(topic)
            display_formatted_output(result, "Thoughts", "green")
            continue
            
        # Handle consult command
        if user_input.lower().startswith('consult '):
            parts = user_input[8:].strip().split(' ', 1)
            if len(parts) != 2:
                console.print("[red]Please specify both colleague and topic[/red]")
                continue
            colleague, topic = parts
            console.print(Panel(f"[bold yellow]Consulting {colleague} about:[/bold yellow] {topic}", title="Consultation"))
            result = await master.consult_colleague(colleague, topic)
            display_formatted_output(result, f"Response from {colleague}", "cyan")
            continue
            
        # Process normal input
        console.print(Panel("[bold yellow]Processing your request...[/bold yellow]", title="Processing"))
        
        # Infer goals
        goals = await master.infer_user_goals(user_input)
        display_formatted_output(goals, "Inferred Goals", "green")
        
        # Create helper
        helper = await master.summon_execution_helper(user_input)
        display_formatted_output(helper, "Helper Created", "blue")
        
        # Simulate helper results
        helper_results = {
            "task": user_input,
            "output": helper.get("response", "Task completed successfully"),
            "status": "completed",
            "details": helper.get("capabilities", "This is a simulated response")
        }
        
        # Evaluate results
        evaluation = await master.evaluate_helper_results(helper_results)
        display_formatted_output(evaluation, "Evaluation", "yellow")

async def main():
    # Create a MasterAgent instance
    master = MasterAgent("DemoMaster")
    
    # Start interactive chat
    await chat_with_agent(master)
    
    console.print("\n[bold green]Thank you for using the Multi-Agent System![/bold green]")

if __name__ == "__main__":
    asyncio.run(main()) 