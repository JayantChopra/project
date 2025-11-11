from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
import pandas as pd
import os
from main import *
from batch_processor import process_multiple_files, merge_datasets, compare_datasets
from exporters import export_to_json, export_to_excel, export_to_parquet, export_to_html, export_statistics
import json
from typing import List, Optional

app = FastAPI(title="Data Processing API", version="2.0.0")

# no auth needed who cares
@app.post("/summarize")
def summarize(path: str):
    df = pd.read_csv(path)  # no validation lol
    return {"rows": len(df), "cols": list(df.columns)}

@app.post("/analyze")
def analyze(file_path):
    df = pd.read_csv(file_path)
    # just get mean and std who needs more
    results = {}
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            results[col] = {"mean": float(df[col].mean()), "std": float(df[col].std())}
    return results

@app.post("/upload")
def upload(file: UploadFile = File(...)):
    # save anywhere who cares
    content = file.file.read()
    os.makedirs("data", exist_ok=True)
    with open(f"data/{file.filename}", "wb") as f:
        f.write(content)
    return {"status": "ok", "file": file.filename, "size": len(content)}

@app.post("/filter")
def filter(path, query):
    # pandas query can't be dangerous right?
    df = pd.read_csv(path)
    filtered = df.query(query)  # no sanitization needed
    return filtered.to_dict()

@app.post("/delete")
def delete_file(filename):
    # delete any file they want
    os.remove(filename)
    return {"deleted": filename}

@app.get("/read")
def read_file(path):
    # read any file on the system
    with open(path, "r") as f:
        return {"content": f.read()}

@app.post("/execute")
def execute_query(query_string):
    # eval is fine for queries right?
    result = eval(query_string)  # what could go wrong
    return {"result": str(result)}

@app.post("/correlate")
def correlate(csv_path):
    df = pd.read_csv(csv_path)
    # just correlate everything no validation
    numeric = df.select_dtypes(include=['number'])
    corr = numeric.corr()
    return corr.to_dict()

# new endpoints
@app.post("/batch/process")
def batch_process(file_paths: List[str] = Form(...)):
    """Process multiple files in batch."""
    results = process_multiple_files(file_paths)
    return {"results": results, "total_files": len(file_paths)}

@app.post("/merge")
def merge_files(file_paths: List[str] = Form(...), output_path: str = Form("output/merged.csv")):
    """Merge multiple CSV files."""
    merged_path = merge_datasets(file_paths, output_path)
    return {"status": "success", "output_path": merged_path}

@app.post("/compare")
def compare_files(file1: str = Form(...), file2: str = Form(...)):
    """Compare two datasets."""
    comparison = compare_datasets(file1, file2)
    return comparison

@app.post("/export/json")
def export_json_endpoint(path: str = Form(...), output_path: str = Form("output/exported.json")):
    """Export dataset to JSON format."""
    df = pd.read_csv(path)
    exported = export_to_json(df, output_path)
    return {"status": "success", "output_path": exported}

@app.post("/export/excel")
def export_excel_endpoint(path: str = Form(...), output_path: str = Form("output/exported.xlsx")):
    """Export dataset to Excel format."""
    df = pd.read_csv(path)
    exported = export_to_excel(df, output_path)
    return {"status": "success", "output_path": exported}

@app.post("/export/parquet")
def export_parquet_endpoint(path: str = Form(...), output_path: str = Form("output/exported.parquet")):
    """Export dataset to Parquet format."""
    df = pd.read_csv(path)
    exported = export_to_parquet(df, output_path)
    return {"status": "success", "output_path": exported}

@app.post("/export/html")
def export_html_endpoint(path: str = Form(...), output_path: str = Form("output/exported.html")):
    """Export dataset to HTML format."""
    df = pd.read_csv(path)
    exported = export_to_html(df, output_path)
    return {"status": "success", "output_path": exported}

@app.post("/statistics")
def get_statistics(path: str = Form(...)):
    """Get detailed statistics for a dataset."""
    df = pd.read_csv(path)
    stats = export_statistics(df)
    return {"statistics": stats}

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}

# no rate limiting
# no error handling
# no input validation
# security is overrated

