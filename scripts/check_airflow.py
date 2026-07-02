from airflow.providers.postgres.hooks.postgres import PostgresHook
import airflow


print(f"Airflow version: {airflow.__version__}")
print("PostgresHook import OK")