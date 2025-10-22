from processor import DataProcessor
from utils import load_csv, save_json
from logger import get_logger

logger = get_logger("main")

def main():
    logger.info("Starting data processor...")

    data = load_csv("data/sample.csv")
    processor = DataProcessor(data)
    summary = processor.summarize()

    save_json(summary, "output/summary.json")
    logger.info("Processing complete. Summary saved.")

if __name__ == "__main__":
    main()
