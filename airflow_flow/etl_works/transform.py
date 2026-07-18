
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path("/mnt/c/Users/dipak/OneDrive/Desktop/etl_pipeline")
STAGING_DIR = PROJECT_ROOT / "data" / "staging"
TRANSFORMED_FILE = STAGING_DIR / "transformed.parquet"


def transform_data(input_path):
    df = pd.read_parquet(input_path)
    df["salary"] = df["salary"].fillna(df["salary"].mean())
    df["email"] = df["email"].fillna("unknown@example.com")
    df["dob"] = df["dob"].ffill()

    df["year_of_birth"] = pd.to_datetime(df["dob"], errors="coerce").dt.year
    df = df[df["salary"] > 50000]

    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(TRANSFORMED_FILE, index=False)

    print("Transformation complete")
    print(df.head(5))
    return str(TRANSFORMED_FILE)
