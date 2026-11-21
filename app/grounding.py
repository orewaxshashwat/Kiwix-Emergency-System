from typing import List, Dict, Tuple

FALLBACK_MESSAGE = (
    "Insufficient evidence in local offline archives to provide a safe answer. "
    "Please stabilize the patient using basic first-aid fundamentals and seek immediate "
    "professional medical assistance or rescue personnel."
)

MEDICAL_DISCLAIMER_SUFFIX = (
    "\n\n[Emergency Caution]: This guidance is grounded in offline medical references. "
    "Seek professional emergency rescue immediately for life-threatening conditions."
)

def evaluate_grounding(sources: List[Dict]) -> Tuple[bool, str]:
    """
    Validates whether the retrieved passages are sufficient to answer safely.
    Enforces the brief's requirement for cautious answers and fallback handling.
    """
    if not sources:
        return False, FALLBACK_MESSAGE

    combined_context = "\n\n".join([
        f"--- Source: {doc['title']} ---\n{doc['content']}"
        for doc in sources
    ])
    return True, combined_context

def format_system_prompt(context: str) -> str:
    """Builds a constrained prompt enforcing strict offline-source grounding."""
    return (
        "You are an offline emergency medical and survival assistant operating in a disconnected zone.\n"
        "Rules you must strictly follow:\n"
        "1. Answer ONLY using the facts from the verified offline sources below.\n"
        "2. Do NOT extrapolate, hallucinate, or recommend unverified medications or invasive procedures.\n"
        "3. Keep instructions concise, numbered, and actionable for someone under extreme stress.\n"
        "4. If the sources do not contain enough direct facts, state that you do not have sufficient information.\n\n"
        f"Verified Offline Sources:\n{context}"
    )