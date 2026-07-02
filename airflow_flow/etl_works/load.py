from pathlib import Path
from airflow.providers.postgres.hooks.postgres import PostgresHook
import pandas as pd
from io import StringIO
from sqlalchemy import create_engine


def load_data(input_path):
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Missing input file: {input_path}")

    df = pd.read_parquet(input_path)
    
    hook = PostgresHook(postgres_conn_id="etl_postgres")
    conn = hook.get_conn()
    cursor = conn.cursor()

    try:
        cursor.execute("DROP TABLE IF EXISTS clean_data")
        cursor.execute("""
            CREATE TABLE clean_data (
                name            TEXT,
                email           TEXT,
                salary          FLOAT,
                dob             DATE,  
                year_of_birth   INT
            )
        """)

        buffer = StringIO()
        df.to_csv(buffer, index=False, header=False)
        buffer.seek(0)

        cursor.copy_expert(
            "COPY clean_data FROM STDIN WITH CSV",
            buffer
        )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()