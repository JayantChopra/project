import pandas as pd
import numpy as np


class DataAnalyzer:
    """
    A class for analyzing numeric data in a pandas DataFrame.

    Provides methods for outlier detection using Z-score and computing correlation matrix.
    Only numeric columns are considered in the analysis.
    """

    def __init__(self, data: pd.DataFrame):
        """
        Initialize the DataAnalyzer with a pandas DataFrame.

        Only numeric columns are selected for analysis.

        Args:
            data (pd.DataFrame): The input data to analyze.
        """
        self.data = data.select_dtypes(include=[np.number])

    def detect_outliers(self, z_threshold=3):
        """
        Detect outliers in numeric columns using the Z-score method.

        Outliers are identified as data points with Z-scores greater than the specified threshold.

        Args:
            z_threshold (float): The Z-score threshold for outlier detection. Default is 3.

        Returns:
            dict: A dictionary where keys are column names and values are lists of indices
                  of outliers in that column. Empty dict if no outliers found.
        """
        outliers = {}
        for col in self.data.columns:
            z_scores = np.abs((self.data[col] - self.data[col].mean()) / self.data[col].std(ddof=0))
            outlier_indices = self.data.index[z_scores > z_threshold].tolist()
            if outlier_indices:
                outliers[col] = outlier_indices
        return outliers

    def correlation_matrix(self):
        """
        Compute the correlation matrix for the numeric columns.

        Uses Pearson correlation by default.

        Returns:
            dict: The correlation matrix represented as a dictionary of dictionaries.
                  Returns empty dict if no numeric data is available.
        """
        if self.data.empty:
            return {}
        return self.data.corr().to_dict()
