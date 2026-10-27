from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
import uvicorn
import faiss
import pickle
import numpy as np
import requests
import time
from sentence_transformers import SentenceTransformer

# --- 1. INITIALIZE THE OFFLINE AI (Runs once when server starts) ---
print("Loading AI model and offline database...")
embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
index = faiss.read_index("emergency_index.faiss")

with open("metadata.pkl", "rb") as f:
    data = pickle.load(f)
    documents = data["documents"]
    metadata = data["metadata"]
print("Server ready!")

app = FastAPI()

# --- 2. DATA MODEL FOR USER QUESTIONS ---
class UserQuery(BaseModel):
    question: str

# --- 3. THE RAG API ENDPOINT ---
@app.post("/api/ask")
async def ask_ai(query: UserQuery):
    start_time = time.time()
    
    # Embed and search
    query_vector = embedding_model.encode([query.question]).astype("float32")
    distances, indices = index.search(query_vector, 3)
    
    context_chunks = []
    sources = []
    for i in range(3):
        idx = indices[0][i]
        context_chunks.append(documents[idx])
        sources.append(metadata[idx]["title"])
        
    retrieval_time = round(time.time() - start_time, 2)
    context_text = "\n\n".join(context_chunks)
    
    prompt = f"""
    You are an offline emergency assistant. Answer ONLY using the provided Context.
    If the Context does not contain the answer, reply EXACTLY with: 'Insufficient evidence to provide a safe answer.'
    Always append this disclaimer: 'This system provides automated information and is not a substitute for professional medical assistance.'

    Context:
    {context_text}

    Question: {query.question}
    Answer:
    """
    
    # Send to Local Ollama
    url = "http://localhost:11434/api/generate"
    payload = {"model": "llama3.2:1b", "prompt": prompt, "stream": False}
    
    try:
        response = requests.post(url, json=payload)
        ai_answer = response.json().get("response", "Error generating response.")
    except:
        ai_answer = "CRITICAL ERROR: Could not connect to local AI model."
        
    generation_time = round(time.time() - start_time - retrieval_time, 2)
    
    # Log to terminal for judges
    print(f"\n[METRICS] Retrieval: {retrieval_time}s | LLM Generation: {generation_time}s")
        
    return {
        "answer": ai_answer, 
        "sources": sources,
        "retrieval_time": retrieval_time,
        "generation_time": generation_time
    }


@app.api_route("/{path:path}", methods=["GET", "POST", "HEAD"])
async def captive_portal_catch_all(request: Request, path: str):
    if path in ["", "/", "api/ask"]:
        return await portal_home()
    return RedirectResponse(url="http://192.168.137.1/", status_code=302)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
