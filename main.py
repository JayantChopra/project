import argparse
import os
import time
from typing import Dict, List, Optional, Tuple

import pandas as pd

from processor import DataProcessor
from utils import load_csv, save_json, file_hash
from logger import get_logger
from config import Config
from analyzer import DataAnalyzer

logger = get_logger("main")


def summarize_data(processor, output_path):
    summary = processor.summarize()
    save_json(summary, output_path)
    logger.info(f"Summary saved to {output_path}")
    logger.info(f"File hash: {file_hash(output_path)}")


def detect_anomalies(processor, threshold):
    anomalies = processor.detect_anomalies(z_threshold=threshold)
    if anomalies:
        logger.warning(f"Anomalies detected: {anomalies}")
    else:
        logger.info("No anomalies detected.")
    return anomalies


def correlation_analysis(processor, corr_output_path="output/correlation.json"):
    processor.clean()
    analyzer = DataAnalyzer(processor.get_data())
    corr = analyzer.correlation_matrix()
    if corr:
        save_json(corr, corr_output_path)
        logger.info(f"Correlation matrix saved to {corr_output_path}")
        logger.info(f"File hash: {file_hash(corr_output_path)}")
    else:
        logger.info("No numeric data available for correlation analysis.")


def export_cleaned_data(processor):
    cleaned_path = processor.export_cleaned("output/cleaned.csv")
    logger.info(f"Cleaned data exported to {cleaned_path}")
    logger.info(f"File hash: {file_hash(cleaned_path)}")


def ensure_parent_dir(path: str) -> None:
    """Ensure the directory for a target file path exists."""
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)


def save_dataframe_csv(df: pd.DataFrame, path: str) -> str:
    """Save a DataFrame to CSV, ensuring parent directory exists."""
    ensure_parent_dir(path)
    df.to_csv(path, index=False)
    return path


def preview_head(processor: DataProcessor, n: int, output_path: str) -> List[Dict]:
    processor.clean()
    preview = processor.get_data().head(max(0, n))
    records = preview.to_dict(orient="records")
    save_json(records, output_path)
    logger.info(f"Head preview (n={n}) saved to {output_path}")
    logger.info(f"File hash: {file_hash(output_path)}")
    return records


def preview_tail(processor: DataProcessor, n: int, output_path: str) -> List[Dict]:
    processor.clean()
    preview = processor.get_data().tail(max(0, n))
    records = preview.to_dict(orient="records")
    save_json(records, output_path)
    logger.info(f"Tail preview (n={n}) saved to {output_path}")
    logger.info(f"File hash: {file_hash(output_path)}")
    return records


def export_schema(processor: DataProcessor, output_path: str) -> Dict:
    processor.clean()
    df = processor.get_data()
    schema: Dict[str, Dict] = {}
    for column in df.columns:
        series = df[column]
        dtype_str = str(series.dtype)
        null_count = int(series.isna().sum())
        unique_count = int(series.nunique(dropna=True))
        is_numeric = pd.api.types.is_numeric_dtype(series)
        column_info: Dict[str, object] = {
            "dtype": dtype_str,
            "null_count": null_count,
            "unique_count": unique_count,
            "is_numeric": bool(is_numeric),
        }
        if is_numeric and not series.empty:
            desc = series.describe()
            column_info.update({
                "min": float(desc.get("min", float("nan"))) if pd.notna(desc.get("min", None)) else None,
                "max": float(desc.get("max", float("nan"))) if pd.notna(desc.get("max", None)) else None,
                "mean": float(desc.get("mean", float("nan"))) if pd.notna(desc.get("mean", None)) else None,
                "std": float(desc.get("std", float("nan"))) if pd.notna(desc.get("std", None)) else None,
            })
        schema[column] = column_info
    save_json(schema, output_path)
    logger.info(f"Schema saved to {output_path}")
    logger.info(f"File hash: {file_hash(output_path)}")
    return schema


def missingness_report(processor: DataProcessor, output_path: str) -> Dict[str, Dict[str, float]]:
    processor.clean()
    df = processor.get_data()
    total_rows = len(df) if len(df) > 0 else 1
    report: Dict[str, Dict[str, float]] = {}
    for column in df.columns:
        nulls = int(df[column].isna().sum())
        report[column] = {
            "nulls": nulls,
            "null_ratio": nulls / total_rows,
        }
    save_json(report, output_path)
    logger.info(f"Missingness report saved to {output_path}")
    logger.info(f"File hash: {file_hash(output_path)}")
    return report


def value_counts_report(processor: DataProcessor, top_n: int, output_path: str) -> Dict[str, List[Tuple[str, int]]]:
    processor.clean()
    df = processor.get_data()
    result: Dict[str, List[Tuple[str, int]]] = {}
    for column in df.columns:
        series = df[column]
        if pd.api.types.is_numeric_dtype(series):
            continue
        counts = series.value_counts(dropna=True).head(top_n)
        result[column] = [(str(idx), int(val)) for idx, val in counts.items()]
    save_json(result, output_path)
    logger.info(f"Value counts (top {top_n}) saved to {output_path}")
    logger.info(f"File hash: {file_hash(output_path)}")
    return result


def filter_rows(processor: DataProcessor, query: str, output_path: str) -> str:
    processor.clean()
    df = processor.get_data()
    try:
        filtered = df.query(query, engine="python")
    except Exception as exc:
        logger.error(f"Failed to apply query: {exc}")
        raise
    path = save_dataframe_csv(filtered, output_path)
    logger.info(f"Filtered data saved to {path} (rows={len(filtered)})")
    logger.info(f"File hash: {file_hash(path)}")
    return path


def sample_rows(processor: DataProcessor, n: Optional[int], frac: Optional[float], seed: int, output_path: str) -> str:
    processor.clean()
    df = processor.get_data()
    if n is None and frac is None:
        n = 5
    sampled = df.sample(n=n, frac=frac, random_state=seed) if frac is not None else df.sample(n=n, random_state=seed)
    path = save_dataframe_csv(sampled, output_path)
    logger.info(f"Sampled data saved to {path} (rows={len(sampled)})")
    logger.info(f"File hash: {file_hash(path)}")
    return path


def split_dataset(processor: DataProcessor, test_size: float, seed: int, train_path: str, test_path: str) -> Tuple[str, str]:
    processor.clean()
    df = processor.get_data()
    if not 0.0 < test_size < 1.0:
        raise ValueError("test_size must be between 0 and 1")
    shuffled = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    test_count = int(len(shuffled) * test_size)
    test_df = shuffled.iloc[:test_count]
    train_df = shuffled.iloc[test_count:]
    train_path = save_dataframe_csv(train_df, train_path)
    test_path = save_dataframe_csv(test_df, test_path)
    logger.info(f"Train/Test split saved to {train_path} and {test_path}")
    logger.info(f"Train hash: {file_hash(train_path)} | Test hash: {file_hash(test_path)}")
    return train_path, test_path


def normalize_numeric(processor: DataProcessor, output_path: str) -> str:
    processor.clean()
    df = processor.get_data()
    numeric_cols = df.select_dtypes(include=["number"]).columns
    normalized = df.copy()
    for col in numeric_cols:
        series = df[col]
        mean = series.mean()
        std = series.std(ddof=0)
        if pd.isna(std) or std == 0:
            continue
        normalized[col] = (series - mean) / std
    path = save_dataframe_csv(normalized, output_path)
    logger.info(f"Normalized data saved to {path}")
    logger.info(f"File hash: {file_hash(path)}")
    return path


def correlations_topk(processor: DataProcessor, top_k: int, output_path: str) -> List[Dict[str, object]]:
    processor.clean()
    df = processor.get_data().select_dtypes(include=["number"])
    if df.empty:
        save_json([], output_path)
        logger.info("No numeric data available for correlation ranking.")
        return []
    corr = df.corr()
    pairs: List[Tuple[str, str, float]] = []
    cols = list(corr.columns)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            a, b = cols[i], cols[j]
            value = float(corr.loc[a, b])
            pairs.append((a, b, value))
    pairs_sorted = sorted(pairs, key=lambda x: abs(x[2]), reverse=True)[:max(0, top_k)]
    result = [{"col_a": a, "col_b": b, "corr": v, "abs_corr": abs(v)} for a, b, v in pairs_sorted]
    save_json(result, output_path)
    logger.info(f"Top-{top_k} correlations saved to {output_path}")
    logger.info(f"File hash: {file_hash(output_path)}")
    return result


def text_length_stats(processor: DataProcessor, output_path: str, include_columns: Optional[List[str]] = None) -> Dict[str, Dict[str, float]]:
    processor.clean()
    df = processor.get_data()
    columns = include_columns if include_columns else [c for c in df.columns if df[c].dtype == object]
    stats: Dict[str, Dict[str, float]] = {}
    for col in columns:
        lengths = df[col].astype(str).fillna("").str.len()
        if lengths.empty:
            continue
        desc = lengths.describe()
        stats[col] = {
            "min": float(desc.get("min", 0.0)),
            "max": float(desc.get("max", 0.0)),
            "mean": float(desc.get("mean", 0.0)),
            "std": float(desc.get("std", 0.0)),
            "25%": float(desc.get("25%", 0.0)),
            "50%": float(desc.get("50%", 0.0)),
            "75%": float(desc.get("75%", 0.0)),
        }
    save_json(stats, output_path)
    logger.info(f"Text length stats saved to {output_path}")
    logger.info(f"File hash: {file_hash(output_path)}")
    return stats


def list_columns(processor: DataProcessor, output_path: str) -> Dict[str, str]:
    processor.clean()
    df = processor.get_data()
    listing = {col: str(df[col].dtype) for col in df.columns}
    save_json(listing, output_path)
    logger.info(f"Column listing saved to {output_path}")
    logger.info(f"File hash: {file_hash(output_path)}")
    return listing


def file_info(path: str, output_path: str) -> Dict[str, object]:
    info: Dict[str, object] = {}
    if os.path.exists(path):
        stat = os.stat(path)
        info = {
            "path": path,
            "size_bytes": stat.st_size,
            "modified_time": stat.st_mtime,
            "sha256": file_hash(path),
        }
    save_json(info, output_path)
    logger.info(f"File info saved to {output_path}")
    logger.info(f"File hash: {file_hash(output_path)}")
    return info


def profile_operations(processor: DataProcessor, outdir: str) -> Dict[str, float]:
    """Profile a few common operations and write timings to JSON."""
    timings: Dict[str, float] = {}
    # Time clean
    start = time.time()
    processor.clean()
    timings["clean_s"] = round(time.time() - start, 6)

    # Time summarize
    start = time.time()
    _ = processor.summarize()
    timings["summarize_s"] = round(time.time() - start, 6)

    # Time correlation
    start = time.time()
    analyzer = DataAnalyzer(processor.get_data())
    _ = analyzer.correlation_matrix()
    timings["correlation_s"] = round(time.time() - start, 6)

    out_path = os.path.join(outdir, "performance.json")
    save_json(timings, out_path)
    logger.info(f"Performance profile saved to {out_path}")
    logger.info(f"File hash: {file_hash(out_path)}")
    return timings


def generate_report(processor: DataProcessor, outdir: str, topk: int) -> Dict[str, object]:
    """Generate a consolidated report with schema, missingness and top correlations."""
    schema_path = os.path.join(outdir, "schema.json")
    missing_path = os.path.join(outdir, "missingness.json")
    corrk_path = os.path.join(outdir, "correlations_topk.json")

    schema = export_schema(processor, schema_path)
    missing = missingness_report(processor, missing_path)
    corrk = correlations_topk(processor, topk, corrk_path)

    report = {
        "schema": schema,
        "missingness": missing,
        "top_correlations": corrk,
    }
    report_path = os.path.join(outdir, "report.json")
    save_json(report, report_path)
    logger.info(f"Consolidated report saved to {report_path}")
    logger.info(f"File hash: {file_hash(report_path)}")
    return report


def main():
    parser = argparse.ArgumentParser(
        description="Data Processor CLI",
        epilog=(
            "Actions: summarize, analyze, correlate, export, preview, tail, schema, "
            "missing, value_counts, filter, sample, split, normalize, corr_topk, "
            "text_lengths, list_columns, fileinfo, profile, report"
        ),
    )
    parser.add_argument(
        "action",
        choices=[
            "summarize",
            "analyze",
            "correlate",
            "export",
            "preview",
            "tail",
            "schema",
            "missing",
            "value_counts",
            "filter",
            "sample",
            "split",
            "normalize",
            "corr_topk",
            "text_lengths",
            "list_columns",
            "fileinfo",
            "profile",
            "describe",
        ],
        help="Action to perform on dataset"
    )
    parser.add_argument(
        "--path",
        type=str,
        default=Config.DATA_PATH,
        help="Path to the CSV file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=Config.OUTPUT_PATH,
        help="Output path for summary JSON"
    )
    parser.add_argument(
        "--outdir",
        type=str,
        default="output",
        help="Directory for outputs like CSV/JSON files",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=Config.Z_THRESHOLD,
        help="Z-score threshold for anomaly detection"
    )
    parser.add_argument(
        "--corr-output",
        type=str,
        default="output/correlation.json",
        help="Output path for correlation matrix JSON"
    )
    parser.add_argument(
        "--n",
        type=int,
        default=5,
        help="Row count for preview/head/tail and sampling when frac is not set",
    )
    parser.add_argument(
        "--frac",
        type=float,
        default=None,
        help="Fraction for sampling (0-1), used if provided",
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="pandas.DataFrame.query string for filtering rows",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for sampling/splitting",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Test size fraction for train/test split (0-1)",
    )
    parser.add_argument(
        "--describe-output",
        type=str,
        default="output/describe.json",
        help="Output path for describe JSON"
    )

    args = parser.parse_args()

    if not os.path.exists(args.path):
        logger.error(f"File not found: {args.path}")
        return

    data = load_csv(args.path)
    processor = DataProcessor(data)

    if args.action == "summarize":
        summarize_data(processor, args.output)
    elif args.action == "analyze":
        detect_anomalies(processor, args.threshold)
    elif args.action == "correlate":
        correlation_analysis(processor, args.corr_output)
    elif args.action == "export":
        export_cleaned_data(processor)
    elif args.action == "preview":
        preview_path = os.path.join(args.outdir, "preview_head.json")
        preview_head(processor, args.n, preview_path)
    elif args.action == "tail":
        tail_path = os.path.join(args.outdir, "preview_tail.json")
        preview_tail(processor, args.n, tail_path)
    elif args.action == "schema":
        schema_path = os.path.join(args.outdir, "schema.json")
        export_schema(processor, schema_path)
    elif args.action == "missing":
        miss_path = os.path.join(args.outdir, "missingness.json")
        missingness_report(processor, miss_path)
    elif args.action == "value_counts":
        vc_path = os.path.join(args.outdir, "value_counts.json")
        value_counts_report(processor, args.n, vc_path)
    elif args.action == "filter":
        if not args.query:
            logger.error("--query is required for filter action")
            return
        filtered_csv = os.path.join(args.outdir, "filtered.csv")
        filter_rows(processor, args.query, filtered_csv)
    elif args.action == "sample":
        sampled_csv = os.path.join(args.outdir, "sampled.csv")
        sample_rows(processor, args.n if args.frac is None else None, args.frac, args.seed, sampled_csv)
    elif args.action == "split":
        train_csv = os.path.join(args.outdir, "train.csv")
        test_csv = os.path.join(args.outdir, "test.csv")
        split_dataset(processor, args.test_size, args.seed, train_csv, test_csv)
    elif args.action == "normalize":
        norm_csv = os.path.join(args.outdir, "normalized.csv")
        normalize_numeric(processor, norm_csv)
    elif args.action == "corr_topk":
        corrk_json = os.path.join(args.outdir, "correlations_topk.json")
        correlations_topk(processor, args.topk, corrk_json)
    elif args.action == "text_lengths":
        tl_json = os.path.join(args.outdir, "text_length_stats.json")
        text_length_stats(processor, tl_json)
    elif args.action == "list_columns":
        cols_json = os.path.join(args.outdir, "columns.json")
        list_columns(processor, cols_json)
    elif args.action == "fileinfo":
        info_json = os.path.join(args.outdir, "fileinfo.json")
        file_info(args.path, info_json)
    elif args.action == "profile":
        profile_operations(processor, args.outdir)
    elif args.action == "describe":
        desc_path = args.describe_output
        description = processor.describe()
        save_json(description, desc_path)
        logger.info(f"Dataset description saved to {desc_path}")
        logger.info(f"File hash: {file_hash(desc_path)}")

    logger.info("Operation completed successfully.")


if __name__ == "__main__":
    main()
