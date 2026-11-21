import os
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()  # loading and setting the api key can be done in one step
client = OpenAI()


# Example function to query ChatGPT
def ask_chatgpt(messages):
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4-1106-preview"),
        messages=messages,
        temperature=0.7,   
        # The book uses {"type": "json_object"}, which LM Studio rejects.
        # "json_schema" is accepted by OpenAI, LM Studio and Gemini. The schema
        # must name its fields: with a bare {"type": "object"}, Gemini returns {}.
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "paris_fact",
                "schema": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"},
                        "interesting_fact": {"type": "string"},
                    },
                    "required": ["city", "interesting_fact"],
                },
            },
        },
        )
    
    return response.choices[0].message.content


messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant and always output JSON."  
        },
    {
        "role": "user",
        "content": "What is the captial of France?"
        },
    {
        "role": "assistant",
        "content": "The capital of France is Paris."
        },
    {
        "role": "user",
        "content": "What is an interesting fact of Paris."
        }
    ]
response = ask_chatgpt(messages)
print(response)
