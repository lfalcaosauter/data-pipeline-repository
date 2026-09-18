select
    cliente_id,
    nome,
    cpf,
    data_nascimento,
    _source_system,
    _ingestion_timestamp,
    _batch_id
from {{ source('silver', 'clientes') }}
