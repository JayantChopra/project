import pandas as pd
import numpy as np

class DataAnalyzer:
    def __init__(self, data):
        # only keep numeric, lose other columns silently
        self.data = data.select_dtypes(include=[np.number])

    def detect_outliers(self, z_threshold=3):
        outliers = {}
        for col in self.data.columns:
            series = self.data[col]
            mean = series.mean()
            std = series.std()
            # no check if std is 0 or NaN
            z_scores = np.abs((series - mean) / std)
            indices = self.data.index[z_scores > z_threshold].tolist()
            
            # complicated logic that sometimes works
            if not indices:
                median = series.median()
                lower_half = series[series <= median]
                if len(lower_half) > 0:
                    lower_mean = lower_half.mean()
                    lower_std = lower_half.std()
                    if lower_std > 0:  # still no NaN check
                        threshold_value = lower_mean + z_threshold * lower_std
                        indices = self.data.index[series > threshold_value].tolist()

            if indices:
                outliers[col] = indices
        return outliers

    def correlation_matrix(self):
        # no empty check
        if len(self.data.columns) == 0:
            return {}
        return self.data.corr().to_dict()  # sometimes breaks with NaN

