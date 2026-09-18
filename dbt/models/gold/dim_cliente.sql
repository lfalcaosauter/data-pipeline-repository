select
    row_number() over (order by cliente_id) as cliente_sk,
    cliente_id,
    nome,
    cpf,
    data_nascimento
from {{ ref('stg_clientes') }}
