import logging
import os

import pandas as pd

from silver.config import SOURCE_TABLES
from silver.io import (
    find_latest_complete_batch,
    read_bronze_table,
    write_silver_table,
    write_success_marker,
)
from silver.transformations import (
    process_agencias,
    process_cartoes,
    process_clientes,
    process_contas,
    process_emprestimos,
    process_tipos_transacao,
    process_transacoes,
)
from silver.validation import validate_required_columns

logger = logging.getLogger(__name__)


def run_silver_layer() -> None:
    """Read the latest complete Bronze batch and build Silver tables."""
    logger.info("Starting Silver layer.")

    batch_id, ingestion_date = find_latest_complete_batch()

    logger.info(
        "Selected Bronze batch | batch_id=%s | ingestion_date=%s",
        batch_id,
        ingestion_date,
    )

    raw_data: dict[str, pd.DataFrame] = {}

    # ---------------------------------------------------------
    # 1. Read and validate Bronze
    # ---------------------------------------------------------
    for table_name in SOURCE_TABLES:
        df = read_bronze_table(
            table_name,
            batch_id,
        )

        validate_required_columns(
            df,
            table_name,
        )

        raw_data[table_name] = df

    logger.info(
        "Bronze batch loaded successfully | "
        "batch_id=%s | tables=%d",
        batch_id,
        len(raw_data),
    )

    # ---------------------------------------------------------
    # 2. Transform tables
    # ---------------------------------------------------------
    agencias = process_agencias(
        raw_data["agencias"],
        batch_id,
        ingestion_date,
    )

    clientes = process_clientes(
        raw_data["clientes"],
        batch_id,
        ingestion_date,
    )

    tipos_transacao = process_tipos_transacao(
        raw_data["tipos_transacao"],
        batch_id,
        ingestion_date,
    )

    contas = process_contas(
        raw_data["contas"],
        set(clientes["cliente_id"]),
        set(agencias["agencia_id"]),
        batch_id,
        ingestion_date,
    )

    cartoes = process_cartoes(
        raw_data["cartoes"],
        set(contas["conta_id"]),
        batch_id,
        ingestion_date,
    )

    emprestimos = process_emprestimos(
        raw_data["emprestimos"],
        set(clientes["cliente_id"]),
        batch_id,
        ingestion_date,
    )

    transacoes = process_transacoes(
        raw_data["transacoes"],
        set(contas["conta_id"]),
        set(tipos_transacao["tipo_transacao_id"]),
        batch_id,
        ingestion_date,
    )

    silver_data = {
        "agencias": agencias,
        "clientes": clientes,
        "tipos_transacao": tipos_transacao,
        "contas": contas,
        "cartoes": cartoes,
        "emprestimos": emprestimos,
        "transacoes": transacoes,
    }

    # ---------------------------------------------------------
    # 3. Write Silver batch
    # ---------------------------------------------------------
    written_tables = 0

    try:
        for table_name, df in silver_data.items():
            write_silver_table(
                df,
                table_name,
                batch_id,
                ingestion_date,
            )

            written_tables += 1

        if written_tables != len(SOURCE_TABLES):
            raise RuntimeError(
                "Silver batch is incomplete: "
                f"{written_tables}/{len(SOURCE_TABLES)} tables written."
            )

        # The success marker is written only after every table
        # has been successfully persisted.
        write_success_marker(
            ingestion_date,
            batch_id,
        )

    except Exception:
        logger.exception(
            "Silver layer failed | "
            "batch_id=%s | tables_written=%d",
            batch_id,
            written_tables,
        )
        raise

    logger.info(
        "Silver layer completed successfully | "
        "batch_id=%s | tables=%d",
        batch_id,
        written_tables,
    )


def main() -> None:
    logging.basicConfig(
        level=os.getenv(
            "LOG_LEVEL",
            "INFO",
        ),
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
    )

    run_silver_layer()


if __name__ == "__main__":
    main()