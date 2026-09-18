"""Build business-oriented analytical datasets from Silver."""

import logging
import os
from pathlib import Path

import pandas as pd

from silver.config import SOURCE_TABLES

logger = logging.getLogger(__name__)

PROJECT_DIR = Path(__file__).resolve().parents[2]

SILVER_DIR = Path(
    os.getenv(
        "SILVER_DIR",
        str(PROJECT_DIR / "data" / "silver"),
    )
)

GOLD_DIR = Path(
    os.getenv(
        "GOLD_DIR",
        str(PROJECT_DIR / "data" / "gold"),
    )
)


def get_silver_table_path(
    table_name: str,
    ingestion_date: str,
    batch_id: str,
) -> Path:
    """Return the path of a Silver table for a specific batch."""
    return (
        SILVER_DIR
        / table_name
        / f"ingestion_date={ingestion_date}"
        / f"batch_id={batch_id}"
        / f"{table_name}.parquet"
    )


def get_silver_success_marker(
    ingestion_date: str,
    batch_id: str,
) -> Path:
    """Return the success marker path for a Silver batch."""
    return (
        SILVER_DIR
        / "_metadata"
        / f"ingestion_date={ingestion_date}"
        / f"batch_id={batch_id}"
        / "_SUCCESS"
    )


def find_latest_complete_silver_batch() -> tuple[str, str]:
    """Find the latest Silver batch marked as complete."""
    metadata_dir = SILVER_DIR / "_metadata"

    if not metadata_dir.exists():
        raise FileNotFoundError(
            f"Silver metadata directory not found: {metadata_dir}"
        )

    success_markers = list(
        metadata_dir.glob(
            "ingestion_date=*/batch_id=*/_SUCCESS"
        )
    )

    if not success_markers:
        raise FileNotFoundError(
            "No complete Silver batch found."
        )

    latest_marker = max(
        success_markers,
        key=lambda path: path.stat().st_mtime,
    )

    ingestion_date = (
        latest_marker.parent.parent.name.split(
            "=",
            1,
        )[1]
    )

    batch_id = (
        latest_marker.parent.name.split(
            "=",
            1,
        )[1]
    )

    logger.info(
        "Latest complete Silver batch selected | "
        "batch_id=%s | ingestion_date=%s",
        batch_id,
        ingestion_date,
    )

    return batch_id, ingestion_date


def read_silver_table(
    table_name: str,
    batch_id: str,
    ingestion_date: str,
) -> pd.DataFrame:
    """Read one table from a complete Silver batch."""
    if table_name not in SOURCE_TABLES:
        raise ValueError(
            f"Unsupported Silver table: {table_name!r}. "
            f"Expected one of: {', '.join(SOURCE_TABLES)}."
        )

    file_path = get_silver_table_path(
        table_name=table_name,
        ingestion_date=ingestion_date,
        batch_id=batch_id,
    )

    if not file_path.exists():
        raise FileNotFoundError(
            f"Silver table not found: {file_path}"
        )

    dataframe = pd.read_parquet(file_path)

    logger.info(
        "Silver table loaded | table=%s | rows=%d",
        table_name,
        len(dataframe),
    )

    return dataframe


def validate_silver_batch(
    data: dict[str, pd.DataFrame],
    ingestion_date: str,
    batch_id: str,
) -> None:
    """Validate the Silver batch before analytical processing."""
    success_marker = get_silver_success_marker(
        ingestion_date=ingestion_date,
        batch_id=batch_id,
    )

    if not success_marker.exists():
        raise FileNotFoundError(
            f"Silver success marker not found: {success_marker}"
        )

    required_tables = set(SOURCE_TABLES)

    missing_tables = sorted(
        required_tables - set(data)
    )

    if missing_tables:
        raise ValueError(
            "Silver batch is missing required table(s): "
            f"{', '.join(missing_tables)}"
        )

    empty_tables = [
        table_name
        for table_name in SOURCE_TABLES
        if data[table_name].empty
    ]

    if empty_tables:
        logger.warning(
            "Silver contains empty table(s): %s",
            ", ".join(empty_tables),
        )


def validate_columns(
    dataframe: pd.DataFrame,
    table_name: str,
    required_columns: set[str],
) -> None:
    """Validate required columns before analytical processing."""
    missing_columns = sorted(
        required_columns - set(dataframe.columns)
    )

    if missing_columns:
        raise ValueError(
            f"Silver table '{table_name}' is missing "
            f"required column(s): {', '.join(missing_columns)}"
        )


def build_daily_transaction_volume(
    transacoes: pd.DataFrame,
) -> pd.DataFrame:
    """Build daily transaction counts and financial volume."""
    validate_columns(
        transacoes,
        "transacoes",
        {
            "transacao_id",
            "valor",
            "data_hora",
        },
    )

    dataframe = transacoes.copy()

    dataframe["data"] = pd.to_datetime(
        dataframe["data_hora"],
        utc=True,
        errors="raise",
    ).dt.date

    result = (
        dataframe.groupby(
            "data",
            as_index=False,
        )
        .agg(
            quantidade_transacoes=(
                "transacao_id",
                "count",
            ),
            volume_financeiro=(
                "valor",
                "sum",
            ),
        )
        .sort_values("data")
    )

    return result


def build_daily_pix_transaction_volume(
    transacoes: pd.DataFrame,
    tipos_transacao: pd.DataFrame,
) -> pd.DataFrame:
    """Build daily PIX transaction volume."""
    validate_columns(
        transacoes,
        "transacoes",
        {
            "transacao_id",
            "tipo_transacao_id",
            "valor",
            "data_hora",
        },
    )

    validate_columns(
        tipos_transacao,
        "tipos_transacao",
        {
            "tipo_transacao_id",
            "descricao",
        },
    )

    dataframe = transacoes.merge(
        tipos_transacao[
            [
                "tipo_transacao_id",
                "descricao",
            ]
        ],
        on="tipo_transacao_id",
        how="inner",
        validate="many_to_one",
    )

    dataframe = dataframe[
        dataframe["descricao"]
        .astype(str)
        .str.upper()
        .eq("PIX")
    ].copy()

    dataframe["data"] = pd.to_datetime(
        dataframe["data_hora"],
        utc=True,
        errors="raise",
    ).dt.date

    result = (
        dataframe.groupby(
            "data",
            as_index=False,
        )
        .agg(
            quantidade_transacoes_pix=(
                "transacao_id",
                "count",
            ),
            volume_financeiro_pix=(
                "valor",
                "sum",
            ),
        )
        .sort_values("data")
    )

    return result


def build_financial_volume_by_agency(
    transacoes: pd.DataFrame,
    contas: pd.DataFrame,
) -> pd.DataFrame:
    """Build transaction financial volume grouped by agency."""
    validate_columns(
        transacoes,
        "transacoes",
        {
            "transacao_id",
            "conta_origem_id",
            "valor",
        },
    )

    validate_columns(
        contas,
        "contas",
        {
            "conta_id",
            "agencia_id",
        },
    )

    dataframe = transacoes.merge(
        contas[
            [
                "conta_id",
                "agencia_id",
            ]
        ],
        left_on="conta_origem_id",
        right_on="conta_id",
        how="inner",
        validate="many_to_one",
    )

    result = (
        dataframe.groupby(
            "agencia_id",
            as_index=False,
        )
        .agg(
            quantidade_transacoes=(
                "transacao_id",
                "count",
            ),
            volume_financeiro=(
                "valor",
                "sum",
            ),
        )
        .sort_values(
            "volume_financeiro",
            ascending=False,
        )
    )

    return result


def build_transactions_per_customer(
    transacoes: pd.DataFrame,
    contas: pd.DataFrame,
) -> pd.DataFrame:
    """Build transaction counts grouped by customer."""
    validate_columns(
        transacoes,
        "transacoes",
        {
            "transacao_id",
            "conta_origem_id",
        },
    )

    validate_columns(
        contas,
        "contas",
        {
            "conta_id",
            "cliente_id",
        },
    )

    dataframe = transacoes.merge(
        contas[
            [
                "conta_id",
                "cliente_id",
            ]
        ],
        left_on="conta_origem_id",
        right_on="conta_id",
        how="inner",
        validate="many_to_one",
    )

    result = (
        dataframe.groupby(
            "cliente_id",
            as_index=False,
        )
        .agg(
            quantidade_transacoes=(
                "transacao_id",
                "count",
            ),
        )
        .sort_values(
            "quantidade_transacoes",
            ascending=False,
        )
    )

    return result


def build_average_balance_by_agency(
    contas: pd.DataFrame,
) -> pd.DataFrame:
    """Build average account balance grouped by agency."""
    validate_columns(
        contas,
        "contas",
        {
            "conta_id",
            "agencia_id",
            "saldo",
        },
    )

    result = (
        contas.groupby(
            "agencia_id",
            as_index=False,
        )
        .agg(
            quantidade_contas=(
                "conta_id",
                "count",
            ),
            saldo_medio=(
                "saldo",
                "mean",
            ),
        )
        .sort_values(
            "saldo_medio",
            ascending=False,
        )
    )

    return result


def build_customers_with_loans(
    clientes: pd.DataFrame,
    emprestimos: pd.DataFrame,
) -> pd.DataFrame:
    """Build the analytical dataset of customers with loans."""
    validate_columns(
        clientes,
        "clientes",
        {
            "cliente_id",
            "nome",
        },
    )

    validate_columns(
        emprestimos,
        "emprestimos",
        {
            "emprestimo_id",
            "cliente_id",
            "valor_contratado",
            "parcelas",
        },
    )

    loan_summary = (
        emprestimos.groupby(
            "cliente_id",
            as_index=False,
        )
        .agg(
            quantidade_emprestimos=(
                "emprestimo_id",
                "count",
            ),
            valor_total_emprestimos=(
                "valor_contratado",
                "sum",
            ),
            parcelas_media=(
                "parcelas",
                "mean",
            ),
        )
    )

    result = clientes[
        [
            "cliente_id",
            "nome",
        ]
    ].merge(
        loan_summary,
        on="cliente_id",
        how="inner",
        validate="one_to_one",
    )

    return result.sort_values(
        "valor_total_emprestimos",
        ascending=False,
    )


def build_loan_volume(
    emprestimos: pd.DataFrame,
) -> pd.DataFrame:
    """Build overall loan volume indicators."""
    validate_columns(
        emprestimos,
        "emprestimos",
        {
            "emprestimo_id",
            "valor_contratado",
            "parcelas",
        },
    )

    result = pd.DataFrame(
        [
            {
                "quantidade_emprestimos": len(
                    emprestimos
                ),
                "volume_total_emprestimos": (
                    emprestimos[
                        "valor_contratado"
                    ].sum()
                ),
                "valor_medio_emprestimo": (
                    emprestimos[
                        "valor_contratado"
                    ].mean()
                ),
                "parcelas_media": (
                    emprestimos[
                        "parcelas"
                    ].mean()
                ),
            }
        ]
    )

    return result


def write_gold_dataset(
    dataframe: pd.DataFrame,
    dataset_name: str,
    batch_id: str,
    ingestion_date: str,
) -> Path:
    """Write one Gold analytical dataset."""
    output_dir = (
        GOLD_DIR
        / dataset_name
        / f"ingestion_date={ingestion_date}"
        / f"batch_id={batch_id}"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path = (
        output_dir
        / f"{dataset_name}.parquet"
    )

    dataframe.to_parquet(
        file_path,
        index=False,
        engine="pyarrow",
    )

    logger.info(
        "Gold dataset written | dataset=%s | rows=%d | path=%s",
        dataset_name,
        len(dataframe),
        file_path,
    )

    return file_path


def run_gold_layer() -> None:
    """Build all business-oriented Gold datasets."""
    logger.info("Starting Gold layer.")

    batch_id, ingestion_date = (
        find_latest_complete_silver_batch()
    )

    logger.info(
        "Selected Silver batch | "
        "batch_id=%s | ingestion_date=%s",
        batch_id,
        ingestion_date,
    )

    try:
        silver_data = {
            table_name: read_silver_table(
                table_name=table_name,
                batch_id=batch_id,
                ingestion_date=ingestion_date,
            )
            for table_name in SOURCE_TABLES
        }

        validate_silver_batch(
            data=silver_data,
            ingestion_date=ingestion_date,
            batch_id=batch_id,
        )

        transacoes = silver_data["transacoes"]
        contas = silver_data["contas"]
        clientes = silver_data["clientes"]
        emprestimos = silver_data["emprestimos"]
        tipos_transacao = silver_data[
            "tipos_transacao"
        ]

        gold_data = {
            "daily_transaction_volume": (
                build_daily_transaction_volume(
                    transacoes
                )
            ),
            "daily_pix_transaction_volume": (
                build_daily_pix_transaction_volume(
                    transacoes,
                    tipos_transacao,
                )
            ),
            "financial_volume_by_agency": (
                build_financial_volume_by_agency(
                    transacoes,
                    contas,
                )
            ),
            "transactions_per_customer": (
                build_transactions_per_customer(
                    transacoes,
                    contas,
                )
            ),
            "average_balance_by_agency": (
                build_average_balance_by_agency(
                    contas
                )
            ),
            "customers_with_loans": (
                build_customers_with_loans(
                    clientes,
                    emprestimos,
                )
            ),
            "loan_volume": (
                build_loan_volume(
                    emprestimos
                )
            ),
        }

        written_datasets = 0

        for dataset_name, dataframe in gold_data.items():
            write_gold_dataset(
                dataframe=dataframe,
                dataset_name=dataset_name,
                batch_id=batch_id,
                ingestion_date=ingestion_date,
            )
            written_datasets += 1

        logger.info(
            "Gold layer completed successfully | "
            "batch_id=%s | datasets=%d",
            batch_id,
            written_datasets,
        )

    except Exception:
        logger.exception(
            "Gold layer failed | "
            "batch_id=%s | ingestion_date=%s",
            batch_id,
            ingestion_date,
        )
        raise


def main() -> None:
    """Run the Gold layer."""
    run_gold_layer()


if __name__ == "__main__":
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

    main()