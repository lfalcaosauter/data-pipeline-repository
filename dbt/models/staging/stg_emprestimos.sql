select
    emprestimo_id,
    cliente_id,
    valor_contratado,
    parcelas,
    data_contrato,
    _source_system,
    _ingestion_timestamp,
    _batch_id
from {{ source('silver', 'emprestimos') }}
