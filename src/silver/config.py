
import os
from pathlib import Path

from dotenv import load_dotenv



PROJECT_DIR = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_DIR / ".env")


def resolve_data_path(
    environment_variable: str,
    default_path: Path,
) -> Path:
    """Resolve configured data paths relative to the project root."""
    configured_path = os.getenv(environment_variable)

    if not configured_path:
        return default_path.resolve()

    path = Path(configured_path)

    if not path.is_absolute():
        path = PROJECT_DIR / path

    return path.resolve()


BRONZE_DIR = resolve_data_path(
    "BRONZE_DIR",
    PROJECT_DIR / "data" / "bronze",
)

SILVER_DIR = resolve_data_path(
    "SILVER_DIR",
    PROJECT_DIR / "data" / "silver",
)

REJECTS_DIR = (
    PROJECT_DIR / "data" / "silver_rejects"
).resolve()


SOURCE_TIMEZONE = os.getenv(
    "TIMEZONE",
    "America/Sao_Paulo",
)


SOURCE_TABLES = (
    "agencias",
    "clientes",
    "tipos_transacao",
    "contas",
    "cartoes",
    "emprestimos",
    "transacoes",
)



PARQUET_PATTERN = "*.parquet"


REJECT_NULL_OR_DUPLICATED_PK = (
    "Null or duplicated primary key."
)

REJECT_REQUIRED_FIELD_NULL = (
    "Required field is null."
)


PRIMARY_KEYS = {
    "agencias": "agencia_id",
    "clientes": "cliente_id",
    "tipos_transacao": "tipo_transacao_id",
    "contas": "conta_id",
    "cartoes": "cartao_id",
    "emprestimos": "emprestimo_id",
    "transacoes": "transacao_id",
}


REQUIRED_COLUMNS = {
    "agencias": (
        "agencia_id",
        "nome_agencia",
        "cidade",
    ),
    "clientes": (
        "cliente_id",
        "nome",
        "cpf",
        "data_nascimento",
    ),
    "tipos_transacao": (
        "tipo_transacao_id",
        "descricao",
    ),
    "contas": (
        "conta_id",
        "cliente_id",
        "agencia_id",
        "saldo",
    ),
    "cartoes": (
        "cartao_id",
        "conta_id",
        "numero_cartao",
        "tipo_cartao",
    ),
    "emprestimos": (
        "emprestimo_id",
        "cliente_id",
        "valor_contratado",
        "parcelas",
        "data_contrato",
    ),
    "transacoes": (
        "transacao_id",
        "conta_origem_id",
        "conta_destino_id",
        "tipo_transacao_id",
        "valor",
        "data_hora",
    ),
}
