
# from pyspark.sql import SparkSession

# spark = SparkSession.builder.appName("FakerETL").getOrCreate()


# def extract_data():
#     df = spark.read.csv("fake_data.csv", header=True, inferSchema=True)
#     df.display()

 # for pyspark java is needed
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path("/mnt/c/Users/dipak/OneDrive/Desktop/etl_pipeline")
SOURCE_FILE = PROJECT_ROOT / "data" / "fake_data.parquet"
STAGING_DIR = PROJECT_ROOT / "data" / "staging"
EXTRACTED_FILE = STAGING_DIR / "extracted.parquet"


def extract_data():
    df = pd.read_parquet(SOURCE_FILE)
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(EXTRACTED_FILE, index=False)
    print(df.shape)
    print(df.isnull().sum())
    return str(EXTRACTED_FILE)

