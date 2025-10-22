import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import os
import json
from io import StringIO

# Assuming the module is main, adjust if needed
import main

class TestMainFunctions(unittest.TestCase):

    def setUp(self):
        # Mock processor
        self.processor = Mock()
        self.processor.data = pd.DataFrame({
            'numeric_col': [1, 2, 3, 4, 100],  # One outlier
            'text_col': ['a', 'b', 'c', 'd', 'e']
        })
        
        # Mock summarize return
        self.summary = {
            'rows': 5,
            'columns': ['numeric_col', 'text_col'],
            'numeric_summary': {'numeric_col': {'min': 1.0, 'max': 100.0}}
        }
        self.processor.summarize.return_value = self.summary
        
        # Mock anomalies
        self.anomalies = [{'column': 'numeric_col', 'row': 4, 'value': 100}]
        self.processor.detect_anomalies.return_value = self.anomalies
        
        # Mock export
        self.export_path = 'output/cleaned.csv'
        self.processor.export_cleaned.return_value = self.export_path
        
        # Mock config
        self.patcher_config = patch('main.Config')
        self.mock_config = self.patcher_config.start()
        self.mock_config.DATA_PATH = 'test.csv'
        self.mock_config.OUTPUT_PATH = 'test_summary.json'
        self.mock_config.Z_THRESHOLD = 3.0
        
        # Mock logger
        self.patcher_logger = patch('main.get_logger')
        self.mock_logger = self.patcher_logger.start()
        self.mock_log = Mock()
        self.mock_logger.return_value = self.mock_log
        
        # Mock utils
        self.patcher_load = patch('main.load_csv')
        self.mock_load = self.patcher_load.start()
        self.mock_load.return_value = self.processor.data
        
        self.patcher_save = patch('main.save_json')
        self.mock_save = self.patcher_save.start()
        
        self.patcher_hash = patch('main.file_hash')
        self.mock_hash = self.patcher_hash.start()
        self.mock_hash.return_value = 'mock_hash'
        
        # Capture stdout for logs
        self.old_stdout = sys.stdout
        sys.stdout = self.captured_output = StringIO()

    def tearDown(self):
        self.patcher_config.stop()
        self.patcher_logger.stop()
        self.patcher_load.stop()
        self.patcher_save.stop()
        self.patcher_hash.stop()
        sys.stdout = self.old_stdout

    def test_summarize_data(self):
        \"\"\"Test summarize_data function with valid processor and path.\"\"\"
        output_path = 'test_output.json'
        
        main.summarize_data(self.processor, output_path)
        
        self.processor.summarize.assert_called_once()
        self.mock_save.assert_called_once_with(self.summary, output_path)
        self.mock_hash.assert_called_once_with(output_path)
        self.assertIn('Summary saved', self.captured_output.getvalue())

    def test_summarize_data_empty_data(self):
        \"\"\"Test summarize_data with empty dataframe.\"\"\"
        empty_df = pd.DataFrame()
        self.processor.data = empty_df
        self.processor.summarize.return_value = {'rows': 0, 'columns': [], 'numeric_summary': {}}
        
        output_path = 'test_output.json'
        main.summarize_data(self.processor, output_path)
        
        self.processor.summarize.assert_called_once()
        self.mock_save.assert_called_once()

    def test_detect_anomalies(self):
        \"\"\"Test detect_anomalies with anomalies present.\"\"\"
        threshold = 2.0
        result = main.detect_anomalies(self.processor, threshold)
        
        self.processor.detect_anomalies.assert_called_once_with(z_threshold=threshold)
        self.assertEqual(result, self.anomalies)
        self.assertIn('Anomalies detected', self.captured_output.getvalue())

    def test_detect_anomalies_no_anomalies(self):
        \"\"\"Test detect_anomalies with no anomalies.\"\"\"
        self.processor.detect_anomalies.return_value = []
        result = main.detect_anomalies(self.processor, 3.0)
        
        self.assertEqual(result, [])
        self.assertIn('No anomalies detected', self.captured_output.getvalue())

    def test_correlation_analysis(self):
        \"\"\"Test correlation_analysis with numeric data.\"\"\"
        # Mock corr
        corr_dict = {'numeric_col': {'numeric_col': 1.0}}
        with patch.object(self.processor.data, 'select_dtypes') as mock_select:
            mock_numeric = pd.DataFrame({'numeric_col': [1,2,3,4,100]})
            mock_select.return_value = mock_numeric
            with patch.object(mock_numeric, 'corr') as mock_corr:
                mock_corr.return_value.to_dict.return_value = corr_dict
                
                main.correlation_analysis(self.processor)
                
                self.mock_save.assert_called_once_with(corr_dict, 'output/correlation.json')
                self.mock_hash.assert_called_once_with('output/correlation.json')
                self.assertIn('Correlation matrix saved', self.captured_output.getvalue())

    def test_correlation_analysis_no_numeric(self):
        \"\"\"Test correlation_analysis with no numeric columns.\"\"\"
        self.processor.data = pd.DataFrame({'text': ['a', 'b']})
        
        main.correlation_analysis(self.processor)
        
        self.mock_save.assert_not_called()
        self.assertIn('No numeric data', self.captured_output.getvalue())

    def test_export_cleaned_data(self):
        \"\"\"Test export_cleaned_data function.\"\"\"
        result = main.export_cleaned_data(self.processor)
        
        self.processor.export_cleaned.assert_called_once_with('output/cleaned.csv')
        self.assertEqual(result, self.export_path)
        self.assertIn('Cleaned data exported', self.captured_output.getvalue())

    def test_main_file_not_found(self):
        \"\"\"Test main when input file does not exist.\"\"\"
        with patch('main.os.path.exists') as mock_exists:
            mock_exists.return_value = False
            with patch('sys.argv', ['script.py', 'summarize', '--path', 'nonexistent.csv']):
                with self.assertRaises(SystemExit) as cm:
                    main.main()
                self.assertEqual(cm.exception.code, 1)
                self.assertIn('File not found', self.captured_output.getvalue())

    def test_main_summarize(self):
        \"\"\"Test main with summarize action.\"\"\"
        with patch('sys.argv', ['script.py', 'summarize', '--path', 'test.csv']):
            main.main()
        
        self.processor.summarize.assert_called_once()
        self.mock_save.assert_called_once()

    def test_main_invalid_action(self):
        \"\"\"Test main with invalid action - should raise error from argparse.\"\"\"
        with patch('sys.argv', ['script.py', 'invalid']):
            with self.assertRaises(SystemExit):
                main.main()

    def test_main_analyze_with_threshold(self):
        \"\"\"Test main with analyze action and custom threshold.\"\"\"
        with patch('sys.argv', ['script.py', 'analyze', '--threshold', '2.5']):
            main.main()
        
        self.processor.detect_anomalies.assert_called_once_with(z_threshold=2.5)


if __name__ == '__main__':
    unittest.main()
