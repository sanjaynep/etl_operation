
# from pyspark.sql import SparkSession

# spark = SparkSession.builder.appName("FakerETL").getOrCreate()


# def extract_data():
#     df = spark.read.csv("fake_data.csv", header=True, inferSchema=True)
#     df.display()

 # for pyspark java is needed
import os
import pandas as pd

def extract_data():
    path = os.path.join("/mnt/c/Users/dipak/OneDrive/Desktop/etl_pipeline/data/fake_data.parquet")
    df = pd.read_parquet(path)
    print(df.shape)
    print(df.isnull().sum())
    return df

