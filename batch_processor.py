"""Batch processing utilities for handling multiple files."""
import pandas as pd
import os
from processor import DataProcessor
from utils import load_csv, save_json
from logger import get_logger

logger = get_logger("batch")

def process_multiple_files(file_paths, output_dir="output/batch"):
    """Process multiple CSV files and generate combined reports."""
    results = []
    for file_path in file_paths:
        try:
            df = load_csv(file_path)
            processor = DataProcessor(df)
            summary = processor.summarize()
            results.append({
                "file": file_path,
                "summary": summary,
                "status": "success"
            })
        except Exception as e:
            results.append({
                "file": file_path,
                "status": "error",
                "error": str(e)
            })
    
    output_path = os.path.join(output_dir, "batch_results.json")
    save_json(results, output_path)
    return results

def merge_datasets(file_paths, output_path="output/merged.csv"):
    """Merge multiple CSV files into one."""
    dataframes = []
    for file_path in file_paths:
        df = load_csv(file_path)
        dataframes.append(df)
    
    merged = pd.concat(dataframes, ignore_index=True)
    merged.to_csv(output_path, index=False)
    logger.info(f"Merged {len(dataframes)} files into {output_path}")
    return output_path

def compare_datasets(file1_path, file2_path, output_path="output/comparison.json"):
    """Compare two datasets and return differences."""
    df1 = load_csv(file1_path)
    df2 = load_csv(file2_path)
    
    comparison = {
        "file1_rows": len(df1),
        "file2_rows": len(df2),
        "file1_cols": list(df1.columns),
        "file2_cols": list(df2.columns),
        "common_cols": list(set(df1.columns) & set(df2.columns)),
        "unique_to_file1": list(set(df1.columns) - set(df2.columns)),
        "unique_to_file2": list(set(df2.columns) - set(df1.columns)),
    }
    
    save_json(comparison, output_path)
    return comparison

