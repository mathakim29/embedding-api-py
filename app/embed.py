import numpy as np, httpx, asyncio
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
from .config import DEFAULT_EMBEDDING_MODEL, DEFAULT_TOP_N, DEFAULT_SIM_METHOD, PCA_COMPONENTS, OLLAMA_URL

async def get_embedding(text: str, model: str = DEFAULT_EMBEDDING_MODEL):
    async with httpx.AsyncClient() as client:
        r = await client.post(OLLAMA_URL, json={"model": model, "prompt": text})
        data = r.json()
        if "error" in data:
            raise Exception(f"Embedding error: {data['error']}")
        return data["embedding"]

def reduce_dim(vectors):
    pca = PCA(n_components=PCA_COMPONENTS)
    return pca.fit_transform(np.array(vectors))

def get_top_matches(query_vecs, passage_vecs, top_n=DEFAULT_TOP_N, method=DEFAULT_SIM_METHOD):
    results = []
    if method == "cosine":
        sims = cosine_similarity(query_vecs, passage_vecs)
        ranked = np.argsort(-sims, axis=1)
        for qi, order in enumerate(ranked):
            results.append([{"id": idx, "cosine_similarity": float(sims[qi, idx])} for idx in order[:top_n]])
    elif method == "euclidean":
        dists = euclidean_distances(query_vecs, passage_vecs)
        ranked = np.argsort(dists, axis=1)
        for qi, order in enumerate(ranked):
            results.append([{"id": idx, "euclidean_distance": float(dists[qi, idx])} for idx in order[:top_n]])
    elif method == "manhattan":
        dists = np.sum(np.abs(query_vecs[:, None, :] - passage_vecs[None, :, :]), axis=2)
        ranked = np.argsort(dists, axis=1)
        for qi, order in enumerate(ranked):
            results.append([{"id": idx, "manhattan_distance": float(dists[qi, idx])} for idx in order[:top_n]])
    elif method == "dot":
        sims = np.dot(query_vecs, np.array(passage_vecs).T)
        ranked = np.argsort(-sims, axis=1)
        for qi, order in enumerate(ranked):
            results.append([{"id": idx, "dot_product": float(sims[qi, idx])} for idx in order[:top_n]])
    else:
        raise ValueError(f"Unknown method '{method}'")
    return results
