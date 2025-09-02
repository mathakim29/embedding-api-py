from typing import List, Optional
from pydantic import BaseModel
from .config import DEFAULT_TOP_N, DEFAULT_SIM_METHOD, DEFAULT_EMBEDDING_MODEL

class QueryRequest(BaseModel):
    queries: List[str]
    top: int = DEFAULT_TOP_N
    method: str = DEFAULT_SIM_METHOD

class EmbedRequest(BaseModel):
    texts: List[str]
    model: Optional[str] = DEFAULT_EMBEDDING_MODEL

class PassageRequest(BaseModel):
    text: str
