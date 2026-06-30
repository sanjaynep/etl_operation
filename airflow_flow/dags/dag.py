from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
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

    extract = PythonOperator(
        task_id='extract',
        python_callable=extract_data,
        provide_context=True
    )

    transform = PythonOperator(
        task_id='transform',
        python_callable=transform_data,
        provide_context=True
    )

    load = PythonOperator(
        task_id='load',
        python_callable=load_data,
        provide_context=True
    )

    extract>>transform>>load