# Python Embedding Server API (FastAPI + scikit-learn)

## Overview
This API allows you to store text passages, generate embeddings, and query them by similarity using multiple methods (cosine, euclidean, manhattan, dot).
It also supports dimensionality reduction using PCA by default.
Designed as boilerplate for experimenting with embeddings and similarity search in Python.

## Setup
1. Install [uv - Python project manager](https://docs.astral.sh/uv/getting-started/installation/)

2. Install [Ollama](https://ollama.com/docs/installation)

3. Clone the repo

4. Create a `.env` file with the following (example):

```
DEFAULT_EMBEDDING_MODEL=default-model
OLLAMA_URL=http://localhost:11434/api/embeddings
DEFAULT_TOP_N=5
DEFAULT_SIM_METHOD=cosine
PCA_COMPONENTS=2
```

Note: Please ensure model is installed with `ollama pull {model}`

4. Run the API:

```bash
uv run uvicorn main:app --reload
```

---



## Endpoints

| Endpoint    | Method | Parameter | Type          | Required | Description                                                  | Default                   |
| ----------- | ------ | --------- | ------------- | -------- | ------------------------------------------------------------ | ------------------------- |
| `/passages` | POST   | `text`    | string        | ✅        | Passage text to store and embed                              | —                         |
| `/passages` | GET    | —         | —             | —        | Retrieve all stored passages                                 | —                         |
| `/query`    | POST   | `queries` | list\[string] | ✅        | List of query strings                                        | —                         |
| `/query`    | POST   | `top`     | integer       | ❌        | Number of top matches to return                              | `DEFAULT_TOP_N`           |
| `/query`    | POST   | `method`  | string        | ❌        | Similarity method: `cosine`, `euclidean`, `manhattan`, `dot` | `DEFAULT_SIM_METHOD`      |
| `/embed`    | POST   | `texts`   | list\[string] | ✅        | List of texts to compute embeddings for                      | —                         |
| `/embed`    | POST   | `model`   | string        | ❌        | Embedding model to use                                       | `DEFAULT_EMBEDDING_MODEL` |


### **POST /passages**

Store a passage and compute its embedding.

**Request Body**

```json
{
  "text": "Your passage here"
}
```

**Response**

```json
{
  "status": "ok",
  "id": 1
}
```

**Example (curl)**

```bash
curl -X POST http://127.0.0.1:8000/passages \
-H "Content-Type: application/json" \
-d '{"text": "Hello world"}'
```

---

### **GET /passages**

Retrieve all stored passages.

**Response**

```json
[
  {"id":1,"text":"Hello world"},
  {"id":2,"text":"Another passage"}
]
```

**Example (curl)**

```bash
curl http://127.0.0.1:8000/passages
```

---

### **POST /query**

Query passages by similarity.

**Request Body**

```json
{
  "queries": ["Hello world"],
  "top": 3,
  "method": "cosine"
}
```

**Response**

```json
[
  {
    "query": "Hello world",
    "matches": [
      {"id":1,"text":"Hello world","cosine_similarity":0.98}
    ]
  }
]
```

**Example (curl)**

```bash
curl -X POST http://127.0.0.1:8000/query \
-H "Content-Type: application/json" \
-d '{"queries":["Hello world"],"top":3,"method":"cosine"}'
```

---

### **POST /embed**

Get embeddings for texts without storing them.

**Request Body**

```json
{
  "texts": ["Hello world", "Test text"],
  "model": "default-model"
}
```

**Response**

```json
[
  {"text":"Hello world","embedding":[0.1,0.2,0.3,...]},
  {"text":"Test text","embedding":[0.05,0.2,0.1,...]}
]
```

**Example (curl)**

```bash
curl -X POST http://127.0.0.1:8000/embed \
-H "Content-Type: application/json" \
-d '{"texts":["Hello world","Test text"]'
```

---

## Similarity Methods

* **cosine**: Cosine similarity (default)
* **euclidean**: Euclidean distance
* **manhattan**: Manhattan distance
* **dot**: Dot product

---

## Notes

* Embeddings are stored in SQLite (`passages.db`) with a separate `embeddings` table per model.
* If an embedding does not exist when querying, it is automatically computed and stored.
* PCA dimensionality reduction is applied if configured in `.env`.
