import os
import pandas as pd
from analyzer import DataAnalyzer
from utils import timeit

class DataProcessor:
    """
    DataProcessor class for cleaning, summarizing, and analyzing data.
    
    This class provides methods to clean data, generate summaries, detect anomalies,
    and export cleaned data.
    
    Attributes:
        data (pd.DataFrame): The processed data.
    """
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize the DataProcessor with input data.
        
        Args:
            data (pd.DataFrame): The input dataset to process.
        
        """
        self.data = data
    
    def clean(self):
        """
        Clean the data by removing rows with missing values and duplicates.
        
        This method modifies the internal data attribute and returns self for method chaining.
        
        Returns:
            DataProcessor: The instance itself for chaining.
        
        """
        self.data = self.data.dropna().drop_duplicates()
        return self
    
    @timeit
    def summarize(self):
        """
        Generate a summary of the data after cleaning it.
        
        This method first cleans the data if not already done, then computes basic statistics.
        
        Returns:
            dict: A dictionary containing row count, column names, and numeric summary.
        
        """
        self.clean()
        return {
            "rows": len(self.data),
            "columns": list(self.data.columns),
            "numeric_summary": self.data.describe().to_dict()
        }
    
    def detect_anomalies(self, z_threshold: float = 3.0) -> dict:
        """
        Detect outliers in numeric columns using Z-score method.
        
        Args:
            z_threshold (float): The Z-score threshold for identifying outliers. Default is 3.0.
        
        Returns:
            dict: A dictionary mapping column names to lists of outlier indices.
        
        """
        analyzer = DataAnalyzer(self.data)
        return analyzer.detect_outliers(z_threshold)
    
    def export_cleaned(self, path: str = "output/cleaned.csv") -> str:
        """
        Export the cleaned data to a CSV file.
        
        This method cleans the data if not already done and saves it to the specified path.
        Ensures the output directory exists.
        
        Args:
            path (str): The file path to save the cleaned data. Default is 'output/cleaned.csv'.
        
        Returns:
            str: The path where the file was saved.
        
        """
        self.clean()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.data.to_csv(path, index=False)
        return path
