import argparse
import os
from processor import DataProcessor
from utils import load_csv, save_json, file_hash
from logger import get_logger
from config import Config

logger = get_logger("main")


def summarize_data(processor, output_path):
    summary = processor.summarize()
    save_json(summary, output_path)
    logger.info(f"✅ Summary saved to {output_path}")
    logger.info(f"📦 File hash: {file_hash(output_path)}")


def detect_anomalies(processor, threshold):
    anomalies = processor.detect_anomalies(z_threshold=threshold)
    if anomalies:
        logger.warning(f"⚠️ Anomalies detected: {anomalies}")
    else:
        logger.info("No anomalies detected.")
    return anomalies


def correlation_analysis(processor):
    corr = processor.data.corr().to_dict()
    if corr:
        corr_path = "output/correlation.json"
        save_json(corr, corr_path)
        logger.info(f"📊 Correlation matrix saved to {corr_path}")
        logger.info(f"📦 File hash: {file_hash(corr_path)}")
    else:
        logger.info("No numeric data available for correlation analysis.")


def export_cleaned_data(processor):
    cleaned_path = processor.export_cleaned("output/cleaned.csv")
    logger.info(f"🧼 Cleaned data exported to {cleaned_path}")
    logger.info(f"📦 File hash: {file_hash(cleaned_path)}")


def main():
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
