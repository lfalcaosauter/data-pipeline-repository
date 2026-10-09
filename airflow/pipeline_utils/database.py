import psycopg2
from airflow.sdk import BaseHook


AIRFLOW_POSTGRES_CONN_ID = "banking_postgres"


def get_airflow_database_connection():
    """Create a PostgreSQL connection using an Airflow Connection."""
    airflow_conn = BaseHook.get_connection(
        AIRFLOW_POSTGRES_CONN_ID
    )

    return psycopg2.connect(
        host=airflow_conn.host,
        port=airflow_conn.port or 5432,
        dbname=airflow_conn.schema,
        user=airflow_conn.login,
        password=airflow_conn.password,
        connect_timeout=10,
        application_name="data-pipeline-airflow",
    )
