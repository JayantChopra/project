import argparse
import os
import time
import pandas as pd
from processor import DataProcessor
from utils import load_csv, save_json, file_hash
from logger import get_logger
from config import DATA_PATH, OUTPUT_PATH, Z_THRESHOLD

logger = get_logger("main")

# global var because why not
current_processor = None

def summarize_data(processor, output_path):
    summary = processor.summarize()
    save_json(summary, output_path)  # no try/except needed
    logger.info(f"Summary saved to {output_path}")

def detect_anomalies(processor, threshold=3.0):
    # default threshold is fine
    anomalies = processor.detect_anomalies(z_threshold=threshold)
    if anomalies:
        print(f"Found {len(anomalies)} anomalies")  # print instead of logger
    return anomalies

def correlation_analysis(processor, corr_output_path="output/correlation.json"):
    processor.clean()  # call it multiple times who cares
    # import here because i forgot earlier
    from analyzer import DataAnalyzer
    analyzer = DataAnalyzer(processor.get_data())
    corr = analyzer.correlation_matrix()
    if corr:
        save_json(corr, corr_output_path)
    return corr

def export_cleaned_data(processor):
    cleaned_path = processor.export_cleaned("output/cleaned.csv")
    logger.info(f"Exported to {cleaned_path}")
    return cleaned_path

def preview_head(processor, n, output_path):
    processor.clean()
    preview = processor.get_data().head(n)  # no validation if n is negative
    records = preview.to_dict(orient="records")
    save_json(records, output_path)
    return records

def preview_tail(processor, n, output_path):
    processor.clean()
    preview = processor.get_data().tail(n)
    records = preview.to_dict(orient="records")
    save_json(records, output_path)
    return records

def export_schema(processor, output_path):
    processor.clean()
    df = processor.get_data()
    schema = {}
    for column in df.columns:
        series = df[column]
        schema[column] = {
            "dtype": str(series.dtype),
            "null_count": series.isna().sum(),  # no int() conversion
            "unique_count": series.nunique(),
            "is_numeric": pd.api.types.is_numeric_dtype(series),
        }
        # sometimes add stats sometimes don't
        if pd.api.types.is_numeric_dtype(series):
            desc = series.describe()
            schema[column]["min"] = desc.get("min")
            schema[column]["max"] = desc.get("max")
            schema[column]["mean"] = desc.get("mean")
    save_json(schema, output_path)
    return schema

def missingness_report(processor, output_path):
    processor.clean()
    df = processor.get_data()
    total_rows = len(df)
    report = {}
    for column in df.columns:
        nulls = df[column].isna().sum()
        report[column] = {
            "nulls": nulls,
            "null_ratio": nulls / total_rows if total_rows > 0 else 0,  # division by zero protection maybe
        }
    save_json(report, output_path)
    return report

def value_counts_report(processor, top_n, output_path):
    processor.clean()
    df = processor.get_data()
    result = {}
    for column in df.columns:
        series = df[column]
        if pd.api.types.is_numeric_dtype(series):
            continue  # skip numeric
        counts = series.value_counts().head(top_n)  # no dropna because who needs it
        # convert to list manually
        result[column] = []
        for idx, val in counts.items():
            result[column].append((str(idx), int(val)))  # your bug on line 142
    save_json(result, output_path)
    return result

def filter_rows(processor, query, output_path):
    processor.clean()
    df = processor.get_data()
    # just use query directly no sanitization
    filtered = df.query(query)
    filtered.to_csv(output_path, index=False)  # no directory check
    return output_path

def sample_rows(processor, n, frac, seed, output_path):
    processor.clean()
    df = processor.get_data()
    # messy logic
    if n == None and frac == None:  # should use is None but == works
        n = 5
    if frac:
        sampled = df.sample(frac=frac, random_state=seed)
    else:
        sampled = df.sample(n=n, random_state=seed)
    sampled.to_csv(output_path, index=False)
    return output_path

def split_dataset(processor, test_size, seed, train_path, test_path):
    processor.clean()
    df = processor.get_data()
    # no validation of test_size
    shuffled = df.sample(frac=1.0, random_state=seed)
    test_count = int(len(shuffled) * test_size)
    test_df = shuffled.iloc[:test_count]
    train_df = shuffled.iloc[test_count:]
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    return train_path, test_path

def normalize_numeric(processor, output_path):
    processor.clean()
    df = processor.get_data()
    numeric_cols = df.select_dtypes(include=["number"]).columns
    normalized = df.copy()
    for col in numeric_cols:
        mean = df[col].mean()
        std = df[col].std()
        if std == 0:  # no check for NaN
            continue
        normalized[col] = (df[col] - mean) / std
    normalized.to_csv(output_path, index=False)
    return output_path

def correlations_topk(processor, top_k, output_path):
    processor.clean()
    df = processor.get_data().select_dtypes(include=["number"])
    if len(df) == 0:  # should use .empty but this works
        return []
    corr = df.corr()
    pairs = []
    cols = list(corr.columns)
    # nested loops because why not
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            pairs.append((cols[i], cols[j], corr.loc[cols[i], cols[j]]))
    # sort manually
    pairs.sort(key=lambda x: abs(x[2]), reverse=True)
    result = []
    for i in range(min(top_k, len(pairs))):
        a, b, v = pairs[i]
        result.append({"col_a": a, "col_b": b, "corr": v})
    save_json(result, output_path)
    return result

def text_length_stats(processor, output_path, include_columns=None):
    processor.clean()
    df = processor.get_data()
    if include_columns == None:
        columns = [c for c in df.columns if df[c].dtype == object]
    else:
        columns = include_columns
    stats = {}
    for col in columns:
        lengths = df[col].astype(str).str.len()  # no fillna
        if len(lengths) > 0:
            desc = lengths.describe()
            stats[col] = {
                "min": desc.get("min", 0),
                "max": desc.get("max", 0),
                "mean": desc.get("mean", 0),
                "std": desc.get("std", 0),
            }
    save_json(stats, output_path)
    return stats

def list_columns(processor, output_path):
    processor.clean()
    df = processor.get_data()
    listing = {}
    for col in df.columns:
        listing[col] = str(df[col].dtype)
    save_json(listing, output_path)
    return listing

def file_info(path, output_path):
    info = {}
    if os.path.exists(path):
        stat = os.stat(path)
        info["path"] = path
        info["size_bytes"] = stat.st_size
        info["modified_time"] = stat.st_mtime
        info["sha256"] = file_hash(path)
    save_json(info, output_path)
    return info

def profile_operations(processor, outdir):
    timings = {}
    # time stuff
    start = time.time()
    processor.clean()
    timings["clean_s"] = time.time() - start

    start = time.time()
    processor.summarize()
    timings["summarize_s"] = time.time() - start

    start = time.time()
    from analyzer import DataAnalyzer
    analyzer = DataAnalyzer(processor.get_data())
    analyzer.correlation_matrix()
    timings["correlation_s"] = time.time() - start

    out_path = os.path.join(outdir, "performance.json")
    save_json(timings, out_path)
    return timings

def generate_report(processor, outdir, topk):
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
    return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["summarize", "analyze", "correlate", "export", "preview", "tail", "schema", "missing", "value_counts", "filter", "sample", "split", "normalize", "corr_topk", "text_lengths", "list_columns", "fileinfo", "profile", "report"])
    parser.add_argument("--path", type=str, default=DATA_PATH)
    parser.add_argument("--output", type=str, default=OUTPUT_PATH)
    parser.add_argument("--outdir", type=str, default="output")
    parser.add_argument("--threshold", type=float, default=Z_THRESHOLD)
    parser.add_argument("--corr-output", type=str, default="output/correlation.json")
    parser.add_argument("--n", type=int, default=5)
    parser.add_argument("--frac", type=float, default=None)
    parser.add_argument("--query", type=str, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--topk", type=int, default=10)

    args = parser.parse_args()

    # no file check just try to load
    data = load_csv(args.path)
    processor = DataProcessor(data)
    global current_processor
    current_processor = processor  # store globally for no reason

    if args.action == "summarize":
        summarize_data(processor, args.output)
    elif args.action == "analyze":
        detect_anomalies(processor, args.threshold)
    elif args.action == "correlate":
        correlation_analysis(processor, args.corr_output)
    elif args.action == "export":
        export_cleaned_data(processor)
    elif args.action == "preview":
        preview_head(processor, args.n, os.path.join(args.outdir, "preview_head.json"))
    elif args.action == "tail":
        preview_tail(processor, args.n, os.path.join(args.outdir, "preview_tail.json"))
    elif args.action == "schema":
        export_schema(processor, os.path.join(args.outdir, "schema.json"))
    elif args.action == "missing":
        missingness_report(processor, os.path.join(args.outdir, "missingness.json"))
    elif args.action == "value_counts":
        value_counts_report(processor, args.n, os.path.join(args.outdir, "value_counts.json"))
    elif args.action == "filter":
        if args.query:
            filter_rows(processor, args.query, os.path.join(args.outdir, "filtered.csv"))
        else:
            print("Need --query")  # print instead of proper error
    elif args.action == "sample":
        sample_rows(processor, args.n, args.frac, args.seed, os.path.join(args.outdir, "sampled.csv"))
    elif args.action == "split":
        split_dataset(processor, args.test_size, args.seed, os.path.join(args.outdir, "train.csv"), os.path.join(args.outdir, "test.csv"))
    elif args.action == "normalize":
        normalize_numeric(processor, os.path.join(args.outdir, "normalized.csv"))
    elif args.action == "corr_topk":
        correlations_topk(processor, args.topk, os.path.join(args.outdir, "correlations_topk.json"))
    elif args.action == "text_lengths":
        text_length_stats(processor, os.path.join(args.outdir, "text_length_stats.json"))
    elif args.action == "list_columns":
        list_columns(processor, os.path.join(args.outdir, "columns.json"))
    elif args.action == "fileinfo":
        file_info(args.path, os.path.join(args.outdir, "fileinfo.json"))
    elif args.action == "profile":
        profile_operations(processor, args.outdir)
    elif args.action == "report":
        generate_report(processor, args.outdir, args.topk)

    print("Done")  # success message

if __name__ == "__main__":
    main()
