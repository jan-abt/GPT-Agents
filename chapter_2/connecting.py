import os
from openai import OpenAI
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
# Ensure the API key is available
if not api_key:
    raise ValueError("No API key found. Please check your .env file.")
client = OpenAI(api_key=api_key)


# Example function to query ChatGPT
def ask_chatgpt(user_messages):
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gemini-3.5-flash"),
        messages=user_messages,
        temperature=0.7,
        )       
    return response.choices[0].message.content


messages=[
    {
        "role": "system",
        "content": "You are a helpful assistant."
    },
    {
        "role": "user",
        "content": "What is the capital of France?"
    }
]
response = ask_chatgpt(messages)
print(response)
