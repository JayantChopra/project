"""Data Processor CLI main module.

This module provides the command-line interface for processing CSV data,
including summarization, anomaly detection, correlation analysis, and data export.
"""

import argparse
import os
from processor import DataProcessor
from utils import load_csv, save_json, file_hash
from logger import get_logger
from config import Config

logger = get_logger("main")


def summarize_data(processor, output_path):
    """Summarize the processed data and save to JSON file.

    This function invokes the processor's summarize method, saves the result as JSON,
    and logs the operation including the file hash for verification.

    Args:
        processor (DataProcessor): The data processor instance with loaded data.
        output_path (str): Path to save the summary JSON file.

    Raises:
        IOError: If saving the JSON file fails.
    """
    summary = processor.summarize()
    save_json(summary, output_path)
    logger.info(f"✅ Summary saved to {output_path}")
    logger.info(f"📦 File hash: {file_hash(output_path)}")


def detect_anomalies(processor, threshold):
    """Detect anomalies in the data using Z-score method.

    Performs outlier detection on numeric columns and logs warnings if anomalies are found.

    Args:
        processor (DataProcessor): The data processor instance with loaded data.
        threshold (float): Z-score threshold for considering a value an anomaly (default 3.0).

    Returns:
        list: List of detected anomalies, each as a dict with column, row, and value.

    Example:
        anomalies = detect_anomalies(processor, 2.5)
        if anomalies:
            print(f"Found {len(anomalies)} anomalies.")
    """
    anomalies = processor.detect_anomalies(z_threshold=threshold)
    if anomalies:
        logger.warning(f"⚠️ Anomalies detected: {len(anomalies)} found.")
        for anomaly in anomalies:
            logger.warning(f"  - {anomaly}")
    else:
        logger.info("No anomalies detected.")
    return anomalies


def correlation_analysis(processor):
    """Perform correlation analysis on numeric columns and save to JSON.

    Computes the Pearson correlation matrix for numeric data and saves it.
    Skips if no numeric columns are present.

    Args:
        processor (DataProcessor): The data processor instance with loaded data.

    Raises:
        ValueError: If correlation computation fails due to data issues.
    """
    try:
        numeric_data = processor.data.select_dtypes(include=['number'])
        if numeric_data.empty:
            logger.info("No numeric data available for correlation analysis.")
            return
        corr = numeric_data.corr().to_dict()
        corr_path = "output/correlation.json"
        save_json(corr, corr_path)
        logger.info(f"📊 Correlation matrix saved to {corr_path}")
        logger.info(f"📦 File hash: {file_hash(corr_path)}")
    except Exception as e:
        logger.error(f"Error in correlation analysis: {e}")
        raise


def export_cleaned_data(processor):
    """Export cleaned data to CSV file.

    Cleans the data (removes NaNs and duplicates) and saves to the specified path.
    Creates output directory if it doesn't exist.

    Args:
        processor (DataProcessor): The data processor instance with loaded data.

    Returns:
        str: Path to the exported cleaned CSV file.

    Raises:
        IOError: If saving the CSV file fails.
    """
    cleaned_path = processor.export_cleaned("output/cleaned.csv")
    logger.info(f"🧹 Cleaned data exported to {cleaned_path}")
    logger.info(f"📦 File hash: {file_hash(cleaned_path)}")
    return cleaned_path


def main():
    """Main entry point for the Data Processor CLI.

    Parses command line arguments and executes the specified action on the dataset.
    Supports actions: summarize, analyze (anomaly detection), correlate, export.

    Handles file existence checks and initializes the DataProcessor.

    Args from CLI:
        action (str): Required action to perform.
        --path (str): Path to input CSV file (default from config).
        --threshold (float): Z-score threshold for analyze action (default from config).

    Exits with error log if input file not found or invalid action.
    """
    parser = argparse.ArgumentParser(description="Data Processor CLI")
    parser.add_argument(
        "action",
        choices=["summarize", "analyze", "correlate", "export"],
        help="Action to perform on dataset"
    )
    parser.add_argument(
        "--path",
        type=str,
        default=Config.DATA_PATH,
        help="Path to the CSV file"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=Config.Z_THRESHOLD,
        help="Z-score threshold for anomaly detection"
    )

    args = parser.parse_args()

    if not os.path.exists(args.path):
        logger.error(f"❌ File not found: {args.path}")
        return 1  # Return non-zero for error

    try:
        data = load_csv(args.path)
        processor = DataProcessor(data)

        if args.action == "summarize":
            summarize_data(processor, Config.OUTPUT_PATH)
        elif args.action == "analyze":
            detect_anomalies(processor, args.threshold)
        elif args.action == "correlate":
            correlation_analysis(processor)
        elif args.action == "export":
            export_cleaned_data(processor)
    except Exception as e:
        logger.error(f"❌ Error during processing: {e}")
        return 1

    logger.info("🎉 Operation completed successfully.")
    return 0


if __name__ == "__main__":
    exit(main())
