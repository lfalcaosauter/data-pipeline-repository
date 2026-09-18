select
    tipo_transacao_id,
    descricao,
    _source_system,
    _ingestion_timestamp,
    _batch_id
from {{ source('silver', 'tipos_transacao') }}
