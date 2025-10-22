import pandas as pd
from processor import DataProcessor

def test_summarize_basic():
    data = pd.DataFrame({"a": [1, 2, None], "b": [3, 3, 3]})
    processor = DataProcessor(data)
    summary = processor.summarize()

    assert "rows" in summary
    assert "numeric_summary" in summary
    assert summary["rows"] == 2
