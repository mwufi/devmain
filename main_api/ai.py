from openai import OpenAI   
from dotenv import load_dotenv
import os
from typing import List, Dict, Any
from loguru import logger
load_dotenv()

try:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY")
    )
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None

def get_ai_response(prompt: str) -> str:
    if client is None:
        return "Error: OpenAI client not initialized"

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a whale expert. You are given a prompt and you need to respond with a response that is helpful to the user."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def get_chat_ai_response(messages: List[Dict[str, Any]], bot_info: Dict[str, Any]) -> str:
    """
    Process a list of chat messages and generate an AI response.
    
    Args:
        messages: A list of message objects with 'role', 'content', and other fields
        
    Returns:
        A string containing the AI's response
    """
    if client is None:
        return "Error: OpenAI client not initialized"
    
    print("bot_info", bot_info)
    
    model = "microsoft/wizardlm-2-8x22b"
    if 'model' in bot_info:
        model = bot_info['model']

    if 'systemPrompt' in bot_info:
        # Format messages for OpenAI API
        formatted_messages = [
            {"role": "developer", "content": bot_info['systemPrompt']}
        ]
    else:
        formatted_messages = [
            {"role": "developer", "content": "You are a helpful and enthusiastic chat assistant named " + bot_info['name'] + ". Respond in a friendly and concise manner. Keep your messages relatively short and engaging."}
        ]
    
    # Add conversation history (limit to last 10 messages to keep context manageable)
    for msg in messages[-10:]:
        if "role" in msg and "content" in msg:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    try:
        response = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://ara.computer", # Optional. Site URL for rankings on openrouter.ai.
                "X-Title": "Ara AI Chat", # Optional. Site title for rankings on openrouter.ai.
            },
            model=model,
            messages=formatted_messages
        )
        if response.error:
            logger.error(f"No response from OpenAI: {response}")
            return f"Sorry, I'm having trouble responding right now. Error: {str(response.error)}"
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error getting AI response: {e}")
        return f"Sorry, I'm having trouble responding right now. Error: {str(e)}"
