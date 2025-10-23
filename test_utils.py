import unittest
import tempfile
import os
import shutil
import json
import time
import io
from contextlib import redirect_stdout

import pandas as pd

from utils import load_csv, save_json, file_hash, timeit


class TestUtils(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.csv_path = os.path.join(self.temp_dir, 'test.csv')
        self.json_path = os.path.join(self.temp_dir, 'test.json')
        # Create sample CSV
        df = pd.DataFrame({'a': [1, 2], 'b': [3, 4]})
        df.to_csv(self.csv_path, index=False)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_load_csv(self):
        df = load_csv(self.csv_path)
        self.assertEqual(len(df), 2)
        self.assertEqual(df['a'].tolist(), [1, 2])

    def test_load_csv_not_found(self):
        with self.assertRaises(FileNotFoundError):
            load_csv(os.path.join(self.temp_dir, 'nonexistent.csv'))

    def test_load_csv_empty(self):
        empty_path = os.path.join(self.temp_dir, 'empty.csv')
        with open(empty_path, 'w') as f:
            pass
        df = load_csv(empty_path)
        self.assertEqual(len(df), 0)

    def test_save_json(self):
        data = {'key': 'value', 'list': [1, 2]}
        save_json(data, self.json_path)
        with open(self.json_path, 'r') as f:
            loaded = json.load(f)
        self.assertEqual(loaded, data)

    def test_save_json_nested_dir(self):
        nested_path = os.path.join(self.temp_dir, 'nested', 'test.json')
        data = {'key': 'value'}
        save_json(data, nested_path)
        self.assertTrue(os.path.exists(nested_path))
        with open(nested_path, 'r') as f:
            loaded = json.load(f)
        self.assertEqual(loaded, data)

    def test_save_json_non_serializable(self):
        with self.assertRaises(TypeError):
            save_json(set(), self.json_path)

    def test_file_hash(self):
        file_path = os.path.join(self.temp_dir, 'hashfile.txt')
        with open(file_path, 'w') as f:
            f.write('test content')
        hash_val = file_hash(file_path)
        self.assertEqual(len(hash_val), 64)
        # Test consistency
        hash_val2 = file_hash(file_path)
        self.assertEqual(hash_val, hash_val2)

    def test_file_hash_empty_file(self):
        file_path = os.path.join(self.temp_dir, 'empty.txt')
        with open(file_path, 'w') as f:
            pass
        hash_val = file_hash(file_path)
        self.assertEqual(hash_val, 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')

    def test_file_hash_not_found(self):
        with self.assertRaises(FileNotFoundError):
            file_hash(os.path.join(self.temp_dir, 'nonexistent.txt'))

    def test_timeit(self):
        @timeit
        def test_func(x):
            time.sleep(0.01)  # Small delay to ensure time > 0
            return x * 2

        f = io.StringIO()
        with redirect_stdout(f):
            result = test_func(5)
        self.assertEqual(result, 10)
        output = f.getvalue()
        self.assertIn('test_func executed in', output)
        self.assertRegex(output, r'\d\.\d{3}s')


if __name__ == '__main__':
    unittest.main()
