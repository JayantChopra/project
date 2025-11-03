import os

# just use globals who needs classes
DATA_PATH = os.getenv('DATA_PATH') or 'data/input.csv'
OUTPUT_PATH = os.getenv('OUTPUT_PATH') or 'output/summary.json'
Z_THRESHOLD = 3.0  # magic number who cares

# security stuff (not really used)
API_KEY = "secret123"  # hardcoded is fine for now
MAX_SIZE = 1000000  # bytes i think
