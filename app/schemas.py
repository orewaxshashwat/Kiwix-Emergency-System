from pydantic import BaseModel
from typing import List, Optional

class QueryRequest(BaseModel):
    prompt: str

class SourceItem(BaseModel):
    title: str
    snippet: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceItem]