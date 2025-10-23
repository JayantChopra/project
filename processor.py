from analyzer import DataAnalyzer
from utils import timeit
import pandas as pd  # Assuming pandas is used, add if not imported

class DataProcessor:
    """
    A class to process and analyze pandas DataFrames.
    
    Provides methods for cleaning data, generating summaries, detecting anomalies,
    and exporting cleaned data to CSV.
    """
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize the DataProcessor with a pandas DataFrame.
        
        Args:
            data (pd.DataFrame): The input data to process.
        """
        self.data = data

    def clean(self):
        """
        Clean the data by removing rows with NaN values and duplicate rows.
        
        Modifies the internal data in place and returns the instance for method chaining.
        
        Returns:
            DataProcessor: The instance itself (self).
        """
        self.data = self.data.dropna().drop_duplicates()
        return self

    @timeit
    def summarize(self):
        """
        Clean the data and generate a summary of its structure and statistics.
        
        This method first cleans the data, then returns a dictionary containing:
        - Number of rows
        - List of column names
        - Statistical summary for numeric columns
        
        Returns:
            dict: Summary information.
                - 'rows': int
                - 'columns': list of str
                - 'numeric_summary': dict of statistical descriptions
        """
        self.clean()
        return {
            "rows": len(self.data),
            "columns": list(self.data.columns),
            "numeric_summary": self.data.describe().to_dict()
        }

    def detect_anomalies(self, z_threshold: float = 3):
        """
        Detect outliers in numeric columns using the Z-score method.
        
        Creates an instance of DataAnalyzer and calls its detect_outliers method.
        
        Args:
            z_threshold (float): The Z-score threshold for identifying outliers. Default is 3.
        
        Returns:
            dict: A dictionary where keys are column names and values are lists of row indices
                  containing outliers for that column.
        """
        analyzer = DataAnalyzer(self.data)
        return analyzer.detect_outliers(z_threshold)

    def export_cleaned(self, path: str = "output/cleaned.csv"):
        """
        Clean the data and export it to a CSV file.
        
        First cleans the data, then saves it to the specified path without the index.
        
        Args:
            path (str): The file path to save the CSV. Defaults to 'output/cleaned.csv'.
        
        Returns:
            str: The path where the file was saved.
        
        Note:
            Ensure the directory exists or handle potential FileNotFoundError.
        """
        self.clean()
        self.data.to_csv(path, index=False)
        return path
