select
    conta_id,
    cliente_id,
    agencia_id,
    saldo,
    _source_system,
    _ingestion_timestamp,
    _batch_id
from {{ source('silver', 'contas') }}
