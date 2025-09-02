import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))  # make main.py importable

import pytest
import io
import sqlite3
import numpy as np
from rich.console import Console
from rich.table import Table
from app import db

console = Console()

def test_list_all_passages_rich():
    """
    Display all passages and embeddings in a rich table:
    ID | PASSAGE | MODEL | EMBEDDING
    """
    conn = sqlite3.connect(db.DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, p.text, e.model, e.vector
        FROM passages p
        LEFT JOIN embeddings e ON p.id = e.passage_id
        ORDER BY p.id
    """)
    rows = cur.fetchall()
    conn.close()

    table = Table(title="Passages Database")

    table.add_column("ID", style="cyan", justify="right")
    table.add_column("Passage", style="magenta")
    table.add_column("Model", style="green")
    table.add_column("Embedding", style="yellow")

    for pid, text, model, vec_blob in rows:
        if vec_blob:
            vec = np.load(io.BytesIO(vec_blob))
            # Convert to string and truncate if too long
            vec_str = np.array2string(vec, precision=3, separator=',', suppress_small=True)
            if len(vec_str) > 60:
                vec_str = vec_str[:57] + "..."
        else:
            vec_str = "None"
        table.add_row(str(pid), text[:50], str(model), vec_str)

    console.print(table)
