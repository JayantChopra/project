import pytest
import pandas as pd
import json
import tempfile
import os
from unittest.mock import patch
import time
from utils import load_csv, save_json, file_hash, timeit


def test_load_csv_existing():
    # Create a temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('name,age\nAlice,30\nBob,25')
        temp_path = f.name

    try:
        df = load_csv(temp_path)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert df.iloc[0]['name'] == 'Alice'
    finally:
        os.unlink(temp_path)


def test_load_csv_nonexistent():
    with pytest.raises(FileNotFoundError):
        load_csv('/nonexistent/path.csv')


def test_load_csv_empty():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        # Empty file
        temp_path = f.name

    try:
        with pytest.raises(pd.errors.EmptyDataError):
            load_csv(temp_path)
    finally:
        os.unlink(temp_path)


def test_load_csv_malformed():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write('name,age\nAlice')  # Missing value
        temp_path = f.name

    try:
        with pytest.raises(pd.errors.ParserError):
            load_csv(temp_path)
    finally:
        os.unlink(temp_path)


def test_save_json_dict():
    data = {'name': 'Alice', 'age': 30}
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name

    try:
        save_json(data, temp_path)
        with open(temp_path, 'r') as f_read:
            loaded = json.load(f_read)
        assert loaded == data
        assert os.path.exists(temp_path)
    finally:
        os.unlink(temp_path)


def test_save_json_list():
    data = [1, 2, 3]
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name

    try:
        save_json(data, temp_path)
        with open(temp_path, 'r') as f_read:
            loaded = json.load(f_read)
        assert loaded == data
    finally:
        os.unlink(temp_path)


def test_save_json_non_serializable():
    data = {1, 2, 3}  # set is not JSON serializable
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name

    try:
        with pytest.raises(TypeError):
            save_json(data, temp_path)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_save_json_parent_dir():
    # Test creating parent directories
    temp_dir = tempfile.mkdtemp()
    sub_dir = os.path.join(temp_dir, 'sub')
    path = os.path.join(sub_dir, 'test.json')
    data = {'test': True}

    try:
        save_json(data, path)
        assert os.path.exists(path)
        with open(path, 'r') as f:
            loaded = json.load(f)
        assert loaded == data
    finally:
        os.unlink(path)
        os.rmdir(sub_dir)
        os.rmdir(temp_dir)


def test_file_hash():
    content = b'Hello, world!'
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        expected_hash = 'dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f'
        assert file_hash(temp_path) == expected_hash
    finally:
        os.unlink(temp_path)


def test_file_hash_nonexistent():
    with pytest.raises(FileNotFoundError):
        file_hash('/nonexistent/file.txt')


def test_timeit_basic():
    @timeit
    def test_func():
        time.sleep(0.1)
        return 'done'

    result = test_func()
    assert result == 'done'


def test_timeit_preserves_name():
    @timeit
    def original_func():
        pass

    assert original_func.__name__ == 'original_func'
    assert original_func.__doc__ is None  # Assuming no doc


# To test the print, we can use capsys in pytest, but for simplicity, above is basic.
