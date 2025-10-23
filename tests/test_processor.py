import unittest
import pandas as pd
import os
import tempfile
from unittest.mock import patch, MagicMock
from processor import DataProcessor

class TestDataProcessor(unittest.TestCase):

    def setUp(self):
        # Sample data
        self.sample_data = pd.DataFrame({
            'A': [1, 2, 3, 4, 5],
            'B': [10, 20, 30, 40, 50],
            'C': ['x', 'y', 'x', 'z', 'y']
        })
        # Data with NaNs and duplicates
        self.dirty_data = pd.DataFrame({
            'A': [1, 2, None, 2, 5],
            'B': [10, 20, 30, 20, None],
            'C': ['x', 'y', 'x', 'y', 'z']
        })
        # Empty data
        self.empty_data = pd.DataFrame()

    def test_init(self):
        processor = DataProcessor(self.sample_data)
        self.assertEqual(processor.data.shape, self.sample_data.shape)

    def test_clean_basic(self):
        processor = DataProcessor(self.sample_data.copy())
        cleaned = processor.clean()
        self.assertEqual(cleaned.data.shape, self.sample_data.shape)
        # No NaNs or duplicates in sample

    def test_clean_removes_nans(self):
        processor = DataProcessor(self.dirty_data.copy())
        cleaned = processor.clean()
        expected = pd.DataFrame({
            'A': [1, 5],
            'B': [10, None],  # Wait, no: dropna removes rows with any NaN
            # Actually, dirty_data has NaN in row 2 A, row 4 B, so after dropna: rows 0 and 4? Row 0: 1,10,x; row1:2,20,y; row2:None,30,x -> drop; row3:2,20,y -> duplicate of row1; row4:5,None,z -> drop because None in B
            # So only row0 and row1? Row1:2,20,y; row3:2,20,y duplicate.
            # Row0:1,10,x; row1:2,20,y; row4 has None in B, so dropped.
            # So after dropna: row0,1,3; then drop_duplicates: row0,1 (since 3==1)
            expected_clean = pd.DataFrame({
                'A': [1, 2],
                'B': [10, 20],
                'C': ['x', 'y']
            })
        self.assertTrue(cleaned.data.equals(expected_clean))

    def test_clean_empty_data(self):
        processor = DataProcessor(self.empty_data.copy())
        cleaned = processor.clean()
        self.assertTrue(cleaned.data.empty)

    def test_clean_all_nans(self):
        all_nans = pd.DataFrame({'A': [None, None], 'B': [None, None]})
        processor = DataProcessor(all_nans)
        cleaned = processor.clean()
        self.assertTrue(cleaned.data.empty)

    def test_summarize(self):
        processor = DataProcessor(self.sample_data.copy())
        summary = processor.summarize()
        self.assertIn('rows', summary)
        self.assertIn('columns', summary)
        self.assertIn('numeric_summary', summary)
        self.assertEqual(summary['rows'], 5)
        self.assertEqual(len(summary['columns']), 3)

    def test_summarize_after_clean(self):
        processor = DataProcessor(self.dirty_data.copy())
        summary = processor.summarize()
        self.assertEqual(summary['rows'], 2)  # After cleaning

    def test_detect_anomalies_no_outliers(self):
        processor = DataProcessor(self.sample_data.copy())
        anomalies = processor.detect_anomalies(z_threshold=10)
        self.assertEqual(anomalies, {})  # No outliers with high threshold

    def test_detect_anomalies_with_outliers(self):
        outlier_data = pd.DataFrame({
            'A': [1, 2, 3, 4, 100]  # 100 is outlier
        })
        processor = DataProcessor(outlier_data)
        anomalies = processor.detect_anomalies(z_threshold=2)
        self.assertIn('A', anomalies)
        self.assertEqual(anomalies['A'], [4])  # index 4

    def test_export_cleaned(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'test.csv')
            processor = DataProcessor(self.sample_data.copy())
            exported_path = processor.export_cleaned(path=path)
            self.assertEqual(exported_path, path)
            self.assertTrue(os.path.exists(path))
            exported_df = pd.read_csv(path)
            self.assertTrue(exported_df.equals(self.sample_data))

    def test_export_cleaned_with_dirty_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'test.csv')
            processor = DataProcessor(self.dirty_data.copy())
            exported_path = processor.export_cleaned(path=path)
            self.assertTrue(os.path.exists(path))
            expected = pd.DataFrame({
                'A': [1, 2],
                'B': [10, 20],
                'C': ['x', 'y']
            })
            exported_df = pd.read_csv(path)
            self.assertTrue(exported_df.equals(expected))

if __name__ == '__main__':
    unittest.main()
