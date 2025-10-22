import unittest
import os
import pandas as pd
from unittest.mock import Mock, patch
from processor import DataProcessor

class TestDataProcessor(unittest.TestCase):
    def setUp(self):
        self.sample_data = pd.DataFrame({
            'A': [1, 2, None, 1],
            'B': [5, 6, 7, 5],
            'C': [1, 2, 3, 1]
        })
    
    def test_init(self):
        processor = DataProcessor(self.sample_data)
        pd.testing.assert_frame_equal(processor.data, self.sample_data)
    
    def test_clean(self):
        processor = DataProcessor(self.sample_data)
        cleaned = processor.clean()
        expected_data = pd.DataFrame({
            'A': [1, 2],
            'B': [5, 6],
            'C': [1, 2]
        })
        pd.testing.assert_frame_equal(cleaned.data.reset_index(drop=True), expected_data)
        self.assertIs(cleaned, processor)
    
    def test_summarize(self):
        processor = DataProcessor(self.sample_data)
        summary = processor.summarize()
        self.assertIn('rows', summary)
        self.assertEqual(summary['rows'], 2)
        self.assertIn('columns', summary)
        self.assertEqual(summary['columns'], ['A', 'B', 'C'])
        self.assertIn('numeric_summary', summary)
        self.assertIn('A', summary['numeric_summary'])
    
    @patch('processor.DataAnalyzer')
    def test_detect_anomalies(self, MockAnalyzer):
        mock_analyzer = Mock()
        mock_outliers = {'A': [0]}
        mock_analyzer.detect_outliers.return_value = mock_outliers
        MockAnalyzer.return_value = mock_analyzer
        
        processor = DataProcessor(self.sample_data)
        result = processor.detect_anomalies(z_threshold=2.5)
        self.assertEqual(result, mock_outliers)
        MockAnalyzer.assert_called_once_with(processor.data)
        mock_analyzer.detect_outliers.assert_called_once_with(2.5)
    
    def test_export_cleaned(self):
        test_path = "test_output.csv"
        processor = DataProcessor(self.sample_data)
        saved_path = processor.export_cleaned(test_path)
        self.assertEqual(saved_path, test_path)
        
        exported_data = pd.read_csv(test_path)
        expected_data = pd.DataFrame({
            'A': [1, 2],
            'B': [5, 6],
            'C': [1, 2]
        })
        pd.testing.assert_frame_equal(exported_data.reset_index(drop=True), expected_data)
        
        # Clean up
        if os.path.exists(test_path):
            os.remove(test_path)

if __name__ == '__main__':
    unittest.main()
