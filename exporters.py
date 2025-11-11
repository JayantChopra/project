"""Export utilities for different file formats."""
import pandas as pd
import json
import os
from logger import get_logger

logger = get_logger("exporters")

def export_to_json(df, output_path):
    """Export dataframe to JSON format."""
    records = df.to_dict(orient="records")
    with open(output_path, "w") as f:
        json.dump(records, f, indent=2)
    logger.info(f"Exported {len(df)} rows to JSON: {output_path}")
    return output_path

def export_to_excel(df, output_path, sheet_name="Sheet1"):
    """Export dataframe to Excel format."""
    df.to_excel(output_path, sheet_name=sheet_name, index=False)
    logger.info(f"Exported {len(df)} rows to Excel: {output_path}")
    return output_path

def export_to_parquet(df, output_path):
    """Export dataframe to Parquet format."""
    df.to_parquet(output_path, index=False)
    logger.info(f"Exported {len(df)} rows to Parquet: {output_path}")
    return output_path

def export_to_html(df, output_path):
    """Export dataframe to HTML table format."""
    html = df.to_html(index=False)
    with open(output_path, "w") as f:
        f.write(html)
    logger.info(f"Exported {len(df)} rows to HTML: {output_path}")
    return output_path

def export_statistics(df, output_path="output/statistics.json"):
    """Export detailed statistics for all columns."""
    stats = {}
    for col in df.columns:
        series = df[col]
        col_stats = {
            "dtype": str(series.dtype),
            "null_count": int(series.isna().sum()),
            "null_percentage": float(series.isna().sum() / len(series) * 100),
            "unique_count": int(series.nunique()),
        }
        
        if pd.api.types.is_numeric_dtype(series):
            col_stats.update({
                "min": float(series.min()) if not series.empty else None,
                "max": float(series.max()) if not series.empty else None,
                "mean": float(series.mean()) if not series.empty else None,
                "median": float(series.median()) if not series.empty else None,
                "std": float(series.std()) if not series.empty else None,
            })
        else:
            col_stats["most_common"] = series.value_counts().head(5).to_dict()
        
        stats[col] = col_stats
    
    with open(output_path, "w") as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Statistics exported to {output_path}")
    return stats

