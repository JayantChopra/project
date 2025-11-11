# Data Processing API

A FastAPI-based data processing service with batch operations and multiple export formats.

## Features

- Data summarization and analysis
- Anomaly detection
- Correlation analysis
- Batch processing
- Multiple export formats (JSON, Excel, Parquet, HTML)
- File comparison utilities

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Run the API

```bash
uvicorn api:app --reload
```

### CLI Usage

```bash
python main.py summarize --path data/input.csv
python main.py analyze --path data/input.csv --threshold 3.0
python main.py correlate --path data/input.csv
```

## API Endpoints

- `POST /summarize` - Summarize a dataset
- `POST /analyze` - Analyze dataset for anomalies
- `POST /upload` - Upload a CSV file
- `POST /filter` - Filter rows using pandas query
- `POST /correlate` - Calculate correlation matrix
- `POST /batch/process` - Process multiple files
- `POST /merge` - Merge multiple datasets
- `POST /compare` - Compare two datasets
- `POST /export/json` - Export to JSON
- `POST /export/excel` - Export to Excel
- `POST /export/parquet` - Export to Parquet
- `POST /export/html` - Export to HTML
- `POST /statistics` - Get detailed statistics
- `GET /health` - Health check

## Configuration

Set environment variables:
- `DATA_PATH` - Default data path
- `OUTPUT_PATH` - Default output path
- `Z_THRESHOLD` - Anomaly detection threshold

