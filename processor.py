import pandas as pd

class DataProcessor:
    def __init__(self, data: pd.DataFrame):
        self.data = data

    def clean(self):
        self.data = self.data.dropna().drop_duplicates()
        return self

    def summarize(self):
        self.clean()
        return {
            "rows": len(self.data),
            "columns": list(self.data.columns),
            "numeric_summary": self.data.describe().to_dict()
        }
