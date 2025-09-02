import os
import io
import json
import sqlite3
from pathlib import Path
from typing import List, Optional

import numpy as np
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles



# ------------------- Load .env -------------------
load_dotenv()
for key, value in os.environ.items():
    globals()[key] = value

# ------------------- Constants -------------------
DB_PATH = Path("passages.db")

# ------------------- Database -------------------
def init_passage_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS passages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS embeddings (
            passage_id INTEGER NOT NULL,
            model TEXT NOT NULL,
            vector BLOB NOT NULL,
            PRIMARY KEY (passage_id, model),
            FOREIGN KEY (passage_id) REFERENCES passages(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

def insert_passage(text: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO passages (text) VALUES (?)", (text,))
    pid = cur.lastrowid
    conn.commit()
    conn.close()
    return pid

def load_passages():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, text FROM passages")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "text": r[1]} for r in rows]

def save_embedding(passage_id: int, model: str, vector: np.ndarray):
    buf = io.BytesIO()
    np.save(buf, vector)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO embeddings (passage_id, model, vector)
        VALUES (?, ?, ?)
    """, (passage_id, model, buf.getvalue()))
    conn.commit()
    conn.close()

def load_embedding(passage_id: int, model: str) -> Optional[np.ndarray]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT vector FROM embeddings WHERE passage_id=? AND model=?", (passage_id, model))
    row = cur.fetchone()
    conn.close()
    if row:
        buf = io.BytesIO(row[0])
        return np.load(buf)
    return None

# ------------------- Embeddings -------------------
async def get_embedding(text: str, model: str = DEFAULT_EMBEDDING_MODEL) -> List[float]:
    async with httpx.AsyncClient() as client:
        r = await client.post(OLLAMA_URL, json={"model": model, "prompt": text})
        data = r.json()
        if "error" in data:
            raise Exception(f"Embedding error: {data['error']}")
        return data["embedding"]

# ------------------- PCA -------------------
def reduce_dim(vectors: List[List[float]]) -> np.ndarray:
    pca = PCA(n_components=PCA_COMPONENTS)
    return pca.fit_transform(np.array(vectors))

# ------------------- Similarity / Distance -------------------
def get_top_matches(query_vecs, passage_vecs, top_n=DEFAULT_TOP_N, method=DEFAULT_SIM_METHOD):
    results = []

    if method == "cosine":
        sims = cosine_similarity(query_vecs, passage_vecs)
        ranked = np.argsort(-sims, axis=1)
        for qi, order in enumerate(ranked):
            top_idxs = order[:top_n]
            matches = [{"id": idx, "cosine_similarity": float(sims[qi, idx])} for idx in top_idxs]
            results.append(matches)

    elif method == "euclidean":
        dists = euclidean_distances(query_vecs, passage_vecs)
        ranked = np.argsort(dists, axis=1)
        for qi, order in enumerate(ranked):
            top_idxs = order[:top_n]
            matches = [{"id": idx, "euclidean_distance": float(dists[qi, idx])} for idx in top_idxs]
            results.append(matches)

    elif method == "manhattan":
        dists = np.sum(np.abs(query_vecs[:, None, :] - passage_vecs[None, :, :]), axis=2)
        ranked = np.argsort(dists, axis=1)
        for qi, order in enumerate(ranked):
            top_idxs = order[:top_n]
            matches = [{"id": idx, "manhattan_distance": float(dists[qi, idx])} for idx in top_idxs]
            results.append(matches)

    elif method == "dot":
        sims = np.dot(query_vecs, np.array(passage_vecs).T)
        ranked = np.argsort(-sims, axis=1)
        for qi, order in enumerate(ranked):
            top_idxs = order[:top_n]
            matches = [{"id": idx, "dot_product": float(sims[qi, idx])} for idx in top_idxs]
            results.append(matches)
    else:
        raise ValueError(f"Unknown method '{method}'")
    return results

# ------------------- Pydantic Models -------------------
class QueryRequest(BaseModel):
    queries: List[str]
    top: int = DEFAULT_TOP_N
    method: str = DEFAULT_SIM_METHOD

class EmbedRequest(BaseModel):
    texts: List[str]
    model: Optional[str] = DEFAULT_EMBEDDING_MODEL

class PassageRequest(BaseModel):
    text: str

# ------------------- FastAPI App -------------------
app = FastAPI()

# --- load html sandbox ---
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup_event():
    init_passage_db()

# ------------------- Endpoints -------------------
@app.get("/passages")
async def get_passages():
    return load_passages()

@app.post("/passages")
async def post_passage(req: PassageRequest):
    pid = insert_passage(req.text)
    try:
        vector = await get_embedding(req.text)
        save_embedding(pid, DEFAULT_EMBEDDING_MODEL, np.array(vector))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "ok", "id": pid}

@app.post("/query")
async def query_passages(req: QueryRequest):
    passages = load_passages()
    if not passages:
        raise HTTPException(status_code=400, detail="No passages in DB")
    p_texts = [p["text"] for p in passages]
    p_vecs = []
    for pid, text in zip([p["id"] for p in passages], p_texts):
        vec = load_embedding(pid, DEFAULT_EMBEDDING_MODEL)
        if vec is None:
            vec = np.array(await get_embedding("passage: "+text))
            save_embedding(pid, DEFAULT_EMBEDDING_MODEL, vec)
        p_vecs.append(vec)

    q_vecs = [np.array(await get_embedding("query: "+q)) for q in req.queries]
    top_matches = get_top_matches(np.array(q_vecs), np.array(p_vecs), top_n=req.top, method=req.method)

    results = []
    for qi, q in enumerate(req.queries):
        matches = []
        for m in top_matches[qi]:
            idx = m["id"]
            entry = {"id": passages[idx]["id"], "text": passages[idx]["text"]}
            entry.update({k: v for k, v in m.items() if k != "id"})
            matches.append(entry)
        results.append({"query": q, "matches": matches})
    return results

@app.post("/embed")
async def embed_texts(req: EmbedRequest):
    try:
        embeddings = await asyncio.gather(*(get_embedding(text, model=req.model) for text in req.texts))
        return [{"text": t, "embedding": emb} for t, emb in zip(req.texts, embeddings)]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
