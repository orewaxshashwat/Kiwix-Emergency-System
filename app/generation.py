import asyncio
from ollama import AsyncClient

# Make sure this matches the model you are pulling
MODEL_NAME = "llama3.2"

async def generate_offline_answer(query: str, system_prompt: str):
    """
    Generates an answer using the local Ollama model via the AsyncClient.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]

    try:
        # We use AsyncClient to prevent blocking the FastAPI event loop
        response = await AsyncClient().chat(model=MODEL_NAME, messages=messages)
        return response['message']['content']
        
    except Exception as e:
        return f"Local Generation Error: {str(e)}. Please ensure Ollama is running and the model is pulled."