import argparse
import os
from processor import DataProcessor
from utils import load_csv, save_json, file_hash
from logger import get_logger
from config import Config

logger = get_logger("main")


def summarize_data(processor, output_path):
    """
    Generate a summary of the dataset and save it to a JSON file.

    Args:
        processor (DataProcessor): The data processor instance.
        output_path (str): Path where the summary JSON should be saved.

    Returns:
        None
    """
    summary = processor.summarize()
    save_json(summary, output_path)
    logger.info(f"✅ Summary saved to {output_path}")
    logger.info(f"📦 File hash: {file_hash(output_path)}")


def detect_anomalies(processor, threshold):
    """
    Detect anomalies in the dataset using Z-score method.

    Args:
        processor (DataProcessor): The data processor instance.
        threshold (float): Z-score threshold for anomaly detection.

    Returns:
        list: List of detected anomalies, or empty list if none.
    """
    anomalies = processor.detect_anomalies(z_threshold=threshold)
    if anomalies:
        logger.warning(f"⚠️ Anomalies detected: {anomalies}")
    else:
        logger.info("No anomalies detected.")
    return anomalies


def correlation_analysis(processor):
    """
    Perform correlation analysis on numeric columns and save the matrix to JSON.

    Args:
        processor (DataProcessor): The data processor instance.

    Returns:
        None
    """
    corr = processor.data.corr().to_dict()
    if corr:
        corr_path = "output/correlation.json"
        save_json(corr, corr_path)
        logger.info(f"📊 Correlation matrix saved to {corr_path}")
        logger.info(f"📦 File hash: {file_hash(corr_path)}")
    else:
        logger.info("No numeric data available for correlation analysis.")


def export_cleaned_data(processor):
    """
    Export the cleaned dataset to a CSV file.

    Args:
        processor (DataProcessor): The data processor instance.

    Returns:
        None
    """
    cleaned_path = processor.export_cleaned("output/cleaned.csv")
    logger.info(f"🧼 Cleaned data exported to {cleaned_path}")
    logger.info(f"📦 File hash: {file_hash(cleaned_path)}")


def main():
    """
    Main entry point for the Data Processor CLI.

    Parses command-line arguments and executes the specified action:
    - summarize: Generate and save data summary.
    - analyze: Detect and log anomalies.
    - correlate: Compute and save correlation matrix.
    - export: Export cleaned data.

    Handles file existence checks and logging.
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
        return

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

    logger.info("🎉 Operation completed successfully.")


if __name__ == "__main__":
    main()
