from pathlib import Path

import pandas as pd
import json
from datetime import datetime, timezone
import psutil

PROJECT_ROOT = Path("/mnt/c/Users/dipak/OneDrive/Desktop/etl_pipeline")
SOURCE_FILE = PROJECT_ROOT / "data" / "fake_data.parquet"
STAGING_DIR = PROJECT_ROOT / "data" / "staging"
EXTRACTED_FILE = STAGING_DIR / "extracted.parquet"


def extract_data():
    df = pd.read_parquet(SOURCE_FILE)
    metrics = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "service": "etl_faker_pipeline",
    "cpu_percent": psutil.cpu_percent(interval=None),
    "memory_percent": psutil.virtual_memory().percent,
    "disk_percent": psutil.disk_usage("/mnt/c/Users/dipak/OneDrive/Desktop/etl_pipeline").percent,
    "status_code": 200,
    "log_level": "INFO",
    "last_message": f"extracted rows={len(df)}",
}
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(EXTRACTED_FILE, index=False)
    return str(EXTRACTED_FILE)