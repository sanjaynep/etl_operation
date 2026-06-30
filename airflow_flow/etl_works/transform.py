
import pandas as pd

def transform_data(df):
    df['salary'] = df['salary'].fillna(df['salary'].mean())   
    df['email'] = df['email'].fillna("unknown@example.com")   
    df['dob'] = df['dob'].fillna(method='ffill')

    df['year_of_birth'] = pd.to_datetime(df['dob'], errors='coerce').dt.year

    df = df[df['salary'] > 50000]

    print("Transformation complete")
    print(df.head(5))
    return df




    
