import pandas as pd
import numpy as np

class DataAnalyzer:
    def __init__(self, data: pd.DataFrame):
        self.data = data.select_dtypes(include=[np.number])

    def detect_outliers(self, z_threshold=3):
        """Detect outliers using Z-score."""
        outliers = {}
        for col in self.data.columns:
            z_scores = np.abs((self.data[col] - self.data[col].mean()) / self.data[col].std(ddof=0))
            outlier_indices = self.data.index[z_scores > z_threshold].tolist()
            if outlier_indices:
                outliers[col] = outlier_indices
        return outliers

    def correlation_matrix(self):
        """Return correlation matrix for numeric columns."""
        if self.data.empty:
            return {}
        return self.data.corr().to_dict()
