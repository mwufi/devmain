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
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a whale expert. You are given a prompt and you need to respond with a response that is helpful to the user."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content
