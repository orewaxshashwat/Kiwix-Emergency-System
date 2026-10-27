import faiss
import pickle
import numpy as np
import os
import sys
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from libzim.reader import Archive

# Your exact path
zim_path = r"C:\Users\shash\OneDrive\Documents\kiwix\bitcoin_en_all_maxi_2021-03.zim"

print(f"0. Checking file path: {zim_path}")
if not os.path.exists(zim_path):
    print("CRITICAL ERROR: Windows cannot find this file. Please check the folder to make sure it is actually there and named correctly.")
    sys.exit(1) # Stop the script immediately

print("1. Loading embedding model...")
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

print("2. Opening ZIM file...")
documents = []
metadata = []

try:
    archive = Archive(zim_path)
    print(f"Successfully opened! Total entries inside: {archive.all_entry_count}")
    
    for i in range(archive.all_entry_count):
        entry = archive._get_entry_by_id(i)
        item = entry.get_item()
        
        # # We only want text/html content, skip images/metadata, pta nhi but mera dimag khrha h isliye images skip kro low resource use k liye
        if item.mimetype != "text/html":
            continue
            
        html_content = bytes(item.content)
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
        
        if len(text) > 200: # Skip useless fragments
            chunks = [text[j:j+500] for j in range(0, len(text), 500)]
            for chunk in chunks:
                documents.append(chunk)
                metadata.append({"title": item.path, "source": zim_path})
        
        
except Exception as e:
    print(f"\nCRITICAL ZIM PARSING ERROR: {e}")
    sys.exit(1) # Stop the script immediately

# Prevent the IndexError crash
if len(documents) == 0:
    print("\nERROR: Successfully opened ZIM, but found 0 HTML text articles inside it.")
    sys.exit(1)

print(f"3. Embedding {len(documents)} text chunks...")
embeddings = model.encode(documents, show_progress_bar=True)
embeddings = np.array(embeddings).astype("float32")

print("4. Saving FAISS Vector Database locally...")
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

faiss.write_index(index, "emergency_index.faiss")
with open("metadata.pkl", "wb") as f:
    pickle.dump({"documents": documents, "metadata": metadata}, f)
    
print("Success! You now have a standalone offline knowledge base.")