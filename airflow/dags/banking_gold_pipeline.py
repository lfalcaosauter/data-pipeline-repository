import os
import subprocess
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from airflow.sdk import DAG
from airflow.providers.standard.operators.python import PythonOperator


AIRFLOW_TIMEZONE = ZoneInfo("America/Sao_Paulo")


def run_dbt_command(command):
    """Execute dbt using credentials from the Airflow connection."""
    from airflow.hooks.base import BaseHook

    connection = BaseHook.get_connection("banking_postgres")

    env = os.environ.copy()
    env.update({
        "POSTGRES_HOST": connection.host,
        "POSTGRES_PORT": str(connection.port or 5432),
        "POSTGRES_DB": connection.schema or "banking_oltp",
        "POSTGRES_USER": connection.login,
        "POSTGRES_PASSWORD": connection.password or "",
    })

    subprocess.run(
        ["dbt", command, "--project-dir", "dbt", "--profiles-dir", "dbt"],
        cwd="/opt/airflow/project",
        env=env,
        check=True,
        timeout=3600,
    )


def build_gold():
    run_dbt_command("run")


def validate_gold():
    run_dbt_command("test")


def gold_pipeline_result():
    print("SUCCESS: dbt models built and tests passed.")


with DAG(
    dag_id="banking_gold_pipeline",
    description="Build and validate analytical models with dbt",
    start_date=datetime(2026, 1, 1, tzinfo=AIRFLOW_TIMEZONE),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["banking", "gold", "dbt"],
) as dag:

    build = PythonOperator(
        task_id="build_gold",
        python_callable=build_gold,
        retries=3,
        retry_delay=timedelta(minutes=5),
    )

    validate = PythonOperator(
        task_id="validate_gold",
        python_callable=validate_gold,
        retries=2,
        retry_delay=timedelta(minutes=3),
    )

    result = PythonOperator(
        task_id="gold_pipeline_result",
        python_callable=gold_pipeline_result,
    )

    build >> validate >> result
