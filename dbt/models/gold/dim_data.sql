with datas as (

    select distinct
        cast(data_hora as date) as data
    from {{ ref('stg_transacoes') }}

)

select
    row_number() over (order by data) as data_sk,
    data,
    extract(day from data)::integer as dia,
    extract(month from data)::integer as mes,
    to_char(data, 'TMMonth') as nome_mes,
    extract(quarter from data)::integer as trimestre,
    extract(year from data)::integer as ano,
    extract(isodow from data)::integer as dia_semana
from datas
