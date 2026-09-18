import logging
from collections.abc import Iterator
from typing import Final

import pandas as pd
from psycopg2.extensions import connection, cursor

from config import BATCH_SIZE, LOG_LEVEL
from utils.database import get_database_connection

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
        SELECT
            agencia_id,
            nome_agencia,
            cidade
        FROM agencias
    """,
    "clientes": """
        SELECT
            cliente_id,
            nome,
            cpf,
            data_nascimento
        FROM clientes
    """,
    "tipos_transacao": """
        SELECT
            tipo_transacao_id,
            descricao
        FROM tipos_transacao
    """,
    "contas": """
        SELECT
            conta_id,
            cliente_id,
            agencia_id,
            saldo
        FROM contas
    """,
    "cartoes": """
        SELECT
            cartao_id,
            conta_id,
            numero_cartao,
            tipo_cartao
        FROM cartoes
    """,
    "emprestimos": """
        SELECT
            emprestimo_id,
            cliente_id,
            valor_contratado,
            parcelas,
            data_contrato
        FROM emprestimos
    """,
    "transacoes": """
        SELECT
            transacao_id,
            conta_origem_id,
            conta_destino_id,
            tipo_transacao_id,
            valor,
            data_hora
        FROM transacoes
    """,
}

def _fetch_rows(
    db_cursor: cursor,
    batch_size: int,
) -> Iterator[tuple]:
    """Fetch database rows in batches."""
    while True:
        rows = db_cursor.fetchmany(batch_size)

        if not rows:
            break

        yield from rows


def extract_table(
    table_name: str,
    db_connection: connection | None = None,
) -> pd.DataFrame:
    """Extract one complete source table into a DataFrame."""
    if table_name not in TABLE_QUERIES:
        raise ValueError(
            f"Unsupported source table: {table_name!r}. "
            f"Expected one of: {', '.join(SOURCE_TABLES)}."
        )

    if BATCH_SIZE <= 0:
        raise ValueError(
            "BATCH_SIZE must be greater than zero."
        )

    owns_connection = db_connection is None

    connection_to_use = (
        db_connection
        if db_connection is not None
        else get_database_connection()
    )

    try:
        with connection_to_use.cursor() as db_cursor:
            db_cursor.execute(TABLE_QUERIES[table_name])

            if db_cursor.description is None:
                raise RuntimeError(
                    f"Source query returned no column metadata "
                    f"for table '{table_name}'."
                )

            columns = [
                column.name
                for column in db_cursor.description
            ]

            rows = list(
                _fetch_rows(
                    db_cursor,
                    BATCH_SIZE,
                )
            )

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
    """Extract all configured source tables."""
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

        return extracted_data

    finally:
        db_connection.close()


def main() -> None:
    """Run extraction and log the extracted row counts."""
    logging.basicConfig(
        level=LOG_LEVEL,
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
    )

    extracted_data = extract_all()

    for table_name, dataframe in extracted_data.items():
        logger.info(
            "Source table '%s' ready for Bronze | rows=%d",
            table_name,
            len(dataframe),
        )

if __name__ == "__main__":
    main()