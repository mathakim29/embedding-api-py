import numpy as np
import httpx
import asyncio
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
from .config import DEFAULT_EMBEDDING_MODEL, DEFAULT_TOP_N, DEFAULT_SIM_METHOD, PCA_COMPONENTS, OLLAMA_URL

# ------------------- Async Embedding -------------------
async def get_embedding(text: str, model: str = DEFAULT_EMBEDDING_MODEL):
    """
    Get embedding for a text using Ollama API.
    """
    async with httpx.AsyncClient() as client:
        r = await client.post(OLLAMA_URL, json={"model": model, "prompt": text})
        data = r.json()
        if "error" in data:
            raise Exception(f"Embedding error: {data['error']}")
        return data["embedding"]

# ------------------- PCA Reduction -------------------
def reduce_dim(vectors):
    """
    Reduce dimensions of vectors using PCA.
    """
    pca = PCA(n_components=PCA_COMPONENTS)
    vectors_np = np.array(vectors)
    reduced = pca.fit_transform(vectors_np)
    return reduced

# ------------------- Similarity / Distance -------------------
def get_top_matches(query_vecs, passage_vecs, top_n=DEFAULT_TOP_N, method=DEFAULT_SIM_METHOD):
    """
    Compute top matching passages given query vectors and passage vectors.
    Supports cosine, euclidean, manhattan, and dot-product methods.
    """
    results = []

    # --- Cosine similarity ---
    if method == "cosine":
        sims = cosine_similarity(query_vecs, passage_vecs)
        ranked = np.argsort(-sims, axis=1)
        for qi, order in enumerate(ranked):
            top_matches = []
            for idx in order[:top_n]:
                top_matches.append({"id": idx, "cosine_similarity": float(sims[qi, idx])})
            results.append(top_matches)

    # --- Euclidean distance ---
    elif method == "euclidean":
        dists = euclidean_distances(query_vecs, passage_vecs)
        ranked = np.argsort(dists, axis=1)
        for qi, order in enumerate(ranked):
            top_matches = []
            for idx in order[:top_n]:
                top_matches.append({"id": idx, "euclidean_distance": float(dists[qi, idx])})
            results.append(top_matches)

    # --- Manhattan distance ---
    elif method == "manhattan":
        dists = np.sum(np.abs(query_vecs[:, None, :] - passage_vecs[None, :, :]), axis=2)
        ranked = np.argsort(dists, axis=1)
        for qi, order in enumerate(ranked):
            top_matches = []
            for idx in order[:top_n]:
                top_matches.append({"id": idx, "manhattan_distance": float(dists[qi, idx])})
            results.append(top_matches)

    # --- Dot product similarity ---
    elif method == "dot":
        sims = np.dot(query_vecs, np.array(passage_vecs).T)
        ranked = np.argsort(-sims, axis=1)
        for qi, order in enumerate(ranked):
            top_matches = []
            for idx in order[:top_n]:
                top_matches.append({"id": idx, "dot_product": float(sims[qi, idx])})
            results.append(top_matches)

    # --- Unknown method ---
    else:
        raise ValueError(f"Unknown method '{method}'")

    return results
