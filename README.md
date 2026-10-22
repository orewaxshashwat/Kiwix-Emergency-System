# Kiwix-Emergency-System
An offline-first emergency information appliance that combines Kiwix .zim archives with local Retrieval-Augmented Generation (RAG) to serve source-grounded medical guidance through a zero-install Wi-Fi captive portal.
*** The Problem**
During natural disasters, power grid failures, or isolated wilderness emergencies, access to the internet and cellular networks is instantly severed. This leaves affected individuals without access to critical first-aid, survival, or disaster-response information precisely when they need it most. Traditional emergency apps require proactive installation before a crisis occurs, rendering them useless to the general public post-disaster.

*** The Solution**
This project is an autonomous, offline-first emergency information appliance designed to run on resource-constrained edge hardware (like a Raspberry Pi or an offline Windows/Linux laptop).

By broadcasting a local Wi-Fi hotspot and utilizing DNS interception, the system acts as a captive portal. Any user within range can connect using their smartphone—without downloading any apps—and ask natural-language questions regarding medical or survival scenarios.

* **How It Works (The RAG Pipeline)**
To ensure absolute accuracy and safety without internet access, the system utilizes a specialized local Retrieval-Augmented Generation (RAG) architecture:

**Offline Knowledge:** The system parses and indexes highly compressed Kiwix .zim archives (such as MedlinePlus or Wikipedia Medical).

**Edge Inference:** When a user submits a query via the captive portal, a local FAISS vector database retrieves the most relevant offline text chunks using sentence-transformers.

**Source-Grounded Generation:** A lightweight, quantized local LLM (Llama 3.2 1B via Ollama) processes the chunks. It is strictly prompted to synthesize an answer only from the retrieved offline data, directly citing its sources to the user.

* **Safety & Constraints**
Designed strictly for emergency medical environments, the system features a hard-coded "insufficient-evidence fallback." If the local database lacks the specific medical knowledge required to answer a query safely, the LLM refuses to hallucinate and defaults to a cautious warning. The entire pipeline operates with zero cloud APIs, zero external dependencies at runtime, and strict optimizations for limited CPU and RAM constraints.
