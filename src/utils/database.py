import logging

import psycopg2
from psycopg2.extensions import connection

from config import (
    DB_CONNECT_TIMEOUT,
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
)

logger = logging.getLogger(__name__)


def get_database_connection() -> connection:
    """Create and return a PostgreSQL database connection."""
    logger.info(
        "Connecting to PostgreSQL | host=%s port=%s database=%s",
        POSTGRES_HOST,
        POSTGRES_PORT,
        POSTGRES_DB,
    )

    return psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        connect_timeout=DB_CONNECT_TIMEOUT,
        application_name="data-pipeline",
    )