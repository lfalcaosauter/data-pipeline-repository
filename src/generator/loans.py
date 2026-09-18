from faker import Faker

from config import NUM_EMPRESTIMOS
from generator.helpers import generate_money


def insert_emprestimos(
    cursor,
    fake: Faker,
    start_id: int,
    cliente_min_id: int,
    cliente_max_id: int,
) -> None:
    """Insert synthetic loans."""
    data = []

    for emprestimo_id in range(
        start_id,
        start_id + NUM_EMPRESTIMOS,
    ):
        cliente_id = fake.random_int(
            min=cliente_min_id,
            max=cliente_max_id,
        )

        valor_contratado = generate_money(
            fake,
            minimum_cents=100_000,
            maximum_cents=10_000_000,
        )

        parcelas = fake.random_element(
            elements=(6, 12, 18, 24, 36, 48),
        )

        data_contrato = fake.date_between(
            start_date="-3y",
            end_date="today",
        )

        data.append(
            (
                emprestimo_id,
                cliente_id,
                valor_contratado,
                parcelas,
                data_contrato,
            )
        )

    cursor.executemany(
        """
        INSERT INTO emprestimos (
            emprestimo_id,
            cliente_id,
            valor_contratado,
            parcelas,
            data_contrato
        )
        VALUES (%s, %s, %s, %s, %s)
        """,
        data,
    )
