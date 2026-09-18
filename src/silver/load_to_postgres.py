import logging
from pathlib import Path
from typing import cast

import pandas as pd
from psycopg2.extras import execute_values

from config import SILVER_DIR
from silver.io import find_latest_complete_batch
from utils.database import get_database_connection

logger = logging.getLogger(__name__)


SILVER_TABLES = (
    "agencias",
    "clientes",
    "contas",
    "cartoes",
    "emprestimos",
    "tipos_transacao",
    "transacoes",
)


TABLE_COLUMNS = {
    "agencias": (
        "agencia_id",
        "nome_agencia",
        "cidade",
        "_source_system",
        "_ingestion_timestamp",
        "_batch_id",
    ),
    "clientes": (
        "cliente_id",
        "nome",
        "cpf",
        "data_nascimento",
        "_source_system",
        "_ingestion_timestamp",
        "_batch_id",
    ),
    "contas": (
        "conta_id",
        "cliente_id",
        "agencia_id",
        "saldo",
        "_source_system",
        "_ingestion_timestamp",
        "_batch_id",
    ),
    "cartoes": (
        "cartao_id",
        "conta_id",
        "tipo_cartao",
        "numero_cartao_mascarado",
        "_source_system",
        "_ingestion_timestamp",
        "_batch_id",
    ),
    "emprestimos": (
        "emprestimo_id",
        "cliente_id",
        "valor_contratado",
        "parcelas",
        "data_contrato",
        "_source_system",
        "_ingestion_timestamp",
        "_batch_id",
    ),
    "tipos_transacao": (
        "tipo_transacao_id",
        "descricao",
        "_source_system",
        "_ingestion_timestamp",
        "_batch_id",
    ),
    "transacoes": (
        "transacao_id",
        "conta_origem_id",
        "conta_destino_id",
        "tipo_transacao_id",
        "valor",
        "data_hora",
        "_source_system",
        "_ingestion_timestamp",
        "_batch_id",
    ),
}


TABLE_DDL = {
    "agencias": """
        CREATE TABLE IF NOT EXISTS silver.agencias (
            agencia_id INTEGER,
            nome_agencia TEXT,
            cidade TEXT,
            _source_system TEXT,
            _ingestion_timestamp TIMESTAMPTZ,
            _batch_id TEXT
        )
    """,
    "clientes": """
        CREATE TABLE IF NOT EXISTS silver.clientes (
            cliente_id INTEGER,
            nome TEXT,
            cpf TEXT,
            data_nascimento DATE,
            _source_system TEXT,
            _ingestion_timestamp TIMESTAMPTZ,
            _batch_id TEXT
        )
    """,
    "contas": """
        CREATE TABLE IF NOT EXISTS silver.contas (
            conta_id INTEGER,
            cliente_id INTEGER,
            agencia_id INTEGER,
            saldo NUMERIC(15, 2),
            _source_system TEXT,
            _ingestion_timestamp TIMESTAMPTZ,
            _batch_id TEXT
        )
    """,
    "cartoes": """
        CREATE TABLE IF NOT EXISTS silver.cartoes (
            cartao_id INTEGER,
            conta_id INTEGER,
            tipo_cartao TEXT,
            numero_cartao_mascarado TEXT,
            _source_system TEXT,
            _ingestion_timestamp TIMESTAMPTZ,
            _batch_id TEXT
        )
    """,
    "emprestimos": """
        CREATE TABLE IF NOT EXISTS silver.emprestimos (
            emprestimo_id INTEGER,
            cliente_id INTEGER,
            valor_contratado NUMERIC(15, 2),
            parcelas INTEGER,
            data_contrato DATE,
            _source_system TEXT,
            _ingestion_timestamp TIMESTAMPTZ,
            _batch_id TEXT
        )
    """,
    "tipos_transacao": """
        CREATE TABLE IF NOT EXISTS silver.tipos_transacao (
            tipo_transacao_id INTEGER,
            descricao TEXT,
            _source_system TEXT,
            _ingestion_timestamp TIMESTAMPTZ,
            _batch_id TEXT
        )
    """,
    "transacoes": """
        CREATE TABLE IF NOT EXISTS silver.transacoes (
            transacao_id INTEGER,
            conta_origem_id INTEGER,
            conta_destino_id INTEGER,
            tipo_transacao_id INTEGER,
            valor NUMERIC(15, 2),
            data_hora TIMESTAMPTZ,
            _source_system TEXT,
            _ingestion_timestamp TIMESTAMPTZ,
            _batch_id TEXT
        )
    """,
}


def get_silver_table_path(
    table_name: str,
    ingestion_date: str,
    batch_id: str,
) -> Path:
    """Return the Parquet path for a Silver table."""
    return (
        SILVER_DIR
        / table_name
        / f"ingestion_date={ingestion_date}"
        / f"batch_id={batch_id}"
        / f"{table_name}.parquet"
    )


def create_silver_schema(cursor) -> None:
    """Create the PostgreSQL Silver schema."""
    cursor.execute(
        "CREATE SCHEMA IF NOT EXISTS silver"
    )


def create_silver_tables(cursor) -> None:
    """Create PostgreSQL tables for the Silver layer."""
    for table_name in SILVER_TABLES:
        cursor.execute(TABLE_DDL[table_name])


def truncate_silver_tables(cursor) -> None:
    """Remove the current Silver snapshot from PostgreSQL."""
    table_names = ", ".join(
        f"silver.{table_name}"
        for table_name in SILVER_TABLES
    )

    cursor.execute(
        f"TRUNCATE TABLE {table_names}"
    )


def load_dataframe(
    cursor,
    table_name: str,
    dataframe: pd.DataFrame,
) -> None:
    """Load a Silver DataFrame into PostgreSQL."""
    columns = TABLE_COLUMNS[table_name]

    missing_columns = [
        column
        for column in columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns for {table_name}: "
            f"{missing_columns}"
        )

    selected_dataframe = dataframe.loc[
        :,
        list(columns),
    ].copy()

    values = [
        tuple(row)
        for row in selected_dataframe.itertuples(
            index=False,
            name=None,
        )
    ]

    if not values:
        logger.warning(
            "Silver table is empty | table=%s",
            table_name,
        )
        return

    column_sql = ", ".join(columns)

    insert_sql = f"""
        INSERT INTO silver.{table_name} (
            {column_sql}
        )
        VALUES %s
    """

    execute_values(
        cursor,
        insert_sql,
        values,
        page_size=1000,
    )

    logger.info(
        "Loaded Silver table | table=%s rows=%s",
        table_name,
        len(values),
    )


def run_silver_postgres_load() -> None:
    """Load the latest complete Silver batch into PostgreSQL."""
    batch_id, ingestion_date = find_latest_complete_batch()

    logger.info(
        "Loading Silver batch into PostgreSQL | "
        "batch_id=%s ingestion_date=%s",
        batch_id,
        ingestion_date,
    )

    connection = get_database_connection()

    try:
        with connection, connection.cursor() as cursor:
            create_silver_schema(cursor)
            create_silver_tables(cursor)
            truncate_silver_tables(cursor)

            for table_name in SILVER_TABLES:
                file_path = get_silver_table_path(
                    table_name,
                    ingestion_date,
                    batch_id,
                )

                if not file_path.exists():
                    raise FileNotFoundError(
                        f"Silver table not found: {file_path}"
                    )

                dataframe = cast(
                    pd.DataFrame,
                    pd.read_parquet(file_path),
                )

                load_dataframe(
                    cursor,
                    table_name,
                    dataframe,
                )

        logger.info(
            "Silver PostgreSQL load completed successfully."
        )

    finally:
        connection.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
    )

    run_silver_postgres_load()