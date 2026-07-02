#!/usr/bin/env sh

PROJECT_ROOT="/mnt/c/Users/dipak/OneDrive/Desktop/etl_pipeline"
PROJECT_ROOT=$(printf '%s' "$PROJECT_ROOT" | tr -d '\r')

export AIRFLOW_HOME="$PROJECT_ROOT/airflow_home"
export AIRFLOW__CORE__DAGS_FOLDER="$PROJECT_ROOT/airflow_flow/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"