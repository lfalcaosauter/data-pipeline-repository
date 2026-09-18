select
    cartao_id,
    conta_id,
    tipo_cartao,
    numero_cartao_mascarado,
    _source_system,
    _ingestion_timestamp,
    _batch_id
from {{ source('silver', 'cartoes') }}
