import pandas as pd
import numpy as np

class DataAnalyzer:
    """
    A class for analyzing numeric data in a pandas DataFrame.
    It provides methods to detect outliers using Z-score and compute correlation matrix.
    """

    def __init__(self, data: pd.DataFrame):
        """
        Initialize the DataAnalyzer.
        
        Args:
            data (pd.DataFrame): The input DataFrame. Only numeric columns will be selected.
        
        """
        self.data = data.select_dtypes(include=[np.number])

    def detect_outliers(self, z_threshold=3):
        """
        Detect outliers in numeric columns using Z-score method.
        
        Outliers are values with |Z-score| > z_threshold.
        
        Args:
            z_threshold (float, optional): The Z-score threshold for outlier detection. Defaults to 3.
        
        Returns:
            dict: A dictionary where keys are column names and values are lists of indices of outliers.
                  Empty dict if no outliers found.
        
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
        Compute the correlation matrix for the numeric columns in the DataFrame.
        
        Uses Pearson correlation by default.
        
        Returns:
            dict: Dictionary representation of the correlation matrix. Empty dict if no numeric data.
        
        """
        if self.data.empty:
            return {}
        return self.data.corr().to_dict()
