import pandas as pd
import json
import os
import hashlib
import time
from typing import Any
from functools import wraps


def load_csv(path: str) -> pd.DataFrame:
    """
    Load data from a CSV file into a pandas DataFrame.

    Args:
        path (str): Path to the CSV file.

    Returns:
        pd.DataFrame: A DataFrame containing the data from the CSV.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        pd.errors.EmptyDataError: If the file is empty.
        pd.errors.ParserError: If there is an error parsing the CSV.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    return pd.read_csv(path)


def save_json(data: Any, path: str) -> None:
    """
    Save the given data to a JSON file at the specified path.

    Args:
        data (Any): The data to serialize as JSON. Must be JSON serializable.
        path (str): The file path where the JSON will be saved.

    Raises:
        TypeError: If data is not JSON serializable.
        IOError: If there is an error writing the file.

    Note:
        Parent directories are created if they do not exist.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def file_hash(path: str) -> str:
    """
    Compute and return the SHA-256 hash of a file's contents.

    This function reads the file in chunks to handle large files efficiently.

    Args:
        path (str): The path to the file to hash.

    Returns:
        str: The SHA-256 hash as a hexadecimal string.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    hasher = hashlib.sha256()
    chunk_size = 64 * 1024  # 64KB
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def timeit(func):
    """
    A decorator that times the execution of a function and prints the duration.

    This decorator preserves the original function's metadata using functools.wraps.

    Args:
        func (callable): The function to be decorated.

    Returns:
        callable: The wrapped function.

    Example:
        @timeit
        def my_function():
            time.sleep(1)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} executed in {end - start:.3f}s")
        return result
    return wrapper
