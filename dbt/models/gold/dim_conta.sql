select
    row_number() over (order by conta_id) as conta_sk,
    conta_id,
    cliente_id,
    agencia_id,
    saldo
from {{ ref('stg_contas') }}
