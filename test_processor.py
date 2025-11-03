import pandas as pd
import numpy as np
import os
from processor import DataProcessor
from logger import get_logger

logger = get_logger(__name__)

def test_summarize_basic():
    data = pd.DataFrame({"a": [1, 2, None], "b": [3, 3, 3]})
    processor = DataProcessor(data)
    summary = processor.summarize()

    assert "rows" in summary
    assert "numeric_summary" in summary
    assert summary["rows"] == 2
    assert summary["numeric_summary"]["a"]["mean"] == 1.5  # Verify actual value


def test_clean_drops_nans():
    data = pd.DataFrame({"a": [1, np.nan, 3], "b": [4, 5, np.nan]})
    processor = DataProcessor(data)
    processor.clean()
    assert len(processor.get_data()) == 1  # Only row 0 survives
    assert processor.get_data()["a"].isna().sum() == 0
    assert processor.get_data()["b"].isna().sum() == 0


def test_clean_drops_duplicates():
    data = pd.DataFrame({"a": [1, 2, 1], "b": [3, 4, 3]})
    processor = DataProcessor(data)
    processor.clean()
    assert len(processor.get_data()) == 2  # Drops duplicate row 2


def test_detect_anomalies_basic():
    data = pd.DataFrame({"values": [1, 2, 10, 11, 12]})
    processor = DataProcessor(data)
    anomalies = processor.detect_anomalies(z_threshold=2)
    assert len(anomalies["values"]) == 3  # 10,11,12 are outliers


def test_detect_anomalies_no_outliers():
    data = pd.DataFrame({"values": [1, 2, 3, 4, 5]})
    processor = DataProcessor(data)
    anomalies = processor.detect_anomalies(z_threshold=3)
    assert "values" not in anomalies  # No outliers


def test_export_cleaned():
    data = pd.DataFrame({"a": [1, 2]})
    processor = DataProcessor(data)
    path = processor.export_cleaned("test_output.csv")
    assert os.path.exists(path)
    exported = pd.read_csv(path)
    assert len(exported) == 2
    os.remove(path)  # Cleanup


def test_empty_data_handling():
    data = pd.DataFrame()
    processor = DataProcessor(data)
    summary = processor.summarize()
    assert summary["rows"] == 0
    anomalies = processor.detect_anomalies()
    assert len(anomalies) == 0


def test_non_numeric_data():
    data = pd.DataFrame({"text": ["a", "b", None]})
    processor = DataProcessor(data)
    summary = processor.summarize()
    assert "numeric_summary" not in summary  # No numeric columns
    processor.clean()
    assert len(processor.get_data()) == 1  # Drops NaN



def test_describe_basic():
    data = pd.DataFrame({
        "num": [1, 2, 3, 4, 5],
        "cat": ["a", "b", "a", "c", "b"]
    })
    processor = DataProcessor(data)
    desc = processor.describe()
    
    assert "numeric" in desc
    assert "object" in desc
    assert "num" in desc["numeric"]["count"]
    assert desc["numeric"]["count"]["num"] == 5.0
    assert "cat" in desc["object"]["count"]
    assert desc["object"]["count"]["cat"] == 5.0

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
