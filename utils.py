import pandas as pd
import json
import os
import hashlib
import time
from functools import wraps

def load_csv(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    return pd.read_csv(path)

def save_json(data, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def file_hash(path: str):
    """Return SHA-256 hash of a file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    hasher = hashlib.sha256()
    buf_size = 4096
    with open(path, "rb") as f:
        while True:
            chunk = f.read(buf_size)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()

def timeit(func):
    """Decorator to measure function runtime."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} executed in {end - start:.3f}s")
        return result
    return wrapper