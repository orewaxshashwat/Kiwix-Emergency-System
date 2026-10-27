import faiss
import requests
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

print("Loading AI model and offline database...")
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
index = faiss.read_index("emergency_index.faiss")

with open("metadata.pkl", "rb") as f:
    data = pickle.load(f)
    documents = data["documents"]
    metadata = data["metadata"]

print("\nSystem ready! Type 'exit' to quit.")

# Start an infinite loop for continuous terminal chat
while True:
    query = input("\n[USER QUERY]: ")
    if query.lower() in ['exit', 'quit']:
        break

    # Embed the query and search FAISS
    query_vector = model.encode([query]).astype("float32")
    k = 3 # Retrieve top 3 matches
    distances, indices = index.search(query_vector, k)

    context_chunks = []
    print("--- RETRIEVED OFFLINE SOURCES ---")
    for i in range(k):
        idx = indices[0][i]
        chunk = documents[idx]
        source = metadata[idx]["title"]
        context_chunks.append(chunk)
        print(f"Source {i+1} [{source}]: {chunk[:100]}...")

    # Construct the loosened prompt for the LLM
    context_text = "\n\n".join(context_chunks)

    prompt = f"""
    You are an offline emergency assistant. 
    First, prioritize answering using the provided Context. 
    If the Context does not fully answer the question, you may use your own general knowledge to provide a safe, helpful response. 
    Do not guess medical dosages. Always append this disclaimer: 'This system provides automated information and is not a substitute for professional medical assistance.'

    Context:
    {context_text}

    Question: {query}
    Answer:
    """

    print("\n--- ANALYSING INPUT ---")
        
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "llama3.2:1b",
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            print("\n==============================")
            print("Result:")
            print(result["response"])
            print("==============================\n")
        else:
            print(f"\nError from Local Model: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\nCRITICAL ERROR: Could not connect to Ollama.")
        print("Please open a new PowerShell window and run: ollama run llama3.2:1b")