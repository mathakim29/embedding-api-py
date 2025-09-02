import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))  # make main.py importable

import pytest
import asyncio
from fastapi.testclient import TestClient
import main
from app import db

@pytest.fixture(scope="module")
def setup_db():
    db.init_passage_db()
    return True

@pytest.fixture(scope="module")
def client():
    with TestClient(main.app) as c:
        yield c

def test_post_and_get_passage(setup_db, client):
    # POST a passage
    r = client.post("/passages", json={"text": "Hello world"})
    assert r.status_code == 200
    pid = r.json()["id"]

    # GET passages
    r2 = client.get("/passages")
    assert r2.status_code == 200
    assert any(p["id"] == pid for p in r2.json())
