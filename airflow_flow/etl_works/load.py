from sqlalchemy import create_engine
import os 

def load_data(df):
    username = os.getenv("PSQL_USERNAME")
    password = os.getenv("PSQL_PASSWORD")
    engine = create_engine(f"postgresql://{username}:{password}@localhost:5432/etl_db")

    if not username or not password:
        raise ValueError("Environment variables not set correctly. "
                         f"PSQL_USERNAME={username}, PSQL_PASSWORD={password}")

    print(f"Using username={username}, password={'*' * len(password)}")

    df.to_sql("clean_data", engine, if_exists="replace", index=False)