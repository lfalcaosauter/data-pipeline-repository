
import os
import subprocess
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from airflow.providers.standard.operators.python import PythonOperator
from airflow.sdk import DAG

sys.path.insert(0, "/opt/airflow/project/airflow")
sys.path.insert(0, "/opt/airflow/project/src")

from generator.generate_data import main as run_generator
from bronze.bronze import run_bronze_layer
from silver.silver import run_silver_layer
from silver.load_to_postgres import run_silver_postgres_load

from pipeline_utils.database import get_airflow_database_connection


AIRFLOW_TIMEZONE = ZoneInfo("America/Sao_Paulo")

DATABASE_RETRY_ARGS = {
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}


def generate_data_task() -> None:
    """Generate synthetic banking data using the Airflow connection."""
    connection = get_airflow_database_connection()

    try:
        run_generator(connection)
    finally:
        connection.close()


def bronze_task() -> None:
    """Extract OLTP data and persist the Bronze layer."""
    connection = get_airflow_database_connection()

    try:
        run_bronze_layer(connection)
    finally:
        connection.close()


def silver_task() -> None:
    """Transform the latest complete Bronze batch into Silver."""
    run_silver_layer()


def load_silver_postgres_task() -> None:
    """Load Silver data using the Airflow PostgreSQL connection."""
    connection = get_airflow_database_connection()

    try:
        run_silver_postgres_load(db_connection=connection)
    finally:
        connection.close()


def run_dbt_command(command: str) -> None:
    """Run a dbt command using credentials from the Airflow connection."""
    connection = get_airflow_database_connection()

    try:
        env = os.environ.copy()

        env.update(
            {
                "POSTGRES_HOST": connection.info.host,
                "POSTGRES_PORT": str(connection.info.port or 5432),
                "POSTGRES_DB": connection.info.dbname,
                "POSTGRES_USER": connection.info.user,
                "POSTGRES_PASSWORD": connection.info.password,
            }
        )

        subprocess.run(
            [
                "dbt",
                command,
                "--project-dir",
                "dbt",
                "--profiles-dir",
                "dbt",
            ],
            cwd="/opt/airflow/project",
            env=env,
            check=True,
        )
    finally:
        connection.close()


def dbt_run_task() -> None:
    """Build dbt models using the Airflow PostgreSQL connection."""
    run_dbt_command("run")


def dbt_test_task() -> None:
    """Run dbt data quality tests."""
    run_dbt_command("test")


with DAG(
    dag_id="banking_pipeline",
    description="Executes the complete banking data pipeline",
    start_date=datetime(
        2026,
        1,
        1,
        tzinfo=AIRFLOW_TIMEZONE,
    ),
    schedule="0 6 * * *",
    catchup=False,
    max_active_runs=1,
    tags=["banking", "pipeline", "dbt"],
) as dag:

    generate_data = PythonOperator(
        task_id="generate_data",
        python_callable=generate_data_task,
        retries=DATABASE_RETRY_ARGS["retries"],
        retry_delay=DATABASE_RETRY_ARGS["retry_delay"],
    )

    run_bronze = PythonOperator(
        task_id="run_bronze",
        python_callable=bronze_task,
        retries=DATABASE_RETRY_ARGS["retries"],
        retry_delay=DATABASE_RETRY_ARGS["retry_delay"],
    )

    run_silver = PythonOperator(
        task_id="run_silver",
        python_callable=silver_task,
        retries=1,
        retry_delay=timedelta(minutes=2),
    )

    load_silver_postgres = PythonOperator(
        task_id="load_silver_postgres",
        python_callable=load_silver_postgres_task,
        retries=DATABASE_RETRY_ARGS["retries"],
        retry_delay=DATABASE_RETRY_ARGS["retry_delay"],
    )

    run_dbt = PythonOperator(
        task_id="run_dbt",
        python_callable=dbt_run_task,
        retries=DATABASE_RETRY_ARGS["retries"],
        retry_delay=DATABASE_RETRY_ARGS["retry_delay"],
    )

    run_dbt_test = PythonOperator(
        task_id="run_dbt_test",
        python_callable=dbt_test_task,
        retries=DATABASE_RETRY_ARGS["retries"],
        retry_delay=DATABASE_RETRY_ARGS["retry_delay"],
    )

    (
        generate_data
        >> run_bronze
        >> run_silver
        >> load_silver_postgres
        >> run_dbt
        >> run_dbt_test
    )