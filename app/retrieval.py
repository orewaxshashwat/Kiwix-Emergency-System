import sqlite3
import re
from typing import List, Dict
from app.config import DB_PATH, RETRIEVAL_LIMIT

def clean_fts_query(query: str) -> str:
    """Sanitize the search query to avoid SQLite FTS syntax errors."""
    tokens = re.findall(r"\b\w+\b", query)
    if not tokens:
        return ""
    # Use OR to maximize recall in offline emergency situations
    return " OR ".join(tokens)

def search_offline_index(query: str, limit: int = RETRIEVAL_LIMIT) -> List[Dict]:
    """Search the local SQLite FTS5 index for matching emergency documentation."""
    if not DB_PATH.exists():
        return []

    fts_query = clean_fts_query(query)
    if not fts_query:
        return []

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        sql = """
            SELECT title, content, bm25(documents) as score
            FROM documents
            WHERE documents MATCH ?
            ORDER BY score ASC
            LIMIT ?
        """
        cursor.execute(sql, (fts_query, limit))
        rows = cursor.fetchall()

        results = []
        for row in rows:
            results.append({
                "title": row[0],
                "content": row[1],
                "score": float(row[2])
            })
        return results
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()