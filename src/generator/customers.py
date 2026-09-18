from faker import Faker

from config import NUM_CLIENTES
from generator.helpers import generate_cpf


def get_existing_cpfs(cursor) -> set[str]:
    """Return all CPFs already stored in the database."""
    cursor.execute(
        """
        SELECT cpf
        FROM clientes
        """
    )

    return {
        row[0]
        for row in cursor.fetchall()
    }


def insert_clientes(
    cursor,
    fake: Faker,
    start_id: int,
) -> None:
    """Insert synthetic customers."""
    data = []
    used_cpfs: set[str] = set()
    existing_cpfs = get_existing_cpfs(cursor)

    for cliente_id in range(
        start_id,
        start_id + NUM_CLIENTES,
    ):
        cpf = generate_cpf(fake)

        while cpf in used_cpfs or cpf in existing_cpfs:
            cpf = generate_cpf(fake)

        used_cpfs.add(cpf)

        data.append(
            (
                cliente_id,
                fake.name(),
                cpf,
                fake.date_of_birth(
                    minimum_age=18,
                    maximum_age=80,
                ),
            )
        )

    cursor.executemany(
        """
        INSERT INTO clientes (
            cliente_id,
            nome,
            cpf,
            data_nascimento
        )
        VALUES (%s, %s, %s, %s)
        """,
        data,
    )
