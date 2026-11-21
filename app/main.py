from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from pathlib import Path

from app.schemas import QueryRequest, QueryResponse, SourceItem
from app.retrieval import search_offline_index
from app.grounding import evaluate_grounding, format_system_prompt
from app.generation import generate_offline_answer

app = FastAPI(title="Kiwix Emergency Appliance")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

# Mount static folder
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 1. Main User Interface
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>index.html not found in app/static</h1>", status_code=404)
    return HTMLResponse(content=index_file.read_text(encoding="utf-8"))

# 2. Captive Portal OS Probes (Intercepts Apple, Android, and Windows connectivity checks)
@app.get("/generate_204")
@app.get("/gen_204")
@app.get("/hotspot-detect.html")
@app.get("/canonical.html")
@app.get("/ncsi.txt")
@app.get("/connecttest.txt")
async def captive_portal_probe(request: Request):
    return RedirectResponse(url="/", status_code=302)

# 3. RAG Query Endpoint matching frontend app.js
@app.post("/api/query", response_model=QueryResponse)
async def handle_emergency_query(payload: QueryRequest):
    query_text = payload.prompt.strip()
    if not query_text:
        return QueryResponse(
            answer="Please enter a valid emergency question.",
            sources=[]
        )

    # Step 1: Retrieval via SQLite FTS5
    retrieved_docs = search_offline_index(query_text)

    # Step 2: Grounding and Fallback Check
    is_grounded, context_or_fallback = evaluate_grounding(retrieved_docs)

    if not is_grounded:
        return QueryResponse(
            answer=context_or_fallback,
            sources=[]
        )

    # Step 3: Local Offline Generation
    system_prompt = format_system_prompt(context_or_fallback)
    answer = await generate_offline_answer(query_text, system_prompt)

    # Step 4: Source Packaging
    sources_output = [
        SourceItem(
            title=doc["title"],
            snippet=doc["content"][:160] + "..." if len(doc["content"]) > 160 else doc["content"]
        )
        for doc in retrieved_docs
    ]

    return QueryResponse(answer=answer, sources=sources_output)

if __name__ == "__main__":
    import uvicorn
    # Make sure this says "app.main:app"
    uvicorn.run("app.main:app", host="0.0.0.0", port=80, reload=True)