#!/usr/bin/env sh
set -eu

PROJECT_ROOT="/mnt/c/Users/dipak/OneDrive/Desktop/etl_pipeline"
PROJECT_ROOT=$(printf '%s' "$PROJECT_ROOT" | tr -d '\r')

cd "$PROJECT_ROOT"
. .venv/bin/activate
. scripts/airflow-env.sh

airflow db check
airflow dags list