import asyncio, numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from app import db
from app import embed as embeddings
from app.models import QueryRequest, EmbedRequest, PassageRequest
from app.config import DEFAULT_EMBEDDING_MODEL

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup_event():
    db.init_passage_db()

@app.get("/passages")
async def get_passages():
    return db.load_passages()

@app.post("/passages")
async def post_passage(req: PassageRequest):
    pid = db.insert_passage(req.text)
    try:
        vector = await embeddings.get_embedding(req.text)
        db.save_embedding(pid, DEFAULT_EMBEDDING_MODEL, np.array(vector))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "ok", "id": pid}

@app.post("/query")
async def query_passages(req: QueryRequest):
    passages = db.load_passages()
    if not passages:
        raise HTTPException(status_code=400, detail="No passages in DB")
    p_vecs = []
    for p in passages:
        vec = db.load_embedding(p["id"], DEFAULT_EMBEDDING_MODEL)
        if vec is None:
            vec = np.array(await embeddings.get_embedding("passage: " + p["text"]))
            db.save_embedding(p["id"], DEFAULT_EMBEDDING_MODEL, vec)
        p_vecs.append(vec)

    q_vecs = [np.array(await embeddings.get_embedding("query: "+q)) for q in req.queries]
    top_matches = embeddings.get_top_matches(np.array(q_vecs), np.array(p_vecs), top_n=req.top, method=req.method)

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
        embeddings_list = await asyncio.gather(*(embeddings.get_embedding(t, model=req.model) for t in req.texts))
        return [{"text": t, "embedding": emb} for t, emb in zip(req.texts, embeddings_list)]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
