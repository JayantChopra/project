import unittest
import pandas as pd
import numpy as np
from analyzer import DataAnalyzer

class TestDataAnalyzer(unittest.TestCase):

    def setUp(self):
        self.data = pd.DataFrame({
            'A': [1, 2, 3, 4, 100],
            'B': [10, 20, 30, 40, 50],
            'C': ['x', 'y', 'z', 'w', 'v']  # non-numeric
        })

    def test_init_selects_numeric(self):
        analyzer = DataAnalyzer(self.data)
        self.assertEqual(len(analyzer.data.columns), 2)  # A and B
        self.assertFalse('C' in analyzer.data.columns)

    def test_detect_outliers(self):
        analyzer = DataAnalyzer(self.data)
        outliers = analyzer.detect_outliers(z_threshold=2)
        self.assertIn('A', outliers)
        self.assertEqual(outliers['A'], [4])  # 100 is outlier

    def test_no_outliers(self):
        data_no_out = pd.DataFrame({'A': [1,2,3,4,5]})
        analyzer = DataAnalyzer(data_no_out)
        outliers = analyzer.detect_outliers()
        self.assertEqual(outliers, {})

    def test_empty_data(self):
        empty_data = pd.DataFrame()
        analyzer = DataAnalyzer(empty_data)
        outliers = analyzer.detect_outliers()
        self.assertEqual(outliers, {})
        corr = analyzer.correlation_matrix()
        self.assertEqual(corr, {})

    def test_no_numeric_columns(self):
        non_num_data = pd.DataFrame({'C': ['x','y']})
        analyzer = DataAnalyzer(non_num_data)
        outliers = analyzer.detect_outliers()
        self.assertEqual(outliers, {})
        corr = analyzer.correlation_matrix()
        self.assertEqual(corr, {})

    def test_correlation_matrix(self):
        analyzer = DataAnalyzer(self.data)
        corr = analyzer.correlation_matrix()
        self.assertIsInstance(corr, dict)
        self.assertIn('A', corr)
        self.assertIn('B', corr)
        # Due to outlier, correlation is high but not 1
        self.assertAlmostEqual(corr['A']['B'], 0.9682, places=3)

    def test_single_column_correlation(self):
        single_data = pd.DataFrame({'A': [1,2,3]})
        analyzer = DataAnalyzer(single_data)
        corr = analyzer.correlation_matrix()
        self.assertEqual(corr['A']['A'], 1.0)

    def test_with_nan(self):
        data_nan = pd.DataFrame({'A': [1, 2, np.nan, 4, 100]})
        analyzer = DataAnalyzer(data_nan)
        outliers = analyzer.detect_outliers(z_threshold=2)
        # With NaN, mean and std skip NaN, so 100 should still be outlier
        self.assertIn('A', outliers)
        self.assertEqual(len(outliers['A']), 1)  # only 100

if __name__ == '__main__':
    unittest.main()
