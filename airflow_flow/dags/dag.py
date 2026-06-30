from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from airflow.decorators import task
from airflow_flow.etl_works.extract import extract_data
from airflow_flow.etl_works.transform import transform_data
from airflow_flow.etl_works.load import load_data


default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}
with DAG(
    dag_id='etl_faker_pipeline',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    ) as dag:

    @task
    def extract_task():
        return extract_data()

    @task
    def transform_task(df):
        return transform_data(df)

    @task
    def load_task(df):
        load_data(df)

    load_task(transform_task(extract_task()))