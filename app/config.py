import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
for key, value in os.environ.items():
    globals()[key] = value

DB_PATH = Path("passages.db")
