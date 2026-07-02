#!/usr/bin/env sh
set -eu

PROJECT_ROOT="/mnt/c/Users/dipak/OneDrive/Desktop/etl_pipeline"
PROJECT_ROOT=$(printf '%s' "$PROJECT_ROOT" | tr -d '\r')

cd "$PROJECT_ROOT"
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel

AIRFLOW_VERSION=2.9.1
PYTHON_VERSION=3.12
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

python -m pip install "apache-airflow[postgres]==${AIRFLOW_VERSION}" --constraint "$CONSTRAINT_URL"

export AIRFLOW_HOME="$PROJECT_ROOT/airflow_home"
export AIRFLOW__CORE__DAGS_FOLDER="$PROJECT_ROOT/airflow_flow/dags"
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"

airflow db migrate
airflow db check
python -c 'from airflow.providers.postgres.hooks.postgres import PostgresHook; print("PostgresHook import OK")'