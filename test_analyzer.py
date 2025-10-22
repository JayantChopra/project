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

    def test_init_selects_numeric_columns(self):
        analyzer = DataAnalyzer(self.data)
        expected_data = pd.DataFrame({
            'A': [1, 2, 3, 4, 100],
            'B': [10, 20, 30, 40, 50]
        })
        pd.testing.assert_frame_equal(analyzer.data.reset_index(drop=True), expected_data.reset_index(drop=True))

    def test_detect_outliers_normal_case(self):
        analyzer = DataAnalyzer(self.data)
        outliers = analyzer.detect_outliers(z_threshold=3)
        self.assertIn('A', outliers)
        self.assertEqual(outliers['A'], [4])  # 100 is outlier
        self.assertNotIn('B', outliers)

    def test_detect_outliers_no_outliers(self):
        normal_data = pd.DataFrame({
            'A': [1, 2, 3, 4, 5],
            'B': [10, 20, 30, 40, 50]
        })
        analyzer = DataAnalyzer(normal_data)
        outliers = analyzer.detect_outliers(z_threshold=3)
        self.assertEqual(outliers, {})

    def test_detect_outliers_all_outliers(self):
        outlier_data = pd.DataFrame({'A': [100, 200, 300]})
        analyzer = DataAnalyzer(outlier_data)
        outliers = analyzer.detect_outliers(z_threshold=3)
        self.assertIn('A', outliers)
        self.assertEqual(outliers['A'], [0, 1, 2])

    def test_detect_outliers_with_nan(self):
        data_with_nan = pd.DataFrame({'A': [1, 2, np.nan, 100]})
        analyzer = DataAnalyzer(data_with_nan)
        outliers = analyzer.detect_outliers(z_threshold=3)
        # NaN is ignored in mean/std
        self.assertIn('A', outliers)
        self.assertEqual(outliers['A'], [3])  # index 3 is 100

    def test_detect_outliers_empty_dataframe(self):
        empty_data = pd.DataFrame()
        analyzer = DataAnalyzer(empty_data)
        outliers = analyzer.detect_outliers()
        self.assertEqual(outliers, {})

    def test_detect_outliers_single_column(self):
        single_col = pd.DataFrame({'A': [1, 100]})
        analyzer = DataAnalyzer(single_col)
        outliers = analyzer.detect_outliers(z_threshold=3)
        self.assertIn('A', outliers)
        self.assertEqual(outliers['A'], [1])

    def test_correlation_matrix_normal(self):
        analyzer = DataAnalyzer(self.data)
        corr = analyzer.correlation_matrix()
        self.assertIn('A', corr)
        self.assertIn('B', corr['A'])
        # Check it's a dict of dicts
        self.assertIsInstance(corr, dict)

    def test_correlation_matrix_empty(self):
        empty_data = pd.DataFrame()
        analyzer = DataAnalyzer(empty_data)
        corr = analyzer.correlation_matrix()
        self.assertEqual(corr, {})

    def test_correlation_matrix_single_column(self):
        single_col = pd.DataFrame({'A': [1, 2, 3]})
        analyzer = DataAnalyzer(single_col)
        corr = analyzer.correlation_matrix()
        self.assertEqual(corr, {'A': {'A': 1.0}})

    def test_init_with_only_non_numeric(self):
        non_numeric = pd.DataFrame({'C': ['a', 'b', 'c']})
        analyzer = DataAnalyzer(non_numeric)
        self.assertTrue(analyzer.data.empty)

    def test_detect_outliers_custom_threshold(self):
        analyzer = DataAnalyzer(self.data)
        outliers = analyzer.detect_outliers(z_threshold=1)
        self.assertIn('A', outliers)
        # More outliers with lower threshold
        self.assertGreater(len(outliers['A']), 1)


if __name__ == '__main__':
    unittest.main()
