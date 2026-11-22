from app.retrieval import search_offline_index
from app.grounding import evaluate_grounding

def test_retrieval_returns_relevant_doc():
    results = search_offline_index("burns scalds water")
    assert len(results) > 0
    assert "Burns" in results[0]["title"]

def test_fallback_on_unsupported_query():
    results = search_offline_index("quantum physics dark matter particle")
    is_grounded, message = evaluate_grounding(results)
    assert is_grounded is False
    assert "Insufficient evidence" in message