import os
from google import genai
from google.genai import types

def generate(prompt: str, system: str = "", max_tokens: int = 4000, json_mode: bool = False) -> str:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    config = types.GenerateContentConfig(
        system_instruction=system,
        max_output_tokens=max_tokens,
        temperature=0.7
    )
    
    if json_mode:
        config.response_mime_type = "application/json"
        
    response = client.models.generate_content(
        model='gemini-2.5-pro',
        contents=prompt,
        config=config
    )
    return response.text
