import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.standard.operators.trigger_dagrun import (
    TriggerDagRunOperator,
)
from airflow.sdk import DAG


sys.path.insert(0, "/opt/airflow/project/airflow")
sys.path.insert(0, "/opt/airflow/project/src")


AIRFLOW_TIMEZONE = ZoneInfo("America/Sao_Paulo")

DATABASE_RETRY_ARGS = {
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}


def get_airflow_database_connection():
    """Load the Airflow database connection when a task executes."""
    from pipeline_utils.database import (
        get_airflow_database_connection as get_connection,
    )

    return get_connection()


def generate_data_task() -> None:
    """Generate synthetic banking data."""
    from generator.generate_data import main as run_generator

    connection = get_airflow_database_connection()

    try:
        run_generator(connection)
    finally:
        connection.close()


def bronze_task() -> None:
    """Extract and process data into the Bronze layer."""
    from bronze.bronze import run_bronze_layer

    connection = get_airflow_database_connection()

    try:
        run_bronze_layer(connection)
    finally:
        connection.close()


def silver_task() -> None:
    """Transform data in the Silver layer."""
    from silver.silver import run_silver_layer

    run_silver_layer()


def load_silver_postgres_task() -> None:
    """Load the Silver data into PostgreSQL."""
    from silver.load_to_postgres import run_silver_postgres_load

    connection = get_airflow_database_connection()

    try:
        run_silver_postgres_load(db_connection=connection)
    finally:
        connection.close()


with DAG(
    dag_id="banking_pipeline",
    description=(
        "Generates banking data, processes Bronze and Silver, "
        "and triggers the Gold pipeline."
    ),
    start_date=datetime(
        2026, 1, 1, tzinfo=AIRFLOW_TIMEZONE
    ),
    schedule="0 6 * * *",
    catchup=False,
    max_active_runs=1,
    tags=["banking", "pipeline", "bronze", "silver", "gold"],
) as dag:

    generate_data = PythonOperator(
        task_id="generate_data",
        python_callable=generate_data_task,
        **DATABASE_RETRY_ARGS,
    )

    run_bronze = PythonOperator(
        task_id="run_bronze",
        python_callable=bronze_task,
        **DATABASE_RETRY_ARGS,
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
        **DATABASE_RETRY_ARGS,
    )

    trigger_gold = TriggerDagRunOperator(
        task_id="trigger_banking_gold_pipeline",
        trigger_dag_id="banking_gold_pipeline",
        wait_for_completion=True,
        poke_interval=30,
        allowed_states=["success"],
        failed_states=["failed"],
    )

    (
        generate_data
        >> run_bronze
        >> run_silver
        >> load_silver_postgres
        >> trigger_gold
    )
