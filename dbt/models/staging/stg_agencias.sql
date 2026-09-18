select
    agencia_id,
    nome_agencia,
    cidade,
    _source_system,
    _ingestion_timestamp,
    _batch_id
from {{ source('silver', 'agencias') }}
