import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


# Project
PROJECT_DIR = Path(__file__).resolve().parents[1]


# Application
APP_NAME = os.getenv("APP_NAME", "data-pipeline")
APP_ENV = os.getenv("APP_ENV", "development")
APP_DEBUG = os.getenv("APP_DEBUG", "true").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
TIMEZONE = os.getenv("TIMEZONE", "America/Sao_Paulo")


# PostgreSQL
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "banking_oltp")
POSTGRES_USER = os.getenv("POSTGRES_USER", "banking_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "change_me")
DB_CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", "10"))


# Data generation
FAKER_LOCALE = os.getenv("FAKER_LOCALE", "pt_BR")
FAKER_SEED = int(os.getenv("FAKER_SEED", "42"))

NUM_AGENCIAS = int(os.getenv("NUM_AGENCIAS", "10"))
NUM_CLIENTES = int(os.getenv("NUM_CLIENTES", "1000"))
NUM_CONTAS = int(os.getenv("NUM_CONTAS", "1200"))
NUM_CARTOES = int(os.getenv("NUM_CARTOES", "900"))
NUM_EMPRESTIMOS = int(os.getenv("NUM_EMPRESTIMOS", "400"))
NUM_TRANSACOES = int(os.getenv("NUM_TRANSACOES", "10000"))


# Pipeline directories
DATA_DIR = Path(
    os.getenv(
        "DATA_DIR",
        str(PROJECT_DIR / "data"),
    )
)

BRONZE_DIR = Path(
    os.getenv(
        "BRONZE_DIR",
        str(DATA_DIR / "bronze"),
    )
)

SILVER_DIR = Path(
    os.getenv(
        "SILVER_DIR",
        str(DATA_DIR / "silver"),
    )
)

GOLD_DIR = Path(
    os.getenv(
        "GOLD_DIR",
        str(DATA_DIR / "gold"),
    )
)

FILE_FORMAT = os.getenv("FILE_FORMAT", "parquet")


# Pipeline execution
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1000"))

ENABLE_DATA_VALIDATION = (
    os.getenv(
        "ENABLE_DATA_VALIDATION",
        "true",
    ).lower()
    == "true"
)

FAIL_ON_DATA_QUALITY_ERROR = (
    os.getenv(
        "FAIL_ON_DATA_QUALITY_ERROR",
        "true",
    ).lower()
    == "true"
)


# Database connection pool
DB_POOL_MIN_SIZE = int(
    os.getenv(
        "DB_POOL_MIN_SIZE",
        "1",
    )
)

DB_POOL_MAX_SIZE = int(
    os.getenv(
        "DB_POOL_MAX_SIZE",
        "10",
    )
)