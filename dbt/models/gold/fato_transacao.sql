select
    row_number() over (order by t.transacao_id) as transacao_sk,
    t.transacao_id,
    dc.cliente_sk,
    co.conta_sk as conta_origem_sk,
    cd.conta_sk as conta_destino_sk,
    dd.data_sk,
    dtt.tipo_transacao_sk,
    t.valor,
    t.data_hora
from {{ ref('stg_transacoes') }} t

inner join {{ ref('dim_conta') }} co
    on t.conta_origem_id = co.conta_id

inner join {{ ref('dim_conta') }} cd
    on t.conta_destino_id = cd.conta_id

inner join {{ ref('dim_cliente') }} dc
    on co.cliente_id = dc.cliente_id

inner join {{ ref('dim_data') }} dd
    on cast(t.data_hora as date) = dd.data

inner join {{ ref('dim_tipo_transacao') }} dtt
    on t.tipo_transacao_id = dtt.tipo_transacao_id
