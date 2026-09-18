from datetime import UTC, datetime
from decimal import Decimal

from faker import Faker


def generate_cpf(fake: Faker) -> str:
    """Generate an 11-digit synthetic CPF."""
    return fake.numerify(text="###########")


def generate_card_number(fake: Faker) -> str:
    """Generate a 16-digit synthetic card number."""
    return fake.numerify(text="################")


def generate_transaction_datetime(
    fake: Faker,
    start_year: int = 2024,
) -> datetime:
    """Generate a random transaction timestamp."""
    start = datetime(start_year, 1, 1, tzinfo=UTC)
    end = datetime.now(UTC)

    return fake.date_time_between(
        start_date=start,
        end_date=end,
    )


def generate_money(
    fake: Faker,
    minimum_cents: int,
    maximum_cents: int,
) -> Decimal:
    """Generate a monetary value with two decimal places."""
    cents = fake.random_int(
        min=minimum_cents,
        max=maximum_cents,
    )

    return Decimal(cents) / Decimal(100)


def get_next_id(
    cursor,
    table_name: str,
    id_column: str,
) -> int:
    """Return the next available ID for a table."""
    cursor.execute(
        f"""
        SELECT COALESCE(MAX({id_column}), 0) + 1
        FROM {table_name}
        """
    )

    return cursor.fetchone()[0]