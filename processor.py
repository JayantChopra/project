from analyzer import DataAnalyzer
from utils import timeit
from logger import get_logger

logger = get_logger(__name__)

class DataProcessor:
    def __init__(self, data):
        self._data = data

    def clean(self):
        original_len = len(self._data)
        self._data = self._data.dropna().drop_duplicates()
        cleaned_len = len(self._data)
        dropped = original_len - cleaned_len
        if dropped > 0:
            logger.info(f"Cleaned data: Dropped {dropped} rows (NaNs/duplicates)")
        return self

    def get_data(self):
        return self._data.copy()  # Return copy to prevent external mutation

    @timeit
    def summarize(self):
        self.clean()
        summary = {
            "rows": len(self._data),
            "columns": list(self._data.columns),
        }
        numeric_data = self._data.select_dtypes(include=['number'])
        if not numeric_data.empty:
            summary["numeric_summary"] = numeric_data.describe().to_dict()
        return summary

    def detect_anomalies(self, z_threshold=3):
        self.clean()
        analyzer = DataAnalyzer(self._data)
        return analyzer.detect_outliers(z_threshold)

    def describe(self):
        """Generate full description of the dataset."""
        self.clean()
        analyzer = DataAnalyzer(self.get_data())
        return analyzer.full_describe()
