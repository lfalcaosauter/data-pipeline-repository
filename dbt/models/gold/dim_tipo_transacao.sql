select
    row_number() over (order by tipo_transacao_id) as tipo_transacao_sk,
    tipo_transacao_id,
    descricao
from {{ ref('stg_tipos_transacao') }}
