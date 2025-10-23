import unittest
import pandas as pd
from unittest.mock import patch, MagicMock

from processor import DataProcessor


class TestDataProcessor(unittest.TestCase):
    def setUp(self):
        self.sample_data = pd.DataFrame({
            'A': [1, 2, None, 2],
            'B': [4, 5, 6, 7]
        })

    def test_init(self):
        processor = DataProcessor(self.sample_data)
        self.assertEqual(processor.data, self.sample_data)

    def test_clean(self):
        processor = DataProcessor(self.sample_data)
        cleaned = processor.clean().data
        self.assertEqual(len(cleaned), 2)
        self.assertTrue(cleaned['A'].notna().all())
        self.assertFalse(cleaned.duplicated().any())

    def test_clean_empty(self):
        empty_data = pd.DataFrame()
        processor = DataProcessor(empty_data)
        cleaned = processor.clean().data
        self.assertEqual(len(cleaned), 0)

    def test_clean_all_nan(self):
        nan_data = pd.DataFrame({'A': [None, None]})
        processor = DataProcessor(nan_data)
        cleaned = processor.clean().data
        self.assertEqual(len(cleaned), 0)

    def test_summarize(self):
        processor = DataProcessor(self.sample_data)
        summary = processor.summarize()
        self.assertIn('rows', summary)
        self.assertEqual(summary['rows'], 2)
        self.assertIn('columns', summary)
        self.assertIn('numeric_summary', summary)

    def test_summarize_empty(self):
        empty_data = pd.DataFrame()
        processor = DataProcessor(empty_data)
        summary = processor.summarize()
        self.assertEqual(summary['rows'], 0)
        self.assertEqual(summary['columns'], [])
        self.assertIn('numeric_summary', summary)

    @patch('processor.DataAnalyzer')
    def test_detect_anomalies(self, mock_analyzer):
        mock_instance = MagicMock()
        mock_analyzer.return_value = mock_instance
        mock_instance.detect_outliers.return_value = {'outliers': []}

        processor = DataProcessor(self.sample_data)
        result = processor.detect_anomalies(z_threshold=3)

        mock_analyzer.assert_called_once_with(self.sample_data)
        mock_instance.detect_outliers.assert_called_once_with(3)
        self.assertEqual(result, {'outliers': []})

    @patch('processor.DataAnalyzer')
    def test_detect_anomalies_empty(self, mock_analyzer):
        mock_instance = MagicMock()
        mock_analyzer.return_value = mock_instance
        mock_instance.detect_outliers.return_value = {'outliers': []}

        empty_data = pd.DataFrame()
        processor = DataProcessor(empty_data)
        result = processor.detect_anomalies()

        mock_analyzer.assert_called_once_with(empty_data)
        mock_instance.detect_outliers.assert_called_once_with(3)
        self.assertEqual(result, {'outliers': []})

    @patch('pandas.DataFrame.to_csv')
    def test_export_cleaned(self, mock_to_csv):
        processor = DataProcessor(self.sample_data)
        path = processor.export_cleaned("test_output.csv")
        self.assertEqual(path, "test_output.csv")
        mock_to_csv.assert_called_once_with("test_output.csv", index=False)

    @patch('pandas.DataFrame.to_csv')
    def test_export_cleaned_default_path(self, mock_to_csv):
        processor = DataProcessor(self.sample_data)
        path = processor.export_cleaned()
        self.assertEqual(path, "output/cleaned.csv")
        mock_to_csv.assert_called_once_with("output/cleaned.csv", index=False)

    @patch('pandas.DataFrame.to_csv')
    def test_export_cleaned_empty(self, mock_to_csv):
        empty_data = pd.DataFrame()
        processor = DataProcessor(empty_data)
        path = processor.export_cleaned("test_empty.csv")
        self.assertEqual(path, "test_empty.csv")
        mock_to_csv.assert_called_once_with("test_empty.csv", index=False)


if __name__ == '__main__':
    unittest.main()