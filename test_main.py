import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from main import main, summarize_data, detect_anomalies, correlation_analysis, export_cleaned_data
from config import Config

class TestMain(unittest.TestCase):

    @patch('main.load_csv')
    @patch('main.os.path.exists')
    def test_main_file_not_found(self, mock_exists, mock_load_csv):
        mock_exists.return_value = False
        with patch.object(sys, 'argv', ['script.py', 'summarize', '--path', 'nonexistent.csv']):
            main()
            mock_load_csv.assert_not_called()

    @patch('main.load_csv')
    @patch('main.os.path.exists')
    @patch('main.DataProcessor')
    def test_main_summarize(self, mock_processor, mock_exists, mock_load_csv):
        mock_exists.return_value = True
        mock_data = MagicMock()
        mock_load_csv.return_value = mock_data
        mock_proc_instance = MagicMock()
        mock_processor.return_value = mock_proc_instance
        mock_proc_instance.summarize.return_value = {'summary': 'data'}
        with patch.object(sys, 'argv', ['script.py', 'summarize', '--path', 'test.csv']):
            main()
            mock_proc_instance.summarize.assert_called_once()
            # Note: Would need to mock save_json etc., but for basic coverage

    @patch('main.load_csv')
    @patch('main.os.path.exists')
    @patch('main.DataProcessor')
    def test_main_analyze(self, mock_processor, mock_exists, mock_load_csv):
        mock_exists.return_value = True
        mock_data = MagicMock()
        mock_load_csv.return_value = mock_data
        mock_proc_instance = MagicMock()
        mock_processor.return_value = mock_proc_instance
        mock_proc_instance.detect_anomalies.return_value = []
        with patch.object(sys, 'argv', ['script.py', 'analyze', '--path', 'test.csv', '--threshold', '2.0']):
            main()
            mock_proc_instance.detect_anomalies.assert_called_once_with(z_threshold=2.0)

    @patch('main.load_csv')
    @patch('main.os.path.exists')
    @patch('main.DataProcessor')
    def test_main_correlate(self, mock_processor, mock_exists, mock_load_csv):
        mock_exists.return_value = True
        mock_data = MagicMock()
        mock_load_csv.return_value = mock_data
        mock_proc_instance = MagicMock()
        mock_processor.return_value = mock_proc_instance
        mock_data.corr.return_value = MagicMock(to_dict=lambda: {'corr': 'data'})
        with patch.object(sys, 'argv', ['script.py', 'correlate', '--path', 'test.csv']):
            main()
            mock_data.corr.assert_called_once()

    @patch('main.load_csv')
    @patch('main.os.path.exists')
    @patch('main.DataProcessor')
    def test_main_export(self, mock_processor, mock_exists, mock_load_csv):
        mock_exists.return_value = True
        mock_data = MagicMock()
        mock_load_csv.return_value = mock_data
        mock_proc_instance = MagicMock()
        mock_processor.return_value = mock_proc_instance
        mock_proc_instance.export_cleaned.return_value = 'output/cleaned.csv'
        with patch.object(sys, 'argv', ['script.py', 'export', '--path', 'test.csv']):
            main()
            mock_proc_instance.export_cleaned.assert_called_once_with('output/cleaned.csv')

    def test_summarize_data(self):
        mock_processor = MagicMock()
        mock_processor.summarize.return_value = {'test': 'summary'}
        with patch('main.save_json'), patch('main.file_hash'), patch('main.logger'):
            summarize_data(mock_processor, 'test_output.json')
            mock_processor.summarize.assert_called_once()

    def test_detect_anomalies(self):
        mock_processor = MagicMock()
        mock_processor.detect_anomalies.return_value = [{'row': 1}]
        with patch('main.logger'):
            result = detect_anomalies(mock_processor, 3.0)
            self.assertEqual(result, [{'row': 1}])
            mock_processor.detect_anomalies.assert_called_once_with(z_threshold=3.0)

    def test_detect_anomalies_none(self):
        mock_processor = MagicMock()
        mock_processor.detect_anomalies.return_value = []
        with patch('main.logger'):
            result = detect_anomalies(mock_processor, 3.0)
            self.assertEqual(result, [])
            mock_processor.detect_anomalies.assert_called_once_with(z_threshold=3.0)

    def test_correlation_analysis(self):
        mock_processor = MagicMock()
        mock_data = MagicMock()
        mock_processor.data = mock_data
        mock_corr = MagicMock()
        mock_corr.to_dict.return_value = {'a': {'b': 1.0}}
        mock_data.corr.return_value = mock_corr
        with patch('main.save_json'), patch('main.file_hash'), patch('main.logger'):
            correlation_analysis(mock_processor)
            mock_data.corr.assert_called_once()

    def test_correlation_analysis_no_numeric(self):
        mock_processor = MagicMock()
        mock_data = MagicMock()
        mock_processor.data = mock_data
        mock_data.corr.return_value = MagicMock(to_dict=lambda: None)
        with patch('main.logger'):
            correlation_analysis(mock_processor)
            mock_data.corr.assert_called_once()

    def test_export_cleaned_data(self):
        mock_processor = MagicMock()
        mock_processor.export_cleaned.return_value = 'path.csv'
        with patch('main.file_hash'), patch('main.logger'):
            export_cleaned_data(mock_processor)
            mock_processor.export_cleaned.assert_called_once_with('output/cleaned.csv')

if __name__ == '__main__':
    unittest.main()
