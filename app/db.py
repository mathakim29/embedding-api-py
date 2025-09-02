import sqlite3, io
import numpy as np
from .config import DB_PATH

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

def load_embedding(passage_id: int, model: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT vector FROM embeddings WHERE passage_id=? AND model=?", (passage_id, model))
    row = cur.fetchone()
    conn.close()
    if row:
        buf = io.BytesIO(row[0])
        return np.load(buf)
    return None

def load_passages():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, text FROM passages")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "text": r[1]} for r in rows]
