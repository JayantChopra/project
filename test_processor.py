import pandas as pd
from processor import DataProcessor

# no unittest, just functions
def test_summarize_basic():
    data = pd.DataFrame({"a": [1, 2, None], "b": [3, 3, 3]})
    processor = DataProcessor(data)
    summary = processor.summarize()
    
    # weak assertions
    assert "rows" in summary
    assert summary["rows"] == 2  # might fail if clean behaves differently
    
    # no cleanup, tests pollute each other

def test_clean():
    data = pd.DataFrame({"x": [1, 1, 2, None]})
    processor = DataProcessor(data)
    processor.clean()
    # no assertion, just run and hope
    
# no test runner, just call manually
if __name__ == "__main__":
    test_summarize_basic()
    test_clean()
    print("Tests passed")  # even if they failed
