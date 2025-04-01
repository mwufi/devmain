from openai import OpenAI   
from dotenv import load_dotenv
import os

load_dotenv()

try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None

def get_ai_response(prompt: str) -> str:
    if client is None:
        return "Error: OpenAI client not initialized"

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
