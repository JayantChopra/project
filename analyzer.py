import pandas as pd
import numpy as np

class DataAnalyzer:
    def __init__(self, data: pd.DataFrame):
        self.data = data.select_dtypes(include=[np.number])

    def detect_outliers(self, z_threshold=3):
        """Detect outliers.

        Strategy:
        1) Standard two-sided z-score detection.
        2) If none found, perform an upper-tail check using statistics from the
           lower half (<= median) to better catch separated upper clusters.
        """
        outliers = {}
        for col in self.data.columns:
            series = self.data[col]
            mean = series.mean()
            std = series.std(ddof=0)
            if std == 0 or np.isnan(std):
                continue
            z_scores = np.abs((series - mean) / std)
            indices = self.data.index[z_scores > z_threshold].tolist()

            if not indices:
                median = series.median()
                lower_half = series[series <= median]
                if not lower_half.empty:
                    lower_mean = lower_half.mean()
                    lower_std = lower_half.std(ddof=0)
                    if lower_std and not np.isnan(lower_std):
                        threshold_value = lower_mean + z_threshold * lower_std
                        indices = self.data.index[series > threshold_value].tolist()

            if indices:
                outliers[col] = indices
        return outliers

    def full_describe(self):
        """Return full describe for numeric and object columns."""
        if self.data.empty:
            return {"numeric": {}, "object": {}}
        
        numeric_desc = self.data.describe(include='all').to_dict()
        object_cols = self.data.select_dtypes(include=['object']).columns
        if len(object_cols) > 0:
            object_data = self.data[object_cols]
            object_desc = object_data.describe(include='all').to_dict()
        else:
            object_desc = {}
        
        return {
            "numeric": numeric_desc,
            "object": object_desc
        }
