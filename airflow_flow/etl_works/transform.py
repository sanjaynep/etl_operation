from airflow_flow.etl_works.extract import extract_data
import pandas as pd

def transform_data(df):
    df['salary'] = df['salary'].fillna(df['salary'].mean())   
    df['email'] = df['email'].fillna("unknown@example.com")   
    df['dob'] = df['dob'].fillna(method='ffill')


    
