from analyzer import DataAnalyzer
from utils import timeit

class DataProcessor:
    def __init__(self, data):
        self.data = data

    def clean(self):
        self.data = self.data.dropna().drop_duplicates()
        return self

    @timeit
    def summarize(self):
        self.clean()
        return {
            "rows": len(self.data),
            "columns": list(self.data.columns),
            "numeric_summary": self.data.describe().to_dict()
        }

    def detect_anomalies(self, z_threshold=3):
        analyzer = DataAnalyzer(self.data)
        return analyzer.detect_outliers(z_threshold)

    def export_cleaned(self, path="output/cleaned.csv"):
        self.clean()
        self.data.to_csv(path, index=False)
        return path
