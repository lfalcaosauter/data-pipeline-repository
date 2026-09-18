from faker import Faker

from config import NUM_CONTAS
from generator.helpers import generate_money


def insert_contas(
    cursor,
    fake: Faker,
    start_id: int,
    cliente_min_id: int,
    cliente_max_id: int,
    agencia_min_id: int,
    agencia_max_id: int,
) -> None:
    """Insert synthetic bank accounts."""
    data = []

    for conta_id in range(
        start_id,
        start_id + NUM_CONTAS,
    ):
        cliente_id = fake.random_int(
            min=cliente_min_id,
            max=cliente_max_id,
        )

        agencia_id = fake.random_int(
            min=agencia_min_id,
            max=agencia_max_id,
        )

        saldo = generate_money(
            fake,
            minimum_cents=0,
            maximum_cents=5_000_000,
        )

        data.append(
            (
                conta_id,
                cliente_id,
                agencia_id,
                saldo,
            )
        )

    cursor.executemany(
        """
        INSERT INTO contas (
            conta_id,
            cliente_id,
            agencia_id,
            saldo
        )
        VALUES (%s, %s, %s, %s)
        """,
        data,
    )
