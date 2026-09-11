import logging
import os
from collections.abc import Iterator
from typing import Final

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import connection

load_dotenv()

logger = logging.getLogger(__name__)

SOURCE_TABLES: Final[tuple[str, ...]] = (
    "agencias",
    "clientes",
    "tipos_transacao",
    "contas",
    "cartoes",
    "emprestimos",
    "transacoes",
)

TABLE_QUERIES: Final[dict[str, str]] = {
    "agencias": """
        SELECT agencia_id, nome_agencia, cidade
        FROM agencias
    """,
    "clientes": """
        SELECT cliente_id, nome, cpf, data_nascimento
        FROM clientes
    """,
    "tipos_transacao": """
        SELECT tipo_transacao_id, descricao
        FROM tipos_transacao
    """,
    "contas": """
        SELECT conta_id, cliente_id, agencia_id, saldo
        FROM contas
    """,
    "cartoes": """
        SELECT cartao_id, conta_id, numero_cartao, tipo_cartao
        FROM cartoes
    """,
    "emprestimos": """
        SELECT emprestimo_id, cliente_id, valor_contratado, parcelas,
               data_contrato
        FROM emprestimos
    """,
    "transacoes": """
        SELECT transacao_id, conta_origem_id, conta_destino_id,
               tipo_transacao_id, valor, data_hora
        FROM transacoes
    """,
}

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_NAME = os.getenv("POSTGRES_DB", "banking_oltp")
DB_USER = os.getenv("POSTGRES_USER", "banking_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "change_me")
DB_CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", "10"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1000"))


def get_database_connection() -> connection:
    """Create a PostgreSQL connection using environment configuration."""
    logger.info(
        "Connecting to PostgreSQL | host=%s port=%s database=%s",
        DB_HOST,
        DB_PORT,
        DB_NAME,
    )

    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=DB_CONNECT_TIMEOUT,
        application_name="data-pipeline-extraction",
    )


def _fetch_rows(cursor: object, batch_size: int) -> Iterator[tuple]:
    """Yield source rows in bounded batches."""
    while True:
        rows = cursor.fetchmany(batch_size)  # type: ignore[attr-defined]
        if not rows:
            break

        yield from rows


def extract_table(
    table_name: str,
    db_connection: connection | None = None,
) -> pd.DataFrame:
    """Extract one complete source table without business transformations."""
    if table_name not in TABLE_QUERIES:
        raise ValueError(
            f"Unsupported source table: {table_name!r}. "
            f"Expected one of: {', '.join(SOURCE_TABLES)}."
        )

    if BATCH_SIZE <= 0:
        raise ValueError("BATCH_SIZE must be greater than zero.")

    owns_connection = db_connection is None
    connection_to_use = db_connection or get_database_connection()

    try:
        with connection_to_use.cursor() as cursor:
            cursor.execute(TABLE_QUERIES[table_name])

            if cursor.description is None:
                raise RuntimeError(
                    f"Source query returned no column metadata for table "
                    f"'{table_name}'."
                )

            columns = [column.name for column in cursor.description]
            rows = list(_fetch_rows(cursor, BATCH_SIZE))

        result = pd.DataFrame.from_records(
            rows,
            columns=columns,
        )

        logger.info(
            "Extracted source table '%s': %d row(s).",
            table_name,
            len(result),
        )

        return result

    except Exception:
        logger.exception(
            "Failed to extract source table '%s'.",
            table_name,
        )
        raise

    finally:
        if owns_connection:
            connection_to_use.close()


def extract_all() -> dict[str, pd.DataFrame]:
    """Extract all configured OLTP tables into Pandas DataFrames."""
    logger.info(
        "Starting OLTP extraction | tables=%d",
        len(SOURCE_TABLES),
    )

    db_connection = get_database_connection()

    try:
        extracted_data = {
            table_name: extract_table(
                table_name=table_name,
                db_connection=db_connection,
            )
            for table_name in SOURCE_TABLES
        }
    finally:
        db_connection.close()

    logger.info("OLTP extraction completed successfully.")

    return extracted_data


def main() -> None:
    """Run a local extraction smoke test and log row counts."""
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    extracted_data = extract_all()

    for table_name, dataframe in extracted_data.items():
        logger.info(
            "Source table '%s' ready for Bronze | rows=%d columns=%d",
            table_name,
            len(dataframe),
            len(dataframe.columns),
        )


if __name__ == "__main__":
    main()