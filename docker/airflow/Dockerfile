FROM apache/airflow:3.3.2

USER airflow

RUN pip install --no-cache-dir \
    "faker>=40.38.0" \
    pandas \
    psycopg2-binary \
    "psycopg[binary]>=3.3.5" \
    "pyarrow>=25.0.1" \
    python-dotenv \
    requests \
    "dbt-core==1.12.5" \
    "dbt-postgres==1.11.0"