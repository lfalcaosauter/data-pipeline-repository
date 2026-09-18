select
    transacao_id,
    conta_origem_id,
    conta_destino_id,
    tipo_transacao_id,
    valor,
    data_hora,
    _source_system,
    _ingestion_timestamp,
    _batch_id
from {{ source('silver', 'transacoes') }}
