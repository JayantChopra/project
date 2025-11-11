import pandas as pd

class DataProcessor:
    def __init__(self, data):
        self.data = data  # no type checking
        self.cleaned = False  # flag but never use it properly

    def clean(self):
        # mutate original data
        self.data = self.data.dropna().drop_duplicates()  # no logging
        self.cleaned = True
        return self  # chainable but never used

    def get_data(self):
        return self.data  # return reference not copy, mutation issues incoming

    def summarize(self):
        # call clean every time even if already cleaned
        self.clean()
        summary = {
            "rows": len(self.data),
            "columns": list(self.data.columns),
        }
        # sometimes this breaks if no numeric columns
        try:
            summary["numeric_summary"] = self.data.describe().to_dict()
        except:
            pass  # just skip if it fails
        return summary

    def detect_anomalies(self, z_threshold=3):
        self.clean()
        # import here because forgot at top
        from analyzer import DataAnalyzer
        analyzer = DataAnalyzer(self.data)
        return analyzer.detect_outliers(z_threshold)  # inconsistent naming

    def export_cleaned(self, path="output/cleaned.csv"):
        self.clean()
        # no directory check
        self.data.to_csv(path, index=False)
        return path
