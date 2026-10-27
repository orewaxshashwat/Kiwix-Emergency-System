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

# --- 4. THE CAPTIVE PORTAL FRONTEND ---
@app.get("/", response_class=HTMLResponse)
async def portal_home():
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Emergency Offline Node</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: sans-serif; background: #f3f4f6; padding: 20px; }
                .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 400px; margin: 0 auto; }
                h1 { color: #dc2626; font-size: 24px; margin-bottom: 10px; }
                input { width: 100%; padding: 10px; margin-bottom: 10px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 5px; }
                button { width: 100%; padding: 10px; background: #2563eb; color: white; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; }
                #result { margin-top: 20px; padding: 10px; background: #f9fafb; border-left: 4px solid #2563eb; display: none; }
                .source-list { font-size: 12px; color: #6b7280; margin-top: 10px; }
                .metrics-display { font-size: 11px; color: #10b981; margin-top: 5px; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>Emergency Assistant</h1>
                <p>Connected to local offline network. No internet required.</p>
                <input type="text" id="question" placeholder="Ask a medical or survival question...">
                <button onclick="askQuestion()">Search Local Database</button>
                
                <div id="result">
                    <strong>Answer:</strong>
                    <div class="metrics-display" id="metrics-text"></div>
                    <p id="answer-text" style="margin-top: 5px;">Loading...</p>
                    <div class="source-list" id="sources-text"></div>
                </div>
            </div>

            <script>
                async function askQuestion() {
                    const q = document.getElementById("question").value;
                    const resultDiv = document.getElementById("result");
                    const answerText = document.getElementById("answer-text");
                    const sourcesText = document.getElementById("sources-text");
                    const metricsText = document.getElementById("metrics-text");
                    
                    if (!q) return;
                    
                    resultDiv.style.display = "block";
                    answerText.innerText = "Searching offline database...";
                    sourcesText.innerText = "";
                    metricsText.innerText = "";
                    
                    try {
                        const res = await fetch("/api/ask", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ question: q })
                        });
                        const data = await res.json();
                        answerText.innerText = data.answer;
                        metricsText.innerText = `⏱ Retrieval: ${data.retrieval_time}s | Generation: ${data.generation_time}s`;
                        sourcesText.innerHTML = "<strong>Sources used:</strong><br>" + data.sources.join("<br>");
                    } catch (e) {
                        answerText.innerText = "Error connecting to local server.";
                    }
                }
            </script>
        </body>
    </html>
    """

# --- 5. THE CAPTIVE PORTAL CATCH-ALL ROUTE ---
@app.api_route("/{path:path}", methods=["GET", "POST", "HEAD"])
async def captive_portal_catch_all(request: Request, path: str):
    if path in ["", "/", "api/ask"]:
        return await portal_home()
    return RedirectResponse(url="http://192.168.137.1/", status_code=302)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)