from pydantic import BaseModel
from typing import List, Optional
from .config import DEFAULT_EMBEDDING_MODEL

class PassageRequest(BaseModel):
    text: str

class EmbedRequest(BaseModel):
    texts: List[str]
    model: Optional[str] = DEFAULT_EMBEDDING_MODEL

class QueryRequest(BaseModel):
    queries: List[str]
    top: int = 5
    method: str = "cosine"
