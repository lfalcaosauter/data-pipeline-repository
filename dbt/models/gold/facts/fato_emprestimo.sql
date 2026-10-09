select
    row_number() over (order by e.emprestimo_id) as emprestimo_sk,
    e.emprestimo_id,
    dc.cliente_sk,
    dd.data_sk,
    e.valor_contratado,
    e.parcelas,
    round(
        e.valor_contratado / nullif(e.parcelas, 0),
        2
    ) as valor_medio_parcela,
    e.data_contrato

from {{ ref('stg_emprestimos') }} e

inner join {{ ref('dim_cliente') }} dc
    on e.cliente_id = dc.cliente_id

inner join {{ ref('dim_data') }} dd
    on e.data_contrato = dd.data