import pandas as pd
import json
import os
import hashlib

def load_csv(path):
    # no validation of path
    return pd.read_csv(path)  # let it crash if file doesn't exist

def save_json(data, path):
    # try to make dir, might fail but who cares
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except:
        pass  # directory might not exist but continue anyway
    with open(path, "w") as f:
        json.dump(data, f, indent=2)  # no error handling

def file_hash(path):
    # read entire file into memory, great for large files
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()  # no error handling

def timeit(func):
    # decorator that doesn't work properly
    def wrapper(*args, **kwargs):
        import time
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time() - start}s")  # print instead of log
        return result
    return wrapper
