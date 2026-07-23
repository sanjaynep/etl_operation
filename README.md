# ETL Operation

An Apache Airflow-orchestrated ETL pipeline that extracts data from Parquet files, transforms it, and loads it into a PostgreSQL database. Built and tested on WSL (Windows Subsystem for Linux).

## Overview

This project implements a simple, three-stage ETL workflow managed by Apache Airflow Where logs are collected and preprocessed each line so that it will be fitted in model for anomaly detection and then if anomaly detecte it will provide alert message of problem and suggestion through email:

```
extract_task → transform_task → load_task → logs collection → anomAaly detection → llm suggestion 
```

- **Extract** — Reads source data from a Parquet file.
- **Transform** — Cleans and reshapes the extracted data for loading.
- **Load** — Writes the transformed data into a PostgreSQL database (`etl_db`).

The DAG tasks are chained sequentially, so each stage only runs once the previous one completes successfully.

## Project Structure

```
etl_operation/
├── airflow_flow/     # Airflow DAG definition(s) for the ETL pipeline
├── airflow_home/      # AIRFLOW_HOME — Airflow config, logs, and metadata
├── data/               # Source data files (Parquet)
├── scripts/            # ETL logic — extract, transform, and load scripts
├── test.py             # Test script
└── .gitignore
```

## Tech Stack

- **Python** — core ETL logic
- **Apache Airflow** — workflow orchestration and scheduling
- **PostgreSQL** — data warehouse / load target
- **Shell scripting** — environment setup and automation
- **WSL** — development environment
- **Qwen** - suggestion llm

## Prerequisites

- Python 3.8+
- PostgreSQL (running locally or accessible remotely) with a database named `etl_db`
- Apache Airflow
- WSL (if developing on Windows)

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/sanjaynep/etl_operation.git
   cd etl_operation
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   > If a `requirements.txt` isn't present yet, install at minimum: `apache-airflow`, `pandas`, `pyarrow`, `psycopg2-binary` (or `sqlalchemy`).

4. **Set the Airflow home directory**
   ```bash
   . scripts/airflow-env.sh
   . scripts/airflow-setip.sh
   ```

5. **Configure PostgreSQL credentials**

   The load step reads database credentials from environment variables. Make sure these are exported in the same shell session that runs Airflow:
   ```bash
   export PSQL_USERNAME=your_postgres_username
   export PSQL_PASSWORD=your_postgres_password
   ```
   better through UI wich is admin>onnections>addconnection

6. **Create the target database** (if it doesn't already exist)
   ```bash
   createdb etl_db
   ```

## Running the Pipeline

   ```bash
   airflow scheduler
   airflow webserver -p 8081
   python3 simulation_pipe/watch_dog.py
   ```
4. Open the Airflow UI ( `http://localhost:8081`) and locate the ETL DAG.
5. Unpause and trigger the DAG to run `extract_task → transform_task → load_task` in sequence.
6. Verify the loaded data in the `etl_db` PostgreSQL database.

## Known Issues

- **`load.py` validation order bug**: if `PSQL_PASSWORD` is `None` properly provide real credentials in airflow if again then configure firewalls and manage postgres files to get access from wsl

## Roadmap

- [ ] Fix credential validation order in `scripts/load.py` to raise a proper `ValueError` on missing credentials
- [ ] Add a `requirements.txt` for reproducible installs
- [ ] Add automated tests for extract/transform/load functions
- [ ] Add logging and error handling around database connection failures

## License

No license specified yet. Add a `LICENSE` file if you intend to make this project reusable by others.
